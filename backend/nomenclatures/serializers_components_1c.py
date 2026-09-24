"""Independent 1C serializers for nomenclature component resources."""

from rest_framework import serializers

from files.serializers import Base64FileField
from nomenclatures.models import DiscountRule, NomenclatureMedia, NomenclatureTenant, TypeOfPlace


class TypeOfPlace1CSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeOfPlace
        fields = "__all__"
        read_only_fields = ("id",)
        extra_kwargs = {field.name: {"required": False, "allow_null": field.null} for field in TypeOfPlace._meta.fields if field.name != "id"}

    def create(self, validated_data):
        if not (validated_data.get("name") or "").strip():
            validated_data["name"] = "1C place type"
        return super().create(validated_data)


class NomenclatureTenant1CSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)

    class Meta:
        model = NomenclatureTenant
        fields = ("id", "tenant", "brand", "floor", "atm")
        read_only_fields = ("id",)
        extra_kwargs = {"tenant": {"required": False, "allow_null": True}, "brand": {"required": False, "allow_null": True}, "floor": {"required": False, "allow_blank": True}, "atm": {"required": False}}


class DiscountRule1CSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(source="public_id", read_only=True)

    class Meta:
        model = DiscountRule
        fields = ("id", "days_from", "days_to", "coefficient")
        read_only_fields = ("id",)
        extra_kwargs = {"days_from": {"required": False}, "days_to": {"required": False, "allow_null": True}, "coefficient": {"required": False}}

    def create(self, validated_data):
        validated_data.setdefault("days_from", 0)
        validated_data.setdefault("coefficient", 1)
        return super().create(validated_data)


class NomenclatureMedia1CSerializer(serializers.ModelSerializer):
    source = Base64FileField(required=False, allow_null=True)

    class Meta:
        model = NomenclatureMedia
        fields = ("id", "media_type", "type", "source", "created", "hash")
        read_only_fields = ("id", "created", "hash")
        extra_kwargs = {"media_type": {"required": False}, "type": {"required": False, "allow_null": True}}
