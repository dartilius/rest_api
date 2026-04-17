from rest_framework import serializers

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
            "all_days", "days_of_week",
            "nomenclature_ids",  # write
            "items",             # read
        ]
        read_only_fields = ["owner"]

    def validate(self, attrs):
        all_days = attrs.get("all_days", True)
        days_of_week = attrs.get("days_of_week", [])

        if not all_days and not days_of_week:
            raise serializers.ValidationError({
                "days_of_week": "Укажите дни недели, если all_days = false."
            })
        if all_days and days_of_week:
            raise serializers.ValidationError({
                "days_of_week": "Нельзя указывать дни недели при all_days = true."
            })
        return attrs