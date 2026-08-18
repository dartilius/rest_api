
"""
Сериализаторы для приложения nomenclatures.

Данный модуль содержит сериализаторы для работы с моделью Nomenclature и связанными сущностями.
Основной сериализатор - NomenclatureSerializer - обеспечивает полный CRUD функционал
с оптимизированной обработкой PATCH запросов.

ОСОБЕННОСТИ РЕАЛИЗАЦИИ:
───────────────────────────────────────────────────────────────────────────────
1. Оптимизированный PATCH - обработка только реально измененных полей
2. Атомарные транзакции - гарантия целостности данных
3. Разделение логики создания и обновления
4. Поддержка вложенных объектов (tenants, address, brand, legalEntity)

АРХИТЕКТУРА:
───────────────────────────────────────────────────────────────────────────────
NomenclatureSerializer
├── Поля (fields)
│   ├── read_only: для отображения (brand, legalEntity, address, etc.)
│   ├── write_only: для записи (brand_id, legalEntity_id, tenants_id, etc.)
│   └── read_write: обычные поля (name, description, etc.)
├── Валидация (validate_*)
│   ├── validate_settings() - проверка настроек вещания
│   └── validate() - общая валидация
├── Создание (create)
│   └── @transaction.atomic - атомарное создание со всеми связями
├── Обновление (update)
│   ├── _get_current_values() - получение текущих значений
│   ├── _has_field_changed() - проверка изменения поля
│   ├── _update_tenants() - обновление арендаторов
│   ├── _update_address() - обновление адреса
│   └── @transaction.atomic - атомарное обновление
└── Представление (to_representation)
    └── Формирование ответа для клиента
"""

import hashlib
import json
from datetime import time
from typing import Optional, Dict, Any, Set, List, Tuple, Union

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Model
from django.utils import timezone
from rest_framework import serializers

from addresses.models import Address as AddressBook
from addresses.serializers import (
    AddressCreateSerializer,
    AddressReadSerializer,
    AddressWebResultSerializer
)
from brands.models import Brand
from brands.serializers import BrandListSerializer, BrandCardSerializer
from counterparties.models import Counterparty
from counterparties.serializers import CounterpartiesShortSerializer
from files.serializers import Base64FileField
from nomenclatures.models import (
    Nomenclature,
    StatusHistory,
    TIMEZONES,
    NomenclatureImage,
    NomenclatureAddress,
    AVAILABLE_CONTENT_TYPES,
    TypeOfPlace,
    NomenclatureTenant,
    DiscountRule,
)
from api.base_objects import Article

# Регистрация кастомных типов полей для DRF
serializers.ModelSerializer.serializer_field_mapping[Article] = serializers.IntegerField

# Разрешенные форматы для загрузки изображений
ALLOWED_FORMATS = ("jpg", "jpeg", "png", "webp")


# ═══════════════════════════════════════════════════════════════════════════════
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ═══════════════════════════════════════════════════════════════════════════════

def format_local_datetime(value):
    """
    Форматирует datetime в локальное время без часового пояса.

    Аргументы:
        value (datetime): Объект datetime для форматирования

    Возвращает:
        str: Строка в формате 'YYYY-MM-DD HH:MM:SS' в локальном времени

    Пример:
        >>> format_local_datetime(datetime(2026, 6, 22, 9, 0, 0))
        '2026-06-22 09:00:00'
    """
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_default_timezone())
    return f"{timezone.localtime(value):%Y-%m-%d %H:%M:%S}"


# ═══════════════════════════════════════════════════════════════════════════════
# СЕРИАЛИЗАТОРЫ ДЛЯ СВЯЗАННЫХ СУЩНОСТЕЙ
# ═══════════════════════════════════════════════════════════════════════════════

class DiscountRuleSerializer(serializers.ModelSerializer):
    """Сериализатор для правил скидок."""

    class Meta:
        model = DiscountRule
        fields = ("id", "days_from", "days_to", "coefficient")
        read_only_fields = ("id",)


class PhotoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для фотографий номенклатуры.

    Поддерживает загрузку изображений в формате Base64.
    Выполняет проверку формата и размера файла.
    """

    source = Base64FileField()

    class Meta:
        model = NomenclatureImage
        fields = ("id", "source", "type", "created")
        read_only_fields = ("id", "created")

    def validate_source(self, file):
        """
        Валидация загружаемого файла.

        Аргументы:
            file (File): Загружаемый файл

        Возвращает:
            File: Валидный файл

        Исключения:
            ValidationError: Если формат не поддерживается или превышен размер
        """
        ext = file.name.split(".")[-1].lower()
        if ext not in ALLOWED_FORMATS:
            raise serializers.ValidationError(
                f"Недопустимый формат файла. Разрешены: {', '.join(ALLOWED_FORMATS)}"
            )
        if file.size > 15 * 1024 * 1024:
            raise serializers.ValidationError("Максимальный размер файла 15MB")
        return file

    def validate(self, attrs):
        """
        Проверка дубликатов по хешу.

        Аргументы:
            attrs (dict): Валидируемые атрибуты

        Возвращает:
            dict: Валидные атрибуты

        Исключения:
            ValidationError: Если фотография уже существует
        """
        nomenclature = self.context.get("nomenclature")
        if not nomenclature:
            raise serializers.ValidationError("Номенклатура не передана")

        file_data = attrs["source"].read()
        file_hash = hashlib.md5(file_data).hexdigest()
        attrs["source"].seek(0)

        if NomenclatureImage.objects.filter(
            nomenclature=nomenclature,
            hash=file_hash
        ).exists():
            raise serializers.ValidationError(
                "Эта фотография уже прикреплена к номенклатуре"
            )
        return attrs

    def create(self, validated_data):
        """
        Создание фотографии с привязкой к номенклатуре.

        Аргументы:
            validated_data (dict): Валидные данные

        Возвращает:
            NomenclatureImage: Созданный объект
        """
        validated_data["nomenclature"] = self.context["nomenclature"]
        return super().create(validated_data)


class InNomenclaturePhotoSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для фотографий внутри номенклатуры."""

    class Meta:
        model = NomenclatureImage
        fields = ("source", "id")
        read_only_fields = ("source", "id")


class TypeOfPlaceWebSerializer(serializers.ModelSerializer):
    """Сериализатор для типа места в веб-интерфейсе."""

    class Meta:
        model = TypeOfPlace
        fields = ("name", "abbreviation")
        read_only_fields = fields


class TypeOfPlaceSerializer(serializers.ModelSerializer):
    """Полный сериализатор для типа места."""

    class Meta:
        model = TypeOfPlace
        fields = "__all__"
        read_only_fields = ("id",)


