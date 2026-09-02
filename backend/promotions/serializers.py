"""Сериализаторы приложения promotions."""

from rest_framework import serializers

from promotions.models import Promotion


def serialize_counterparty(counterparty):
    """Формирует данные контрагента из заранее загруженных брендов."""
    if not counterparty:
        return None

    brands = getattr(counterparty, "_prefetched_brands", counterparty.brands.all())
    return {
        "id": str(counterparty.id),
        "name": counterparty.name,
        "brands": [
            {
                "id": str(brand.id),
                "name": brand.name,
                "description": brand.description,
            }
            for brand in brands
        ],
    }


class PromotionSerializer(serializers.ModelSerializer):
    """Сериализация и валидация одной акции."""

    class Meta:
        model = Promotion
        fields = "__all__"
        read_only_fields = ("id", "code1c", "created", "owner")

    def validate(self, attrs):
        start_period = attrs.get("start_period", getattr(self.instance, "start_period", None))
        end_period = attrs.get("end_period", getattr(self.instance, "end_period", None))
        if start_period and end_period and start_period > end_period:
            raise serializers.ValidationError(
                {"end_period": "Дата окончания не может быть раньше даты начала."},
            )
        return attrs

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["main_info"] = {
            "name": instance.name,
            "description": instance.description,
            "relevance": instance.is_active,
        }
        data["timeline"] = {
            "start": instance.start_period,
            "end": instance.end_period,
        }
        data["counterparty"] = serialize_counterparty(instance.counterparty)
        for field in ("name", "description"):
            data.pop(field, None)
        return data


class PromotionListSerializer(PromotionSerializer):
    """Сериализатор для списка акций."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["relevance"] = instance.is_active
        for field in ("start_period", "end_period", "is_active"):
            data.pop(field, None)
        return data
