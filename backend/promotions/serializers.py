from rest_framework import serializers

from promotions.models import Promotion

class PromotionOutputSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    logotype = serializers.CharField(allow_null=True)
    code1c = serializers.CharField()
    created = serializers.DateTimeField()

    main_info = serializers.SerializerMethodField()
    timeline = serializers.SerializerMethodField()
    counterparty = serializers.SerializerMethodField()

    def get_main_info(self, obj):
        return {
            "name": obj.name,
            "description": obj.description,
            "relevance": obj.is_active,
        }

    def get_timeline(self, obj):
        return {
            "start": obj.start_period,
            "end": obj.end_period,
            "created": obj.created,
        }

    def get_counterparty(self, obj):
        if not obj.counterparty:
            return None
        cp = obj.counterparty
        return {
            "id": cp.id,
            "name": cp.name,
            "brands": [
                {
                    "id": cp.brand_id,
                    "name": cp.brand_name,
                }
            ]
        }


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
        model = Promotion
        fields = '__all__'
        read_only_fields = ('id', 'code1c', 'created', 'owner')

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # timeline
        data["timeline"] = {
            "start": instance.start_period,
            "end": instance.end_period,
        }

        # relevance
        data["relevance"] = instance.is_active

        # counterparty
        if instance.counterparty:
            data["counterparty"] = {
                "id": instance.counterparty.id,
                "name": instance.counterparty.name,
                "brands": [
                    {
                        "id": b.id,
                        "name": b.name,
                        "description": getattr(b, "description", None),
                        # "logotype": getattr(b, "logotype", None),
                    } for b in instance.counterparty.brands.all()
                ]
            }
        else:
            data["counterparty"] = None

        # удаляем лишние поля
        for field in ["start_period", "end_period", "is_active"]:
            data.pop(field, None)

        return data