class TenantWriteSerializer(serializers.Serializer):
    """
    Сериализатор для записи арендаторов.

    Используется как write_only поле в NomenclatureSerializer.
    """

    id = serializers.UUIDField()
    floor = serializers.CharField(required=False, allow_blank=True)
    atm = serializers.BooleanField(required=False, default=False)
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    def validate_id(self, value):
        """
        Проверка существования арендатора.

        Аргументы:
            value (UUID): ID арендатора

        Возвращает:
            UUID: Валидный ID

        Исключения:
            ValidationError: Если арендатор не найден
        """
        try:
            Counterparty.objects.get(id=value)
            return value
        except Counterparty.DoesNotExist:
            raise serializers.ValidationError(
                f"Арендатор с id {value} не найден"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# СЕРИАЛИЗАТОРЫ ДЛЯ СПИСКОВ И КАРТОЧЕК
# ═══════════════════════════════════════════════════════════════════════════════

class ShortBrandNomenclatureSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой информации о номенклатуре с брендом."""

    brand_name = serializers.CharField(source='brand.name', default='Без значения')
    brand_id = serializers.CharField(source='brand.id', default=None)
    brand_logotype = Base64FileField(source="brand.logotype", default=None)
    type_of_place = serializers.CharField(source='typeOfPlace.name', default=None)
    tenants_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Nomenclature
        fields = (
            "brand_name", "brand_id", "brand_logotype",
            "type_of_place", "tenants_count"
        )
        read_only_fields = fields


class NomenclatureTenantResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа с арендаторами номенклатуры."""

    id = serializers.UUIDField(read_only=True)
    tenant_id = serializers.SerializerMethodField()
    brands_list = serializers.SerializerMethodField()
    logotype = serializers.SerializerMethodField()
    floor = serializers.CharField(read_only=True)
    atm = serializers.BooleanField(read_only=True)
    brand_id = serializers.SerializerMethodField()

    class Meta:
        model = NomenclatureTenant
        fields = ('id', 'brands_list', 'logotype', 'floor', 'atm', 'brand_id', 'tenant_id')

    def get_brands_list(self, obj):
        """Возвращает название бренда."""
        if obj.brand:
            return obj.brand.name
        return f"Бренд не указан (tenant: {obj.tenant.id})"

    def get_logotype(self, obj):
        """Возвращает URL логотипа бренда."""
        if obj.brand and obj.brand.logotype:
            if hasattr(obj.brand.logotype, 'url'):
                return obj.brand.logotype.url
            return str(obj.brand.logotype)
        return None

    def get_brand_id(self, obj):
        """Возвращает ID бренда."""
        return str(obj.brand.id) if obj.brand else None

    def get_tenant_id(self, obj):
        """Возвращает ID арендатора."""
        return str(obj.tenant.id) if obj.tenant else None


class NomenclatureSearchSerializer(serializers.ModelSerializer):
    """Сериализатор для поиска номенклатур."""

    brand_name = serializers.SerializerMethodField()
    type_of_place_name = serializers.SerializerMethodField()
    legal_entity_name = serializers.SerializerMethodField()
    responsible_ad_name = serializers.SerializerMethodField()
    tenants_names = serializers.SerializerMethodField()

    class Meta:
        model = Nomenclature
        fields = [
            'id', 'name', 'code1c', 'contentType', 'version',
            'brand_name', 'type_of_place_name',
            'legal_entity_name', 'responsible_ad_name', 'tenants_names'
        ]

    def get_brand_name(self, obj):
        """Возвращает название бренда."""
        return obj.brand.name if obj.brand else None

    def get_type_of_place_name(self, obj):
        """Возвращает название типа места."""
        return obj.typeOfPlace.name if obj.typeOfPlace else None

    def get_legal_entity_name(self, obj):
        """Возвращает полное название юридического лица."""
        if not obj.legalEntity:
            return None
        try:
            le = obj.legalEntity
            parts = []
            if le.last_name:
                parts.append(str(le.last_name))
            if le.first_name:
                parts.append(str(le.first_name))
            if le.middle_name:
                parts.append(str(le.middle_name))
            if le.additional_name:
                parts.append(f"({str(le.additional_name)})")
            if le.keyword:
                parts.append(f"[{str(le.keyword)}]")
            return ' '.join(parts) if parts else None
        except Exception:
            return None

    def get_responsible_ad_name(self, obj):
        """Возвращает имя ответственного за рекламу."""
        if not obj.responsible_ad:
            return None
        try:
            return f"{obj.responsible_ad.last_name or ''} {obj.responsible_ad.first_name or ''}".strip() or None
        except Exception:
            return None

    def get_tenants_names(self, obj):
        """Возвращает список имен арендаторов (макс. 3)."""
        try:
            result = []
            for t in obj.tenants.all()[:3]:
                parts = []
                if t.last_name:
                    parts.append(str(t.last_name))
                if t.first_name:
                    parts.append(str(t.first_name))
                if t.middle_name:
                    parts.append(str(t.middle_name))
                if t.additional_name:
                    parts.append(f"({str(t.additional_name)})")
                if t.keyword:
                    parts.append(f"[{str(t.keyword)}]")
                if parts:
                    result.append(' '.join(parts))
            return result
        except Exception:
            return []


class CityNomenclaturesSerializer(serializers.ModelSerializer):
    """Сериализатор для номенклатур по городу (веб-интерфейс)."""

    typeOfPlace = serializers.CharField(source='typeOfPlace.name', read_only=True)
    formattedAddress = serializers.SerializerMethodField()
    exterior = serializers.SerializerMethodField()
    brand = BrandListSerializer(read_only=True)

    class Meta:
        model = Nomenclature
        fields = [
            "id", "formattedAddress",
            "pricePerMonth", "exterior", "brand", "typeOfPlace"
        ]

    def get_exterior(self, obj):
        """Возвращает список фотографий экстерьера."""
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="exterior"), many=True
        ).data

    def get_formattedAddress(self, obj):
        """
        Возвращает отформатированный адрес с координатами.

        Аргументы:
            obj (Nomenclature): Объект номенклатуры

        Возвращает:
            dict: {
                'name': str,  # отформатированный адрес
                'coordinates': {'latitude': str, 'longitude': str}
            }
        """
        try:
            nomenclature_address = obj.address
        except ObjectDoesNotExist:
            return {"name": "", "coordinates": {"latitude": None, "longitude": None}}

        if not nomenclature_address or not nomenclature_address.address:
            return {"name": "", "coordinates": {"latitude": None, "longitude": None}}

        address = nomenclature_address.address
        if not address:
            return {"name": "", "coordinates": {"latitude": None, "longitude": None}}

        address_parts = []
        if address.city and address.city.name:
            address_parts.append(f"г. {address.city.name}")
        if address.street and address.street.name:
            address_parts.append(f"ул. {address.street.name}")

        house_number = None
        if address.house and address.house.number:
            house_number = address.house.number
        elif address.building and address.building.number:
            house_number = address.building.number
        if house_number:
            address_parts.append(house_number)

        latitude = None
        longitude = None
        if hasattr(address, 'coordinates') and address.coordinates:
            try:
                if hasattr(address.coordinates, 'latitude'):
                    latitude = str(address.coordinates.latitude) if address.coordinates.latitude else None
                if hasattr(address.coordinates, 'longitude'):
                    longitude = str(address.coordinates.longitude) if address.coordinates.longitude else None
            except (AttributeError, TypeError):
                pass

        return {
            "name": ', '.join(address_parts),
            "coordinates": {"latitude": latitude, "longitude": longitude}
        }


class NomenclatureWebSerializer(serializers.ModelSerializer):
    """Сериализатор для веб-интерфейса номенклатур."""

    brand = BrandCardSerializer(read_only=True)
    typeOfPlace = TypeOfPlaceWebSerializer(read_only=True)
    legalEntity = CounterpartiesShortSerializer(read_only=True)
    exterior = serializers.SerializerMethodField()
    interior = serializers.SerializerMethodField()
    contentType = serializers.ChoiceField(
        choices=list(AVAILABLE_CONTENT_TYPES.keys()),
        required=False,
    )
    worktime_start = serializers.TimeField(format='%H:%M', required=False, allow_null=True)
    worktime_end = serializers.TimeField(format='%H:%M', required=False, allow_null=True)
    oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)
    address = AddressWebResultSerializer(source="address.address", read_only=True)

    class Meta:
        model = Nomenclature
        fields = (
            "id", "address", "typeOfPlace", "address",
            "worktime_start", "worktime_end", "oldCatalogSlug", "address",
            "legalEntity", "exterior", "interior", "contentType", "brand",
            "description", "possibility", "pricePerMonth",
            "external_video_media", "external_audio_media",
            "internal_video_media", "internal_audio_media",
            "responsible_ad", "nomenclature_tenants"
        )
        read_only_fields = fields

    def get_interior(self, obj):
        """Возвращает список фотографий интерьера."""
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="interior"), many=True
        ).data

    def get_exterior(self, obj):
        """Возвращает список фотографий экстерьера."""
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="exterior"), many=True
        ).data

    def _user_id_name(self, user):
        """Возвращает информацию о пользователе."""
        if not user:
            return None
        basic_phones = list(
            user.contacts_cp
            .filter(type="phone", basic=True)
            .values_list("meaning", flat=True)
        )
        if not basic_phones and user.phone_number:
            basic_phones = [str(user.phone_number)]
        phones = [str(p) for p in basic_phones if p]
        return {
            "id": str(user.id),
            "full_name": user.first_name,
            "phone_number": phones,
        }

    def to_representation(self, instance):
        """Формирует ответ с преобразованием полей."""
        repr_ = super().to_representation(instance)
        if "contentType" in repr_:
            key = repr_["contentType"]
            repr_["contentType"] = AVAILABLE_CONTENT_TYPES.get(key, key)
        repr_["responsible"] = {
            "ad": self._user_id_name(instance.responsible_ad),
        }
        repr_["tenants_length"] = instance.tenants.count()
        fields_to_remove = ["responsible_ad", "nomenclature_tenants"]
        for field in fields_to_remove:
            repr_.pop(field, None)
        return repr_


