from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from files.serializers import Base64FileField
from brands.models import Brand


class BrandCreateSerializer(serializers.ModelSerializer):
    """Схема создания бренда."""
    logotype = Base64FileField(write_only=True, required=False)

    class Meta:
        model = Brand
        fields = ("name", "logotype", "description", "code1c")
        extra_kwargs = {'name': {'validators': []}}

    def validate(self, attrs):
        name = attrs.get("name")
        code1c = attrs.get("code1c")

        if not name:
            raise ValidationError({"name": "Название бренда обязательно"})

        # --- Проверка уникальности code1c ---
        if code1c:
            old_brand = Brand.objects.filter(code1c=code1c).first()
            if old_brand:
                # Логируем попытку
                with open('/app/network_logs/brand_conflicts.log', 'a', encoding='utf-8') as f:
                    f.write(f'{name}: {old_brand.id}, {getattr(old_brand, "code1c", "—")}\n')

                # Ошибка валидации
                raise ValidationError({
                    "error": "Brand with this code1c already exists",
                    "existing_brand_id": old_brand.id,
                    "existing_brand_name": old_brand.name,
                    "existing_brand_code1c": old_brand.code1c,
                    "message": f"Бренд с кодом '{code1c}' уже существует (id={old_brand.id}, name='{old_brand.name}')",
                })

        # --- Проверка имени ---
        if not code1c:
            # При пустом коде — просто логируем, если имя повторяется (но не запрещаем)
            same_name = Brand.objects.filter(name=name, code1c__isnull=True)
            if same_name.exists():
                with open('/app/network_logs/brand_conflicts.log', 'a', encoding='utf-8') as f:
                    f.write(
                        f"[Повтор имени без кода] "
                        f"Создан бренд '{name}' без кода (уже есть {same_name.count()} похожих)\n"
                    )

        return attrs


class BrandSerializer(serializers.ModelSerializer):
    logotype = Base64FileField(required=False)

    class Meta:
        model = Brand
        fields = ("id", "name", "logotype", "created", "description", "code1c")
        read_only_fields = ("id", "created", "code1c")


class BrandShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор — только id и name."""

    class Meta:
        model = Brand
        fields = ("id", "name", "code1c")
