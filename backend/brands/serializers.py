from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from files.serializers import Base64FileField
from brands.models import Brand


class BrandCreateSerializer(serializers.ModelSerializer):
    """схема создания бренда."""
    logotype = Base64FileField(write_only=True, required=False)

    def validate_name(self, name):
        if not name:
            return name

        # Проверяем, существует ли бренд с таким названием
        old_brand = Brand.objects.filter(name=name).first()
        if old_brand:
            # Записываем ошибку в лог-файл
            with open('/app/logs/brand_conflicts.log', 'a', encoding='utf-8') as f:
                f.write(f'{name}: {old_brand.id}\n')

            raise ValidationError({
                'error': 'Brand already exists',
                'existing_brand_id': old_brand.id,
                'message': f'Бренд "{name}" уже существует'
            })
        return name

    class Meta:
        model = Brand
        fields = ("name", "logotype", "description")


class BrandSerializer(serializers.ModelSerializer):
    """Схема чтения бренда."""

    class Meta:
        model = Brand

    fields = ("id", "name", "logotype", "created", "description")
    read_only_fields = ("id", "created")


class BrandShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор — только id и name."""

    class Meta:
        model = Brand
        fields = ("id", "name")
