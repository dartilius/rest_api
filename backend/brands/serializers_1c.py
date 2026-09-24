"""Standalone serializers for the 1C brand directory."""

from rest_framework import serializers

from brands.models import Brand
from files.serializers import Base64FileField


class Brand1CSerializer(serializers.ModelSerializer):
    logotype = Base64FileField(required=False, allow_null=True)

    class Meta:
        model = Brand
        fields = ("id", "name", "slug", "code1c", "description", "logotype", "created")
        read_only_fields = ("id", "slug", "created")
        extra_kwargs = {
            "name": {"required": False, "allow_blank": True},
            "code1c": {"required": False, "allow_null": True, "allow_blank": True},
            "description": {"required": False, "allow_null": True, "allow_blank": True},
        }

    def create(self, validated_data):
        if not (validated_data.get("name") or "").strip():
            validated_data["name"] = "1C brand"
        return super().create(validated_data)