class NomenclatureWebMapBrandSerializer(serializers.ModelSerializer):
    """Бренд в выдаче точек публичной карты."""

    logotype = Base64FileField(required=False)

    class Meta:
        model = Brand
        fields = ("name", "logotype")
        read_only_fields = fields


class NomenclatureWebMapFacadeSerializer(serializers.ModelSerializer):
    """Первое фото фасада в выдаче точек публичной карты."""

    class Meta:
        model = NomenclatureImage
        fields = ("id", "source")
        read_only_fields = fields


class NomenclatureWebMapPlaceSerializer(serializers.ModelSerializer):
    """Компактная номенклатура для отображения на карте."""

    brand = NomenclatureWebMapBrandSerializer(read_only=True)
    type_of_place = serializers.CharField(
        source="typeOfPlace.abbreviation",
        read_only=True,
        allow_null=True,
    )
    coordinates = serializers.SerializerMethodField()
    facade = serializers.SerializerMethodField()
    old_slug = serializers.CharField(source="old_catalog_slug", read_only=True)

    class Meta:
        model = Nomenclature
        fields = (
            "id",
            "name",
            "coordinates",
            "type_of_place",
            "brand",
            "facade",
            "old_slug",
        )
        read_only_fields = fields

    def get_coordinates(self, obj):
        try:
            address = obj.address.address
            coordinates = address.coordinates if address else None
        except ObjectDoesNotExist:
            coordinates = None

        if not coordinates:
            return None

        return {
            "latitude": str(coordinates.latitude) if coordinates.latitude else None,
            "longitude": str(coordinates.longitude) if coordinates.longitude else None,
        }

    def get_facade(self, obj):
        facades = getattr(obj, "prefetched_facades", None)
        image = facades[0] if facades else None
        if image is None and facades is None:
            image = obj.images.filter(type="exterior").first()
        return NomenclatureWebMapFacadeSerializer(image).data if image else None


class NomenclatureWebSearchRequestSerializer(serializers.Serializer):
    """Фильтры и пагинация read-only поиска публичного каталога."""

    search = serializers.CharField(required=False, allow_blank=True, max_length=255)
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    id = serializers.UUIDField(required=False)
    code1c = serializers.CharField(required=False, allow_blank=True, max_length=64)
    versions = serializers.ListField(
        child=serializers.CharField(max_length=127), required=False, max_length=100
    )
    version = serializers.CharField(required=False, allow_blank=True, max_length=127)
    timezone = serializers.CharField(required=False, allow_blank=True, max_length=31)
    status = serializers.ChoiceField(
        choices=("0", "1", "2", "null"), required=False
    )
    brand_id = serializers.UUIDField(required=False)
    brand_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, max_length=100
    )
    type_of_place_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, max_length=100
    )
    city_slugs = serializers.ListField(
        child=serializers.SlugField(max_length=255), required=False, max_length=100
    )
    city_slug = serializers.SlugField(required=False, max_length=255)
    legal_entity_name = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    brand_name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    type_of_place = serializers.CharField(
        required=False, allow_blank=True, max_length=255
    )
    content_types = serializers.ListField(
        child=serializers.ChoiceField(choices=list(AVAILABLE_CONTENT_TYPES)),
        required=False,
        max_length=len(AVAILABLE_CONTENT_TYPES),
    )
    price_from = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=0
    )
    price_to = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, min_value=0
    )
    has_facade = serializers.BooleanField(required=False)
    ordering = serializers.ChoiceField(
        choices=(
            "default",
            "name",
            "-name",
            "price_per_month",
            "-price_per_month",
            "pricePerMonth",
            "-pricePerMonth",
            "version",
            "-version",
            "timezone",
            "-timezone",
            "brand_name",
            "-brand_name",
            "legal_entity_name",
            "-legal_entity_name",
            "type_place",
            "-type_place",
            "created",
            "-created",
        ),
        required=False,
        default="default",
    )
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=24)

    def validate(self, attrs):
        search = attrs.get("search", "").strip()
        if search and len(search) < 3:
            raise serializers.ValidationError(
                {"search": "Поисковый запрос должен содержать не менее 3 символов."}
            )
        price_from = attrs.get("price_from")
        price_to = attrs.get("price_to")
        if price_from is not None and price_to is not None and price_from > price_to:
            raise serializers.ValidationError(
                {"price_to": "Должна быть больше или равна price_from."}
            )
        return attrs


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка номенклатур."""

    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
    brand = BrandListSerializer()
    legalEntity = CounterpartiesShortSerializer()
    exterior = serializers.SerializerMethodField()
    formattedAddress = serializers.CharField(source="formatted_address", read_only=True)
    oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)

    class Meta:
        model = Nomenclature
        fields = (
            "id", "name", "legalEntity", "brand",
            "exterior", "formattedAddress", "typeOfPlace",
            "pricePerMonth", "code1c", "oldCatalogSlug",
        )
        extra_fields = ("formattedAddress", "oldCatalogSlug")
        read_only_fields = fields

    def get_exterior(self, obj):
        """Возвращает список фотографий экстерьера."""
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="exterior"), many=True
        ).data

    def get_status(self, obj):
        """Возвращает статус доступности."""
        try:
            return obj.availability.status
        except AttributeError:
            return None

    def get_last_answer(self, obj):
        """Возвращает время последнего ответа."""
        try:
            return format_local_datetime(obj.availability.last_answer_date)
        except AttributeError:
            return "Не выходила в сеть"


class StatusHistorySerializer(serializers.ModelSerializer):
    """Сериализатор для истории доступности."""

    class Meta:
        fields = ("change_time", "status")
        read_only_fields = fields
        model = StatusHistory

    def to_representation(self, value):
        """Форматирует время изменения в локальное время."""
        repr_ = super().to_representation(value)
        repr_["change_time"] = format_local_datetime(value.change_time)
        repr_["timezone"] = timezone.get_current_timezone_name()
        return repr_


class NomenclatureCardSerializer(serializers.ModelSerializer):
    """Минимальный сериализатор для карточек каталога и корзины."""

    brand = BrandCardSerializer()
    exterior = serializers.SerializerMethodField()
    formattedAddress = serializers.SerializerMethodField()
    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
    slotsPerHour = serializers.CharField(source="slots_per_hour", read_only=True)
    oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)

    class Meta:
        model = Nomenclature
        fields = (
            "id", "brand", "exterior",
            "formattedAddress", "typeOfPlace", "pricePerMonth",
            "slotsPerHour", "oldCatalogSlug"
        )
        read_only_fields = fields

    def get_exterior(self, obj):
        """Возвращает первое фото экстерьера."""
        prefetched_exterior = getattr(obj, "prefetched_exterior", None)
        if prefetched_exterior is None:
            image = obj.images.filter(type="exterior").first()
        else:
            image = prefetched_exterior[0] if prefetched_exterior else None
        if not image:
            return []
        return InNomenclaturePhotoSerializer([image], many=True).data

    def get_formattedAddress(self, obj):
        """Возвращает адрес в формате, который использует карта каталога."""
        empty_address = {
            "name": "",
            "coordinates": {"latitude": None, "longitude": None},
        }

        try:
            nomenclature_address = obj.address
        except ObjectDoesNotExist:
            return empty_address

        if not nomenclature_address or not nomenclature_address.address:
            return empty_address

        address = nomenclature_address.address
        address_parts = []

        if address.city and address.city.name:
            address_parts.append(f"г. {address.city.name}")
        if address.street and address.street.name:
            address_parts.append(f"ул. {address.street.name}")

        house_number = None
        if address.house and address.house.number:
            house_number = address.house.number
        elif address.building and address.building.number:
            house_number = address.building.number
        if house_number:
            address_parts.append(house_number)

        coordinates = address.coordinates
        return {
            "name": ', '.join(address_parts),
            "coordinates": {
                "latitude": (
                    str(coordinates.latitude)
                    if coordinates and coordinates.latitude
                    else None
                ),
                "longitude": (
                    str(coordinates.longitude)
                    if coordinates and coordinates.longitude
                    else None
                ),
            },
        }


class NomenclatureWebSearchResponseSerializer(serializers.Serializer):
    """Страница результатов публичного поиска."""

    count = serializers.IntegerField(read_only=True)
    page = serializers.IntegerField(read_only=True)
    limit = serializers.IntegerField(read_only=True)
    next_page = serializers.IntegerField(read_only=True, allow_null=True)
    previous_page = serializers.IntegerField(read_only=True, allow_null=True)
    results = NomenclatureCardSerializer(many=True, read_only=True)


class NomenclatureWebMapResponseSerializer(serializers.Serializer):
    """Полный набор точек карты для заданных фильтров."""

    count = serializers.IntegerField(read_only=True)
    results = NomenclatureWebMapPlaceSerializer(many=True, read_only=True)


class NomenclatureShortSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для номенклатур."""

    formattedAddress = serializers.SerializerMethodField()
    exterior = serializers.SerializerMethodField()
    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)

    class Meta:
        model = Nomenclature
        fields = [
            "id", "formattedAddress",
            "exterior", "typeOfPlace", "pricePerMonth"
        ]

    def get_formattedAddress(self, obj):
        """Возвращает отформатированный адрес."""
        try:
            nomenclature_address = obj.address
        except ObjectDoesNotExist:
            return ""

        if not nomenclature_address or not nomenclature_address.address:
            return ""

        address = nomenclature_address.address
        address_parts = []
        if address.city and address.city.name:
            address_parts.append(f"г. {address.city.name}")
        if address.street and address.street.name:
            address_parts.append(f"ул. {address.street.name}")

        house_number = None
        if address.house and address.house.number:
            house_number = address.house.number
        elif address.building and address.building.number:
            house_number = address.building.number
        if house_number:
            address_parts.append(house_number)
        return ', '.join(address_parts)

    def get_exterior(self, obj):
        """Возвращает первое фото экстерьера."""
        image = obj.images.filter(type="exterior").first()
        if not image:
            return []
        return InNomenclaturePhotoSerializer([image], many=True).data


