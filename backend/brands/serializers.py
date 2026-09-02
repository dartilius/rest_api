"""Сериализаторы приложения brands."""

from django.db.models import Min
from rest_framework import serializers

from brands.models import Brand
from files.serializers import Base64FileField
from nomenclatures.models import Nomenclature


def get_brand_min_price(brand: Brand):
    """Возвращает минимальную цену опубликованных активных точек бренда."""
    return Nomenclature.web.filter(brand=brand).aggregate(
        min_price=Min("pricePerMonth"),
    )["min_price"]


class BrandCreateSerializer(serializers.ModelSerializer):
    """Схема создания и частичного обновления бренда."""

    logotype = Base64FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Brand
        fields = ("name", "logotype", "description", "code1c")
        extra_kwargs = {"name": {"validators": []}}


class BrandListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка брендов."""

    logotype = Base64FileField(required=False)
    min_price = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True,
        required=False,
    )

    class Meta:
        model = Brand
        fields = ("id", "name", "logotype", "slug", "min_price")
        read_only_fields = ("id", "slug")

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["min_price"] = (
            instance.min_price
            if hasattr(instance, "min_price")
            else get_brand_min_price(instance)
        )
        return data


class BrandDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор бренда."""

    logotype = Base64FileField(required=False)
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = "__all__"

    def get_min_price(self, obj):
        return obj.min_price if hasattr(obj, "min_price") else get_brand_min_price(obj)


class BrandShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор — только id и name."""

    class Meta:
        model = Brand
        fields = ("id", "name")


class BrandCardSerializer(serializers.ModelSerializer):
    """Сериализатор для карточки бренда."""

    logotype = Base64FileField(required=False)

    class Meta:
        model = Brand
        fields = ("id", "name", "logotype")
        read_only_fields = fields
