from rest_framework import serializers

from feedback.models import Feedback
from placement_order.models import PlacementOrder
from placement_order.serializers import AttributionField


class FeedbackSerializer(serializers.ModelSerializer):
    # Фронт шлёт camelCase — маппим в snake_case модели
    brandId = serializers.CharField(source="brand_id", required=False, allow_null=True, allow_blank=True)
    nomenclaturesIds = serializers.ListField(
        child=serializers.CharField(),
        source="nomenclatures_ids",
        required=False,
        allow_null=True,
    )
    placement_order_id = serializers.PrimaryKeyRelatedField(
        source="placement_order",
        queryset=PlacementOrder.objects.all(),
        required=False,
        allow_null=True,
    )
    attribution = AttributionField(required=False, allow_null=True)

    class Meta:
        model = Feedback
        fields = [
            "id",
            "code1c",
            "name",
            "phone",
            "email",
            "message",
            "pathname",
            "brandId",
            "nomenclaturesIds",
            "placement_order_id",
            "attribution",
            "created",
        ]
        read_only_fields = ["id", "created"]

    def validate(self, attrs):
        placement_order = attrs.get("placement_order")
        attribution = attrs.get("attribution")
        if placement_order and attribution and placement_order.attribution:
            if attribution != placement_order.attribution:
                raise serializers.ValidationError({
                    "attribution": "Must match the linked placement order attribution."
                })
        if placement_order and attribution is None:
            attrs["attribution"] = placement_order.attribution
        return attrs
