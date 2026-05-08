from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import logging

from files.serializers import Base64FileField
from brands.models import Brand


logger = logging.getLogger("brands")


class BrandCreateSerializer(serializers.ModelSerializer):
    """Схема создания бренда."""
    logotype = Base64FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Brand
        fields = ("name", "logotype", "description", "code1c")
        extra_kwargs = {'name': {'validators': []}}

class BrandListSerializer(serializers.ModelSerializer):
    logotype = Base64FileField(required=False)

    class Meta:
        model = Brand
        fields = ("id", "name", "logotype", "slug")
        read_only_fields = ("id", "slug")

class BrandDetailSerializer(serializers.ModelSerializer):
    logotype = Base64FileField(required=False)
    class Meta:
        model = Brand
        fields= "__all__"


class BrandShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор — только id и name."""

    class Meta:
        model = Brand
        fields = ("id", "name")

class BrandCardSerializer(serializers.ModelSerializer):
    logotype = Base64FileField(required=False)

    class Meta:
        model = Brand
        fields = ("id", "name", "logotype")
        read_only_fields = fields