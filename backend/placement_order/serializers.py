from rest_framework import serializers
from datetime import timedelta

from nomenclatures.models import Nomenclature
from .models import PlacementOrder, PlacementOrderItem
from .dates import current_business_date
from .marketing import validate_attribution_payload


class AttributionField(serializers.JSONField):
    """JSON field constrained to the documented attribution allow-list."""

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        try:
            return validate_attribution_payload(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc)) from exc


class PlacementOrderItemSerializer(serializers.ModelSerializer):
    nomenclature_name = serializers.CharField(
        source="nomenclature.name", read_only=True
    )
    responsible_name = serializers.CharField(
        source="responsible.get_full_name", read_only=True
    )

    class Meta:
        model = PlacementOrderItem
        fields = ["id", "nomenclature", "nomenclature_name", "responsible", "responsible_name"]

    def validate_nomenclature_ids(self, nomenclatures):
        without_responsible = [
            nom.name for nom in nomenclatures
            if nom.responsible_ad is None
        ]
        if without_responsible:
            raise serializers.ValidationError(
                f"У следующих мест не назначен ответственный: {', '.join(without_responsible)}"
            )
        return nomenclatures


class PlacementOrderSerializer(serializers.ModelSerializer):
    nomenclature_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        write_only=True,
        queryset=Nomenclature.objects.all(),
        source="nomenclatures"
    )
    items = PlacementOrderItemSerializer(many=True, read_only=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    attribution = AttributionField(required=False, allow_null=True)
    duration = serializers.IntegerField(required=False, default=30, min_value=1)
    all_days = serializers.BooleanField(required=False, default=True)
    commercial_status_display = serializers.CharField(
        source="get_commercial_status_display", read_only=True
    )
    cabinet_url = serializers.SerializerMethodField()

    class Meta:
        model = PlacementOrder
        fields = [
            "id", "owner", "name", "plan_number", "revision", "cabinet_url", "duration",
            "start_date", "end_date",
            "all_days", "days_of_week",
            "nomenclature_ids",
            "items",
            "commercial_status", "commercial_status_display", "lost_reason", "manager_comment",
            "attribution", "created", "updated",
            "qualified_at", "proposal_sent_at", "booked_at", "lost_at",
        ]
        read_only_fields = [
            "owner", "plan_number", "revision", "commercial_status", "commercial_status_display",
            "lost_reason", "manager_comment", "created", "updated", "qualified_at",
            "proposal_sent_at", "booked_at", "lost_at",
        ]

    def get_cabinet_url(self, obj):
        return f"/media-plans/{obj.id}"

    def validate(self, attrs):
        instance = self.instance
        all_days = attrs.get("all_days", instance.all_days if instance else True)
        days_of_week = attrs.get("days_of_week", instance.days_of_week if instance else [])
        start_date = attrs.get("start_date", instance.start_date if instance else None)
        end_date = attrs.get("end_date", instance.end_date if instance else None)

        errors = {}

        # дни недели
        if not all_days and not days_of_week:
            errors["days_of_week"] = "Укажите дни недели, если all_days = false."
        if all_days and days_of_week:
            errors["days_of_week"] = "Нельзя указывать дни недели при all_days = true."

        # start_date минимум +2 дня от сегодня
        today = current_business_date()
        min_start = today + timedelta(days=2)

        if start_date and start_date < min_start:
            errors["start_date"] = "Дата начала должна быть минимум через 2 дня от текущей даты."

        # end_date минимум на 1 день позже start_date
        if start_date and end_date and end_date <= start_date:
            errors["end_date"] = "Дата окончания должна быть минимум на 1 день позже даты начала."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class CommercialStatusSerializer(serializers.ModelSerializer):
    """Staff-only serializer for the commercial funnel transition."""

    class Meta:
        model = PlacementOrder
        fields = [
            "commercial_status", "lost_reason", "manager_comment", "qualified_at",
            "proposal_sent_at", "booked_at", "lost_at",
        ]
        read_only_fields = ["qualified_at", "proposal_sent_at", "booked_at", "lost_at"]

    def validate(self, attrs):
        status = attrs.get("commercial_status", self.instance.commercial_status)
        reason = attrs.get("lost_reason", self.instance.lost_reason)
        if status == "lost" and not reason:
            raise serializers.ValidationError({"lost_reason": "This field is required for lost orders."})
        if status != "lost" and "lost_reason" in attrs and reason:
            raise serializers.ValidationError({"lost_reason": "Only allowed when commercial_status is lost."})
        return attrs

    def update(self, instance, validated_data):
        if validated_data.get("commercial_status", instance.commercial_status) != "lost":
            validated_data["lost_reason"] = None
        return super().update(instance, validated_data)