# ═══════════════════════════════════════════════════════════════════════════════
# ОСНОВНОЙ СЕРИАЛИЗАТОР - NomenclatureSerializer
# ═══════════════════════════════════════════════════════════════════════════════

class NomenclatureSerializer(serializers.ModelSerializer):
    """
    Основной сериализатор для модели Nomenclature.

    Обеспечивает полный CRUD функционал с оптимизированной обработкой PATCH запросов.

    ПОЛЯ:
    ───────────────────────────────────────────────────────────────────────────────
    read_only (только для чтения):
        - typeOfPlace: Название типа места
        - status: Статус доступности
        - last_answer: Время последнего ответа
        - legalEntity: Информация о юридическом лице
        - brand: Информация о бренде
        - address: Информация об адресе
        - exterior: Список фото экстерьера
        - interior: Список фото интерьера
        - article: Артикул (автоинкремент)
        - formattedAddress: Отформатированный адрес
        - oldCatalogSlug: Старый slug для редиректов

    write_only (только для записи):
        - typeOfPlace_id: ID типа места (FK)
        - legalEntity_id: ID юридического лица (FK)
        - brand_id: ID бренда (FK)
        - tenants_id: Список арендаторов (с вложенными данными)
        - address_data: Данные для создания адреса
        - address_id: ID существующего адреса

    read_write (чтение и запись):
        - name: Название
        - description: Описание
        - timezone: Часовой пояс
        - settings: Настройки вещания
        - code1c: Код из 1С
        - contentType: Тип контента
        - pricePerMonth: Стоимость в месяц
        - responsible_*: Ответственные лица
        - worktime_start: Время открытия
        - worktime_end: Время закрытия

    МЕТОДЫ:
    ───────────────────────────────────────────────────────────────────────────────
    validate_settings(value) -> dict
        Валидация настроек вещания. Проверяет форматы времени и диапазоны громкости.

    create(validated_data) -> Nomenclature
        Создание номенклатуры с атомарной транзакцией.
        Обрабатывает все связи: brand, legalEntity, typeOfPlace, address, tenants.

    update(instance, validated_data) -> Nomenclature
        Частичное обновление с оптимизацией.
        Определяет реально измененные поля и обрабатывает только их.

    to_representation(instance) -> dict
        Формирует ответ для клиента.
        Добавляет вычисляемые поля и группирует данные.

    ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ:
    ───────────────────────────────────────────────────────────────────────────────
    _get_current_values(instance) -> dict
        Возвращает текущие значения полей из базы данных.

    _has_field_changed(instance, field_name, new_value, current_values) -> bool
        Проверяет, изменилось ли поле реально.

    _update_tenants(instance, tenants_data) -> None
        Обновляет арендаторов (полная замена).

    _update_address(instance, address_data) -> None
        Обновляет адрес по данным.

    _update_address_by_id(instance, address_id) -> None
        Обновляет адрес по ID.
    """

    # ─── READ_ONLY ПОЛЯ ────────────────────────────────────────────────────────

    typeOfPlace = serializers.CharField(source='typeOfPlace.name', read_only=True)
    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()
    legalEntity = CounterpartiesShortSerializer(read_only=True)
    brand = BrandListSerializer(read_only=True)
    address = AddressReadSerializer(source="address.address", read_only=True)
    exterior = serializers.SerializerMethodField()
    interior = serializers.SerializerMethodField()
    article = serializers.IntegerField(read_only=True)
    formattedAddress = serializers.SerializerMethodField()
    oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)

    # ─── WRITE_ONLY ПОЛЯ ──────────────────────────────────────────────────────

    typeOfPlace_id = serializers.PrimaryKeyRelatedField(
        queryset=TypeOfPlace.objects.all(),
        source="typeOfPlace",
        write_only=True,
        required=False,
        allow_null=True,
    )
    legalEntity_id = serializers.PrimaryKeyRelatedField(
        queryset=Counterparty.objects.all(),
        source="legalEntity",
        write_only=True,
        required=False,
        allow_null=True,
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        source="brand",
        write_only=True,
        required=False,
        allow_null=True,
    )
    tenants_id = TenantWriteSerializer(
        many=True,
        write_only=True,
        required=False
    )
    address_data = AddressCreateSerializer(
        source="address.address",
        required=False,
        write_only=True
    )
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=AddressBook.objects.all(),
        source="address.address",
        write_only=True,
        required=False,
        allow_null=True,
    )

    # ─── READ_WRITE ПОЛЯ ──────────────────────────────────────────────────────

    code1c = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    contentType = serializers.ChoiceField(
        choices=list(AVAILABLE_CONTENT_TYPES.keys()),
        required=False,
    )
    worktime_start = serializers.TimeField(format='%H:%M', required=False, allow_null=True)
    worktime_end = serializers.TimeField(format='%H:%M', required=False, allow_null=True)

    class Meta:
        model = Nomenclature
        fields = "__all__"
        read_only_fields = (
            "id", "owner", "hw_info", "version", "created",
            "status", "last_answer", "interior", "exterior",
            "typeOfPlace", "formattedAddress",
        )

    # ═════════════════════════════════════════════════════════════════════════
    # МЕТОДЫ ДЛЯ READ_ONLY ПОЛЕЙ
    # ═════════════════════════════════════════════════════════════════════════

    def get_status(self, obj) -> Optional[int]:
        """
        Возвращает статус доступности номенклатуры.

        Аргументы:
            obj (Nomenclature): Объект номенклатуры

        Возвращает:
            Optional[int]: Код статуса (0-Online, 1-Offline 5min, 2-Offline 1hour)
                          или None, если статус недоступен
        """
        try:
            return obj.availability.status
        except AttributeError:
            return None

    def get_last_answer(self, obj) -> str:
        """
        Возвращает время последнего ответа номенклатуры.

        Аргументы:
            obj (Nomenclature): Объект номенклатуры

        Возвращает:
            str: Время в формате 'YYYY-MM-DD HH:MM:SS' или 'Не выходила в сеть'
        """
        try:
            return format_local_datetime(obj.availability.last_answer_date)
        except AttributeError:
            return "Не выходила в сеть"

    def get_exterior(self, obj):
        """
        Возвращает список фотографий экстерьера.

        Аргументы:
            obj (Nomenclature): Объект номенклатуры

        Возвращает:
            list: Список сериализованных фото экстерьера
        """
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="exterior"), many=True
        ).data

    def get_interior(self, obj):
        """
        Возвращает список фотографий интерьера.

        Аргументы:
            obj (Nomenclature): Объект номенклатуры

        Возвращает:
            list: Список сериализованных фото интерьера
        """
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="interior"), many=True
        ).data

    def get_formattedAddress(self, obj):
        """
        Возвращает отформатированный адрес с координатами.

        Аргументы:
            obj (Nomenclature): Объект номенклатуры

        Возвращает:
            dict: {
                'name': str,  # отформатированный адрес
                'coordinates': {'latitude': str, 'longitude': str}
            }
        """
        try:
            nomenclature_address = obj.address
        except ObjectDoesNotExist:
            return {"name": "", "coordinates": {"latitude": None, "longitude": None}}

        if not nomenclature_address or not nomenclature_address.address:
            return {"name": "", "coordinates": {"latitude": None, "longitude": None}}

        address = nomenclature_address.address
        if not address:
            return {"name": "", "coordinates": {"latitude": None, "longitude": None}}

        address_parts = []
        if address.city and address.city.name:
            address_parts.append(f"г. {address.city.name}")
        if address.street and address.street.name:
            address_parts.append(f"ул. {address.street.name}")

        house_number = None
        if address.house and address.house.number:
            house_number = address.house.number
        elif address.building and address.building.number:
            house_number = address.building.number
        if house_number:
            address_parts.append(house_number)

        latitude = None
        longitude = None
        if hasattr(address, 'coordinates') and address.coordinates:
            try:
                if hasattr(address.coordinates, 'latitude'):
                    latitude = str(address.coordinates.latitude) if address.coordinates.latitude else None
                if hasattr(address.coordinates, 'longitude'):
                    longitude = str(address.coordinates.longitude) if address.coordinates.longitude else None
            except (AttributeError, TypeError):
                pass

        return {
            "name": ', '.join(address_parts),
            "coordinates": {"latitude": latitude, "longitude": longitude}
        }

    # ═════════════════════════════════════════════════════════════════════════
    # ВАЛИДАЦИЯ
    # ═════════════════════════════════════════════════════════════════════════

    def validate_settings(self, value: Dict[str, Any]) -> Dict[str, Any]:
        """
        Валидация настроек вещания.

        Проверяет:
        1. Наличие обязательных ключей 'worktime' и 'default_volume' для каждого дня
        2. Корректность формата времени (HH:MM-HH:MM)
        3. Корректность громкости (0-100, ровно 4 значения)
        4. Отсутствие пересечений в custom_volume

        Аргументы:
            value (dict): Настройки для каждого дня недели
                Формат: {
                    'mon': {'worktime': '09:00-18:00', 'default_volume': [50, 50, 50, 50]},
                    'tue': {'worktime': '09:00-18:00', 'default_volume': [50, 50, 50, 50]},
                    ...
                }

        Возвращает:
            dict: Валидные настройки

        Исключения:
            ValidationError: При любой ошибке валидации
        """
        def _translate_error(err):
            """Переводит стандартную ошибку времени в человеко-читаемый вид."""
            time_val = str()
            e_list = str(err).split()
            match e_list[0]:
                case "second":
                    time_val = "секунд"
                case "minute":
                    time_val = "минут"
                case "hour":
                    time_val = "часов"
            raise serializers.ValidationError(
                f"Количество {time_val} должно быть в пределах {e_list[-1]}"
            )

        def _validate_time(interval: str) -> None:
            """
            Валидация интервала времени.

            Аргументы:
                interval (str): Интервал в формате 'HH:MM-HH:MM'

            Исключения:
                ValidationError: Если формат неверный или время некорректно
            """
            if not isinstance(interval, str):
                raise serializers.ValidationError("Интервал времени имеет не правильный формат!")
            split_interval = interval.split("-")
            if len(split_interval) != 2:
                raise serializers.ValidationError("Интервал времени должен содержать ровно два значения!")
            start = list(map(int, split_interval[0].split(":")))
            end = list(map(int, split_interval[1].split(":")))
            try:
                start_time = time(*start)
                end_time = time(*end)
            except ValueError as e:
                if "must be" in str(e):
                    _translate_error(e)
                else:
                    raise e
            if not time(0, 0, 0) <= start_time < end_time <= time(23, 59, 59):
                raise serializers.ValidationError(
                    "Время начала не может быть больше времени окончания "
                    "и должно быть в промежутке 00:00:00 - 23:59:59"
                )

        def _validate_volume(volume: tuple) -> None:
            """
            Валидация громкости.

            Аргументы:
                volume (tuple): Кортеж из 4 значений громкости

            Исключения:
                ValidationError: Если не 4 значения или вне диапазона 0-100
            """
            length = 4
            if len(volume) != length:
                raise serializers.ValidationError(f"Значений громкости должно быть ровно {length}")
            if not all(isinstance(vol, int) for vol in volume):
                raise serializers.ValidationError("Громкость должна передаваться целочисленным значением")
            if not all(0 <= vol <= 100 for vol in volume):
                raise serializers.ValidationError("Громкость может быть только от 0 до 100")

        def _validate_collision(custom_settings: dict) -> None:
            """
            Валидация пересечений временных отрезков в custom_volume.

            Аргументы:
                custom_settings (dict): Настройки пользовательской громкости

            Исключения:
                ValidationError: Если есть пересечения
            """
            sorted_settings = sorted(custom_settings)
            for curr, next_ in zip(sorted_settings, sorted_settings[1:]):
                split_curr = curr.split("-")
                end_curr = list(map(int, split_curr[1].split(":")))
                split_next = next_.split("-")
                start_next = list(map(int, split_next[0].split(":")))
                if time(*end_curr) > time(*start_next):
                    raise serializers.ValidationError(
                        "Обнаружено пересечение в часах пользовательских настроек громкости"
                    )

        for day, settings in value.items():
            # Проверка обязательных ключей
            try:
                req_keys = {
                    "worktime": settings["worktime"],
                    "default_volume": tuple(settings["default_volume"]),
                }
            except KeyError as ke:
                raise serializers.ValidationError(f"{ke} не передан")
            except TypeError:
                raise serializers.ValidationError(
                    "Список значений громкости имеет не правильный формат"
                )

            _validate_time(req_keys["worktime"])
            _validate_volume(req_keys["default_volume"])

            if "custom_volume" in settings:
                for interval, volume in settings["custom_volume"].items():
                    _validate_time(interval)
                    _validate_volume(tuple(volume))
                _validate_collision(settings["custom_volume"])

        return value

    # ═════════════════════════════════════════════════════════════════════════
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ДЛЯ ОПТИМИЗАЦИИ PATCH
    # ═════════════════════════════════════════════════════════════════════════

    def _get_current_values(self, instance: Nomenclature) -> Dict[str, Any]:
        """
        Получает текущие значения всех полей из экземпляра модели.

        Используется для сравнения с новыми значениями при PATCH запросах.

        Аргументы:
            instance (Nomenclature): Объект номенклатуры

        Возвращает:
            dict: Словарь с текущими значениями полей
                {
                    'name': str,
                    'description': str,
                    'timezone': str,
                    'settings': dict,
                    'code1c': str,
                    'contentType': str,
                    'typeOfPlace': UUID,
                    'pricePerMonth': Decimal,
                    'brand': UUID,
                    'legalEntity': UUID,
                    'responsible_radio': UUID,
                    'responsible_ad': UUID,
                    'responsible_technic': UUID,
                    'responsible_technic_on_address': UUID,
                    'responsible_placement_marketing': UUID,
                }
        """
        return {
            'name': instance.name,
            'description': instance.description,
            'timezone': instance.timezone,
            'settings': instance.settings,
            'code1c': instance.code1c,
            'contentType': instance.contentType,
            'typeOfPlace': instance.typeOfPlace_id,
            'pricePerMonth': instance.pricePerMonth,
            'brand': instance.brand_id,
            'legalEntity': instance.legalEntity_id,
            'responsible_radio': instance.responsible_radio_id,
            'responsible_ad': instance.responsible_ad_id,
            'responsible_technic': instance.responsible_technic_id,
            'responsible_technic_on_address': instance.responsible_technic_on_address_id,
            'responsible_placement_marketing': instance.responsible_placement_marketing_id,
        }

    def _has_field_changed(
        self,
        instance: Nomenclature,
        field_name: str,
        new_value: Any,
        current_values: Dict[str, Any]
    ) -> bool:
        """
        Проверяет, изменилось ли поле реально.

        Учитывает типы данных и сложные структуры (JSON, списки, FK).

        Аргументы:
            instance (Nomenclature): Объект номенклатуры
            field_name (str): Имя проверяемого поля
            new_value (Any): Новое значение (из validated_data)
            current_values (dict): Текущие значения полей

        Возвращает:
            bool: True если поле изменилось, False в противном случае
        """
        # Для write_only полей - отдельная логика
        if field_name in ['tenants_id', 'address_data']:
            return new_value is not None and new_value != []

        if field_name == 'address_id':
            old_value = current_values.get('address_id')
            return old_value != new_value

        # Для обычных полей
        old_value = current_values.get(field_name)

        # Оба None - не изменилось
        if old_value is None and new_value is None:
            return False

        # Для FK полей (brand, legalEntity, typeOfPlace)
        if field_name in ['brand', 'legalEntity', 'typeOfPlace']:
            if hasattr(new_value, 'id'):
                new_value = new_value.id
            return old_value != new_value

        # JSON поля (settings, hw_info)
        if isinstance(old_value, dict) and isinstance(new_value, dict):
            return json.dumps(old_value, sort_keys=True) != json.dumps(new_value, sort_keys=True)

        # Списки (media)
        if isinstance(old_value, list) and isinstance(new_value, list):
            if old_value and new_value and all(
                isinstance(x, (str, UUID)) for x in old_value + new_value
            ):
                return set(old_value) != set(new_value)
            return old_value != new_value

        return old_value != new_value

    def _update_tenants(self, instance: Nomenclature, tenants_data: Optional[List[Dict]]) -> None:
        """
        Обновление арендаторов номенклатуры.

        Выполняет полную замену: удаляет всех старых арендаторов и создает новых.
        Использует bulk_create для оптимизации производительности.

        Аргументы:
            instance (Nomenclature): Объект номенклатуры
            tenants_data (list): Список данных арендаторов или None/[] для удаления всех

        Возвращает:
            None

        Исключения:
            ValidationError: Если арендатор не найден или данные некорректны
        """
        if tenants_data is None or tenants_data == []:
            NomenclatureTenant.objects.filter(nomenclature=instance).delete()
            return

        new_rows = []
        seen_keys = set()

        for tenant_data in tenants_data:
            tenant_id = tenant_data.get('id')
            floor = tenant_data.get('floor', '')
            brand_obj = tenant_data.get('brand')
            atm = tenant_data.get('atm', False)

            if not tenant_id:
                continue

            try:
                counterparty = Counterparty.objects.get(id=tenant_id)
            except Counterparty.DoesNotExist:
                continue

            unique_key = (
                str(counterparty.id),
                str(brand_obj.id) if brand_obj else None,
                floor,
                atm,
            )

            if unique_key in seen_keys:
                continue
            seen_keys.add(unique_key)

            new_rows.append(
                NomenclatureTenant(
                    nomenclature=instance,
                    tenant=counterparty,
                    floor=floor,
                    brand=brand_obj,
                    atm=atm,
                )
            )

        with transaction.atomic():
            NomenclatureTenant.objects.filter(nomenclature=instance).delete()
            if new_rows:
                NomenclatureTenant.objects.bulk_create(new_rows, batch_size=100)

    def _update_address(self, instance: Nomenclature, address_data: Optional[Dict]) -> None:
        """
        Обновление адреса номенклатуры по данным.

        Аргументы:
            instance (Nomenclature): Объект номенклатуры
            address_data (dict): Данные для создания адреса

        Возвращает:
            None

        Исключения:
            ValidationError: Если данные адреса некорректны
        """
        if address_data and isinstance(address_data, dict):
            address_serializer = AddressCreateSerializer(data=address_data)
            address_serializer.is_valid(raise_exception=True)
            address_obj = address_serializer.save()
            NomenclatureAddress.objects.update_or_create(
                nomenclature=instance,
                defaults={"address": address_obj}
            )

    def _update_address_by_id(self, instance: Nomenclature, address_id: Optional[UUID]) -> None:
        """
        Обновление адреса номенклатуры по ID существующего адреса.

        Аргументы:
            instance (Nomenclature): Объект номенклатуры
            address_id (UUID): ID адреса из справочника

        Возвращает:
            None

        Исключения:
            ValidationError: Если адрес с таким ID не найден
        """
        if address_id:
            try:
                address_obj = AddressBook.objects.get(id=address_id)
                NomenclatureAddress.objects.update_or_create(
                    nomenclature=instance,
                    defaults={"address": address_obj}
                )
            except AddressBook.DoesNotExist:
                raise serializers.ValidationError({
                    "address_id": "Адрес с таким ID не найден"
                })

    # ═════════════════════════════════════════════════════════════════════════
    # СОЗДАНИЕ (POST)
    # ═════════════════════════════════════════════════════════════════════════

    @transaction.atomic
    def create(self, validated_data: Dict[str, Any]) -> Nomenclature:
        """
        Создание номенклатуры с атомарной транзакцией.

        Обрабатывает все связи: brand, legalEntity, typeOfPlace, address, tenants.
        При ошибке любого шага все изменения откатываются.

        АРГУМЕНТЫ:
            validated_data (dict): Валидные данные для создания
                - name (str): Название (обязательно)
                - code1c (str): Код из 1С (опционально, должен быть уникальным)
                - pricePerMonth (Decimal): Стоимость (опционально, >= 0)
                - brand_id (UUID): ID бренда (опционально)
                - legalEntity_id (UUID): ID юр. лица (опционально)
                - typeOfPlace_id (UUID): ID типа места (опционально)
                - tenants_id (list): Список арендаторов (опционально)
                - address_data (dict): Данные для создания адреса (опционально)
                - address_id (UUID): ID существующего адреса (опционально)
                - и другие поля модели

        ВОЗВРАЩАЕТ:
            Nomenclature: Созданный объект

        ИСКЛЮЧЕНИЯ:
            ValidationError: При любой ошибке валидации или создания
                - code1c: Если такой код уже существует
                - pricePerMonth: Если значение < 0
                - brand_id: Если бренд не найден
                - legalEntity_id: Если юр. лицо не найдено
                - typeOfPlace_id: Если тип места не найден
                - address_id: Если адрес не найден
                - tenants_id: Если арендатор не найден
        """
        # Извлечение вложенных данных
        address_data = None
        address_id = None

        if "address_data" in validated_data:
            address_data = validated_data.pop("address_data")
        elif "address_id" in validated_data:
            address_id = validated_data.pop("address_id")
        elif "address" in validated_data:
            address_relation = validated_data.pop("address", {})
            address_data = address_relation.get("address") if address_relation else None

        tenants_id = validated_data.pop("tenants_id", [])
        brand_id = validated_data.pop("brand_id", None)
        legalEntity_id = validated_data.pop("legalEntity_id", None)
        typeOfPlace_id = validated_data.pop("typeOfPlace_id", None)

        # Проверка уникальности code1c
        code1c = validated_data.get("code1c")
        if code1c:
            old_item = Nomenclature.objects.filter(code1c=code1c).first()
            if old_item:
                log_path = "/app/network_logs/nomenclature_conflicts.log"
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(f"{validated_data.get('name', '')}: {old_item.id}, {getattr(old_item, 'code1c', '—')}\n")
                except Exception:
                    pass
                raise serializers.ValidationError({
                    "code1c": f"Номенклатура с кодом '{code1c}' уже существует (id={old_item.id})"
                })

        # Проверка pricePerMonth
        price_per_month = validated_data.get("pricePerMonth")
        if price_per_month is not None:
            try:
                if price_per_month < 0:
                    raise serializers.ValidationError({
                        "pricePerMonth": "Стоимость аренды не может быть меньше 0."
                    })
            except TypeError:
                raise serializers.ValidationError({
                    "pricePerMonth": "Стоимость аренды должна быть числом."
                })

        # Создание номенклатуры
        try:
            nomenclature = Nomenclature.objects.create(**validated_data)
        except Exception as e:
            raise serializers.ValidationError({
                "non_field_errors": f"Ошибка при создании номенклатуры: {str(e)}"
            })

        # Обработка brand
        if brand_id:
            try:
                brand = Brand.objects.get(id=brand_id)
                nomenclature.brand = brand
                nomenclature.save(update_fields=['brand'])
            except Brand.DoesNotExist:
                nomenclature.delete()
                raise serializers.ValidationError({
                    "brand_id": "Бренд с таким ID не найден"
                })
            except Exception as e:
                nomenclature.delete()
                raise serializers.ValidationError({
                    "brand_id": f"Ошибка при установке бренда: {str(e)}"
                })

        # Обработка legalEntity
        if legalEntity_id:
            try:
                legal_entity = Counterparty.objects.get(id=legalEntity_id)
                nomenclature.legalEntity = legal_entity
                nomenclature.save(update_fields=['legalEntity'])
            except Counterparty.DoesNotExist:
                nomenclature.delete()
                raise serializers.ValidationError({
                    "legalEntity_id": "Юр. лицо с таким ID не найдено"
                })
            except Exception as e:
                nomenclature.delete()
                raise serializers.ValidationError({
                    "legalEntity_id": f"Ошибка при установке юр. лица: {str(e)}"
                })

        # Обработка typeOfPlace
        if typeOfPlace_id:
            try:
                type_of_place = TypeOfPlace.objects.get(id=typeOfPlace_id)
                nomenclature.typeOfPlace = type_of_place
                nomenclature.save(update_fields=['typeOfPlace'])
            except TypeOfPlace.DoesNotExist:
                nomenclature.delete()
                raise serializers.ValidationError({
                    "typeOfPlace_id": "Тип места с таким ID не найден"
                })
            except Exception as e:
                nomenclature.delete()
                raise serializers.ValidationError({
                    "typeOfPlace_id": f"Ошибка при установке типа места: {str(e)}"
                })

        # Обработка адреса
        if address_id is not None:
            try:
                address_obj = AddressBook.objects.get(id=address_id)
                NomenclatureAddress.objects.create(
                    nomenclature=nomenclature,
                    address=address_obj
                )
            except AddressBook.DoesNotExist:
                raise serializers.ValidationError({
                    "address_id": "Адрес с таким ID не найден"
                })

        elif address_data is not None and address_data != {}:
            if isinstance(address_data, dict):
                try:
                    address_serializer = AddressCreateSerializer(data=address_data)
                    address_serializer.is_valid(raise_exception=True)
                    address_obj = address_serializer.save()
                    NomenclatureAddress.objects.create(
                        nomenclature=nomenclature,
                        address=address_obj
                    )
                except Exception as e:
                    raise serializers.ValidationError({
                        "address_data": f"Ошибка при создании адреса: {str(e)}"
                    })
            elif isinstance(address_data, AddressBook):
                NomenclatureAddress.objects.create(
                    nomenclature=nomenclature,
                    address=address_data
                )

        # Обработка арендаторов
        if tenants_id:
            try:
                self._update_tenants(nomenclature, tenants_id)
            except Exception as e:
                nomenclature.delete()
                raise serializers.ValidationError({
                    "tenants_id": f"Ошибка при добавлении арендаторов: {str(e)}"
                })

        return nomenclature

    # ═════════════════════════════════════════════════════════════════════════
    # ОБНОВЛЕНИЕ (PATCH) - ОПТИМИЗИРОВАННОЕ
    # ═════════════════════════════════════════════════════════════════════════

    @transaction.atomic
    def update(self, instance: Nomenclature, validated_data: Dict[str, Any]) -> Nomenclature:
        """
        Частичное обновление номенклатуры с оптимизацией.

        Особенности:
        1. Определяет реально измененные поля (сравнивает с текущими значениями)
        2. Обрабатывает только измененные поля
        3. Тяжелые операции (tenants) выполняются только при реальном изменении
        4. Атомарная транзакция - при ошибке все откатывается

        АРГУМЕНТЫ:
            instance (Nomenclature): Объект для обновления
            validated_data (dict): Валидные данные для обновления
                - Может содержать любое подмножество полей модели
                - Для write_only полей: tenants_id, address_data, address_id
                - Для FK полей: brand, legalEntity, typeOfPlace

        ВОЗВРАЩАЕТ:
            Nomenclature: Обновленный объект

        АЛГОРИТМ:
            1. Получение текущих значений из instance
            2. Определение реально измененных полей
            3. Если ничего не изменилось - возврат instance
            4. Обработка сложных полей (tenants, address)
            5. Обработка FK полей (brand, legalEntity, typeOfPlace)
            6. Обработка простых полей
            7. Валидация измененных полей (code1c, pricePerMonth)
            8. Сохранение только измененных полей (update_fields)
        """
        # 1. Получение текущих значений
        current_values = self._get_current_values(instance)

        # 2. Определение реально измененных полей
        changed_fields = set()
        for field, new_value in validated_data.items():
            if self._has_field_changed(instance, field, new_value, current_values):
                changed_fields.add(field)

        # 3. Если ничего не изменилось - возвращаем instance
        if not changed_fields:
            return instance

        # 4. Обработка сложных полей (только если изменились)

        # --- ОБРАБОТКА TENANTS ---
        if "tenants_id" in changed_fields:
            tenants_id = validated_data.pop("tenants_id", None)
            self._update_tenants(instance, tenants_id)

        # --- ОБРАБОТКА ADDRESS ---
        # address_data и address_id имеют одинаковый source="address.address",
        # поэтому DRF кладёт итоговое значение в validated_data под вложенным
        # ключом "address", а не "address_data"/"address_id". Обрабатываем оба
        # варианта плюс фолбэк на реальный ключ "address" (как в create()).
        if "address_data" in changed_fields:
            address_data = validated_data.pop("address_data", None)
            self._update_address(instance, address_data)
        elif "address_id" in changed_fields:
            address_id = validated_data.pop("address_id", None)
            self._update_address_by_id(instance, address_id)
        elif "address" in changed_fields:
            address_relation = validated_data.pop("address", {})
            nested_value = address_relation.get("address") if address_relation else None
            if isinstance(nested_value, dict):
                self._update_address(instance, nested_value)
            elif nested_value is not None:
                self._update_address_by_id(instance, nested_value)

        # 5. Обработка FK полей (только если изменились)
        fields_to_update = []

        if "brand" in changed_fields:
            brand_value = validated_data.pop("brand", None)
            if hasattr(brand_value, 'id'):
                brand_value = brand_value.id
            instance.brand_id = brand_value
            fields_to_update.append("brand")

        if "legalEntity" in changed_fields:
            legal_entity_value = validated_data.pop("legalEntity", None)
            if hasattr(legal_entity_value, 'id'):
                legal_entity_value = legal_entity_value.id
            instance.legalEntity_id = legal_entity_value
            fields_to_update.append("legalEntity")

        if "typeOfPlace" in changed_fields:
            type_of_place_value = validated_data.pop("typeOfPlace", None)
            if hasattr(type_of_place_value, 'id'):
                type_of_place_value = type_of_place_value.id
            instance.typeOfPlace_id = type_of_place_value
            fields_to_update.append("typeOfPlace")

        # 6. Обработка простых полей
        simple_fields = {
            'name', 'description', 'is_active', 'id_rasb', 'timezone', 'settings',
            'code1c', 'contentType', 'pricePerMonth',
            'responsible_radio', 'responsible_ad',
            'responsible_technic', 'responsible_technic_on_address',
            'responsible_placement_marketing',
            'worktime_start', 'worktime_end',
        }

        for field in simple_fields:
            if field in changed_fields and field in validated_data:
                setattr(instance, field, validated_data[field])
                fields_to_update.append(field)

        # 7. Валидация (только для измененных полей)

        # Проверка code1c
        if 'code1c' in changed_fields:
            code1c = validated_data.get('code1c')
            if code1c:
                conflict = (
                    Nomenclature.objects
                    .filter(code1c=code1c)
                    .exclude(id=instance.id)
                    .first()
                )
                if conflict:
                    raise serializers.ValidationError({
                        "code1c": f"Код '{code1c}' уже используется в другой номенклатуре (id={conflict.id})"
                    })

        # Проверка pricePerMonth
        if 'pricePerMonth' in changed_fields:
            price_per_month = validated_data.get('pricePerMonth')
            if price_per_month is not None:
                try:
                    if price_per_month < 0:
                        raise serializers.ValidationError({
                            "pricePerMonth": "Стоимость аренды не может быть меньше 0."
                        })
                except TypeError:
                    raise serializers.ValidationError({
                        "pricePerMonth": "Стоимость аренды должна быть числом."
                    })

        # 8. Сохранение только измененных полей
        if fields_to_update:
            instance.save(update_fields=fields_to_update)
        else:
            instance.save()

        return instance

    # ═════════════════════════════════════════════════════════════════════════
    # ПРЕДСТАВЛЕНИЕ (to_representation)
    # ═════════════════════════════════════════════════════════════════════════

    def _user_id_name(self, user):
        """
        Возвращает информацию о пользователе для ответа.

        Аргументы:
            user (CustomUser): Объект пользователя

        Возвращает:
            dict: {
                'id': str,
                'full_name': str,
                'phone_number': list
            } или None, если пользователь отсутствует
        """
        if not user:
            return None

        basic_phones = list(
            user.contacts_cp
            .filter(type="phone", basic=True)
            .values_list("meaning", flat=True)
        )

        if not basic_phones and user.phone_number:
            basic_phones = [str(user.phone_number)]

        phones = [str(p) for p in basic_phones if p]

        return {
            "id": str(user.id),
            "full_name": user.first_name,
            "phone_number": phones,
        }

    def to_representation(self, instance: Nomenclature) -> Dict[str, Any]:
        """
        Формирует ответ для клиента.

        Группирует данные в логические блоки:
        - main_info: Основная информация (описание, владелец, статус и т.д.)
        - responsible: Ответственные лица
        - tenants_length: Количество арендаторов
        - broadcast: Флаг вещания

        Аргументы:
            instance (Nomenclature): Объект номенклатуры

        Возвращает:
            dict: Сериализованные данные
        """
        repr_ = super().to_representation(instance)

        # Основная информация
        repr_["main_info"] = {
            "description": instance.description,
            "owner": instance.owner.full_name,
            "timezone": TIMEZONES[instance.timezone],
            "status": self.get_status(instance),
            "last_answer": self.get_last_answer(instance),
            "version": instance.version,
            "created": f"{instance.created:%Y-%m-%d %H:%M:%S}",
        }

        # Ответственные лица
        repr_["responsible"] = {
            "ad": self._user_id_name(instance.responsible_ad),
            "radio": self._user_id_name(instance.responsible_radio),
            "technic": self._user_id_name(instance.responsible_technic),
            "technic_on_address": self._user_id_name(instance.responsible_technic_on_address),
            "placement_marketing": self._user_id_name(instance.responsible_placement_marketing),
        }

        # Дополнительные поля
        repr_["tenants_length"] = instance.tenants.count()
        repr_["broadcast"] = getattr(instance.legalEntity, "broadcast", None)

        # Удаление дублирующихся полей из main_info
        fields_to_remove = []
        for field in repr_["main_info"]:
            if field in repr_:
                fields_to_remove.append(field)
        for field in fields_to_remove:
            repr_.pop(field)

        # Удаление полей ответственных (уже в группе responsible)
        fields_to_remove = [
            "responsible_ad", "responsible_radio", "responsible_technic",
            "responsible_technic_on_address", "responsible_placement_marketing",
        ]
        for field in fields_to_remove:
            repr_.pop(field, None)

        # Обработка настроек (приведение к нужному формату)
        if "settings" in repr_ and repr_["settings"]:
            for day, setting in list(repr_["settings"].items()):
                repr_["settings"][day] = {
                    "worktime": setting["worktime"],
                    "default_volume": setting["default_volume"],
                    "custom_volume": setting.get("custom_volume", {}),
                }

        # Удаление поля address (уже есть в основном ответе)
        if "address" in repr_:
            repr_.pop("address")

        # Преобразование contentType в человеко-читаемый вид
        if "contentType" in repr_:
            key = repr_["contentType"]
            repr_["contentType"] = AVAILABLE_CONTENT_TYPES.get(key, key)

        return repr_
