"""Standalone serializers for the 1C counterparty directory."""

from rest_framework import serializers

from counterparties.models import Counterparty


class Counterparty1CSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        return obj.name

    class Meta:
        model = Counterparty
        fields = "__all__"
        read_only_fields = ("id", "created", "name", "owner")
        extra_kwargs = {
            field.name: {"required": False, "allow_null": field.null}
            for field in Counterparty._meta.fields
            if field.name not in {"id", "created", "owner"}
        }
