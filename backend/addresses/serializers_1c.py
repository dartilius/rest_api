"""Standalone serializers for the 1C address directory."""

from rest_framework import serializers

from addresses.models import Address


class Address1CSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ("id",)
        extra_kwargs = {
            field.name: {"required": False, "allow_null": field.null}
            for field in Address._meta.fields
            if field.name != "id"
        }
