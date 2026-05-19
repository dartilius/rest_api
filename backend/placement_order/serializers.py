from rest_framework import serializers
from datetime import timedelta
from django.utils import timezone

from nomenclatures.models import Nomenclature
from .models import PlacementOrder, PlacementOrderItem


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

    class Meta:
        model = PlacementOrder
        fields = [
            "id", "owner", "duration",
            "start_date", "end_date",
            "all_days", "days_of_week",
            "nomenclature_ids",
            "items",
        ]
        read_only_fields = ["owner"]

    def validate(self, attrs):
        all_days = attrs.get("all_days", True)
        days_of_week = attrs.get("days_of_week", [])
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        errors = {}

        # дни недели
        if not all_days and not days_of_week:
            errors["days_of_week"] = "Укажите дни недели, если all_days = false."
        if all_days and days_of_week:
            errors["days_of_week"] = "Нельзя указывать дни недели при all_days = true."

        # start_date минимум +2 дня от сегодня
        now = timezone.now()
        min_start = now + timedelta(days=2)

        if start_date and start_date < min_start:
            errors["start_date"] = "Дата начала должна быть минимум через 2 дня от текущей даты."

        # end_date минимум на 1 день позже start_date
        if start_date and end_date and end_date <= start_date:
            errors["end_date"] = "Дата окончания должна быть минимум на 1 день позже даты начала."

        if errors:
            raise serializers.ValidationError(errors)

        return attrs