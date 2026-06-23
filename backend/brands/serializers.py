"""
Сериализаторы для приложения brands.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. BrandListSerializer использует аннотацию min_price из queryset
2. BrandDetailSerializer оптимизирует запрос min_price через annotate
3. Добавлена поддержка предзагруженных данных
"""

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
import logging
from django.db.models import Min

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
    """
    Сериализатор для списка брендов.

    ОПТИМИЗАЦИЯ:
    - Использует аннотацию min_price из queryset
    - Если аннотации нет, делает отдельный запрос
    """
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
        """
        Оптимизированное представление с использованием аннотации.
        """
        data = super().to_representation(instance)

        # Используем аннотацию, если она есть
        if hasattr(instance, 'min_price') and instance.min_price is not None:
            data['min_price'] = instance.min_price
        elif not data.get('min_price'):
            # Fallback: если аннотации нет, делаем запрос
            min_price = instance.nomenclatures.aggregate(
                min_price=Min("pricePerMonth")
            )["min_price"]
            data['min_price'] = min_price

        return data


class BrandDetailSerializer(serializers.ModelSerializer):
    """Полный сериализатор для бренда."""
    logotype = Base64FileField(required=False)
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = "__all__"

    def get_min_price(self, obj):
        """
        Возвращает минимальную цену с оптимизацией.

        Использует аннотацию, если она есть.
        """
        if hasattr(obj, 'min_price'):
            return obj.min_price

        return obj.nomenclatures.aggregate(
            min_price=Min("pricePerMonth")
        )["min_price"]


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

# from rest_framework import serializers
# from rest_framework.exceptions import ValidationError
# import logging
# from django.db.models import Min

# from files.serializers import Base64FileField
# from brands.models import Brand


# logger = logging.getLogger("brands")


# class BrandCreateSerializer(serializers.ModelSerializer):
#     """Схема создания бренда."""
#     logotype = Base64FileField(write_only=True, required=False, allow_null=True)

#     class Meta:
#         model = Brand
#         fields = ("name", "logotype", "description", "code1c")
#         extra_kwargs = {'name': {'validators': []}}

# class BrandListSerializer(serializers.ModelSerializer):
#     logotype = Base64FileField(required=False)
#     min_price = serializers.DecimalField(
#         max_digits=10,
#         decimal_places=2,
#         read_only=True,
#     )
#     class Meta:
#         model = Brand
#         fields = ("id", "name", "logotype", "slug", "min_price")
#         read_only_fields = ("id", "slug")

# class BrandDetailSerializer(serializers.ModelSerializer):
#     logotype = Base64FileField(required=False)
#     min_price = serializers.SerializerMethodField()

#     def get_min_price(self, obj):
#         return obj.nomenclatures.aggregate(
#             min_price=Min("pricePerMonth")
#         )["min_price"]
#     class Meta:
#         model = Brand
#         fields= "__all__"


# class BrandShortSerializer(serializers.ModelSerializer):
#     """Короткий сериализатор — только id и name."""

#     class Meta:
#         model = Brand
#         fields = ("id", "name")

# class BrandCardSerializer(serializers.ModelSerializer):
#     logotype = Base64FileField(required=False)

#     class Meta:
#         model = Brand
#         fields = ("id", "name", "logotype")
#         read_only_fields = fields