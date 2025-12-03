from rest_framework import serializers

from promotions.models import Promotion


class PromotionSerializer(serializers.ModelSerializer):
    """Сериализация одной акции"""
    class Meta:
        fields = '__all__'
        read_only_fields = ('id', 'code1c', 'created', 'owner')
        model = Promotion

    def to_representation(self, obj):
        repr_ = super().to_representation(obj)
        repr_["counterparty"] = None
        repr_["main_info"] = {
            "name": obj.name,
            "description": obj.description,
            "relevance": obj.is_active,
        }
        repr_["timeline"] = {
            "start": obj.start_period,
            "end": obj.end_period,
            "created": obj.created,
        }
        if obj.counterparty:
            repr_["counterparty"] = {
                "id": obj.counterparty.id,
                "name": obj.counterparty.name,
                "brands": [
                    {
                        "id": obj.counterparty.brand_id,
                        "name": obj.counterparty.brand_name,
                    }
                ]
            }
        for field in repr_["main_info"]:
            repr_.pop(field, None)

        for field in repr_["timeline"]:
            repr_.pop(field, None)

        return repr_

class PromotionListSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        read_only_fields = ('id', 'code1c', 'created', 'owner')
        model = Promotion

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_["name"] = value.name
        repr_["timeline"] = {
            "start": value.start_period,
            "end": value.end_period,
        }
        repr_["relevance"] = value.is_active
        repr_["counterparty"] = None
        if value.counterparty:
            repr_["counterparty"] = {
                "id": value.counterparty.id,
                "name": value.counterparty.name,
                "brands": [
                    {
                        "id": value.counterparty.brand_id,
                        "name": value.counterparty.brand_name,
                        "description": value.counterparty.brand_description,
                        "logotype": value.counterparty.brand_logotype,
                    }
                ]
            }
        for field in repr_["main_info"]:
            repr_.pop(field)
        for field in repr_["relevance"]:
            repr_.pop(field)
        for field in repr_["timeline"]:
            repr_.pop(field)

        return repr_