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

    nameForFront = serializers.CharField(source="name_for_front", read_only=True)
    typeOfPlace = serializers.CharField(source='typeOfPlace.name', read_only=True)
    formattedAddress = serializers.SerializerMethodField()
    exterior = serializers.SerializerMethodField()
    brand = BrandListSerializer(read_only=True)

    class Meta:
        model = Nomenclature
        fields = [
            "id", "nameForFront", "formattedAddress",
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
            "id", "address", "oldCatalogSlug", "typeOfPlace", "address",
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


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка номенклатур."""

    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
    brand = BrandListSerializer()
    legalEntity = CounterpartiesShortSerializer()
    exterior = serializers.SerializerMethodField()
    formattedAddress = serializers.CharField(source="formatted_address", read_only=True)
    nameForFront = serializers.CharField(source="name_for_front", read_only=True)
    oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)

    class Meta:
        model = Nomenclature
        fields = (
            "id", "name", "nameForFront", "legalEntity", "brand",
            "exterior", "formattedAddress", "typeOfPlace",
            "pricePerMonth", "code1c", "oldCatalogSlug",
        )
        extra_fields = ("nameForFront", "formattedAddress", "oldCatalogSlug")
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
    nameForFront = serializers.CharField(source="name_for_front", read_only=True)
    slotsPerHour = serializers.CharField(source="slots_per_hour", read_only=True)
    oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)

    class Meta:
        model = Nomenclature
        fields = (
            "id", "nameForFront", "brand", "exterior",
            "formattedAddress", "typeOfPlace", "pricePerMonth",
            "slotsPerHour", "oldCatalogSlug"
        )
        read_only_fields = fields

    def get_exterior(self, obj):
        """Возвращает первое фото экстерьера."""
        image = obj.images.filter(type="exterior").first()
        if not image:
            return []
        return InNomenclaturePhotoSerializer([image], many=True).data

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


class NomenclatureShortSerializer(serializers.ModelSerializer):
    """Упрощенный сериализатор для номенклатур."""

    nameForFront = serializers.SerializerMethodField()
    formattedAddress = serializers.SerializerMethodField()
    exterior = serializers.SerializerMethodField()
    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)

    class Meta:
        model = Nomenclature
        fields = [
            "id", "nameForFront", "formattedAddress",
            "exterior", "typeOfPlace", "pricePerMonth"
        ]

    def get_nameForFront(self, obj):
        """Формирует название для фронтенда."""
        parts = []
        if obj.typeOfPlace:
            parts.append(obj.typeOfPlace.name)
        if obj.brand:
            parts.append(obj.brand.name)
        if obj.address and obj.address.address:
            addr = obj.address.address
            address_parts = []
            if addr.city:
                address_parts.append(f"г. {addr.city.name}")
            if addr.street:
                address_parts.append(f"ул. {addr.street.name}")
            if addr.house:
                address_parts.append(addr.house.number)
            if address_parts:
                parts.append(", ".join(address_parts))
        return " | ".join(filter(None, parts)) or None

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
        - nameForFront: Сгенерированное название для фронтенда
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
    nameForFront = serializers.CharField(source="name_for_front", read_only=True)
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
        extra_fields = ("nameForFront",)
        read_only_fields = (
            "id", "owner", "hw_info", "version", "created",
            "status", "last_answer", "interior", "exterior",
            "nameForFront", "typeOfPlace", "formattedAddress",
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
        if "address_data" in changed_fields:
            address_data = validated_data.pop("address_data", None)
            self._update_address(instance, address_data)

        if "address_id" in changed_fields:
            address_id = validated_data.pop("address_id", None)
            self._update_address_by_id(instance, address_id)

        # 5. Обработка FK полей (только если изменились)
        if "brand" in changed_fields:
            brand_value = validated_data.pop("brand", None)
            if hasattr(brand_value, 'id'):
                brand_value = brand_value.id
            instance.brand_id = brand_value

        if "legalEntity" in changed_fields:
            legal_entity_value = validated_data.pop("legalEntity", None)
            if hasattr(legal_entity_value, 'id'):
                legal_entity_value = legal_entity_value.id
            instance.legalEntity_id = legal_entity_value

        if "typeOfPlace" in changed_fields:
            type_of_place_value = validated_data.pop("typeOfPlace", None)
            if hasattr(type_of_place_value, 'id'):
                type_of_place_value = type_of_place_value.id
            instance.typeOfPlace_id = type_of_place_value

        # 6. Обработка простых полей
        simple_fields = {
            'name', 'description', 'is_active', 'id_rasb', 'timezone', 'settings',
            'code1c', 'contentType', 'pricePerMonth',
            'responsible_radio', 'responsible_ad',
            'responsible_technic', 'responsible_technic_on_address',
            'responsible_placement_marketing'
        }

        fields_to_update = []
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

# import hashlib
# from datetime import time
# from django.core.exceptions import ObjectDoesNotExist
# from django.utils import timezone
# from rest_framework import serializers
# from brands.models import Brand
# from brands.serializers import BrandListSerializer, BrandCardSerializer
# from counterparties.models import Counterparty
# from counterparties.serializers import CounterpartiesShortSerializer
# from files.serializers import Base64FileField
# from nomenclatures.models import (
#     Nomenclature,
#     StatusHistory,
#     TIMEZONES,
#     NomenclatureImage,
#     NomenclatureAddress,
#     AVAILABLE_CONTENT_TYPES,
#     TypeOfPlace,
#     NomenclatureTenant, DiscountRule,
# )
# from addresses.models import Address as AddressBook
# from addresses.serializers import AddressCreateSerializer, AddressReadSerializer, AddressWebResultSerializer
# from api.base_objects import Article

# serializers.ModelSerializer.serializer_field_mapping[Article] = serializers.IntegerField



# serializers.ModelSerializer.serializer_field_mapping[Article] = serializers.IntegerField

# ALLOWED_FORMATS = ("jpg", "jpeg", "png", "webp")



# def format_local_datetime(value):
#     if timezone.is_naive(value):
#         value = timezone.make_aware(value, timezone.get_default_timezone())
#     return f"{timezone.localtime(value):%Y-%m-%d %H:%M:%S}"

# # class TenantShortSerializer(serializers.ModelSerializer):
# #     class Meta:
# #         model = Counterparty
# #         fields = (
# #             'id',
# #             'first_name',
# #             'last_name',
# #             'additional_name',
# #             'keyword',
# #         )

# class DiscountRuleSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DiscountRule
#         fields = ["id", "days_from", "days_to", "coefficient"]


# class PhotoSerializer(serializers.ModelSerializer):
#     source = Base64FileField()

#     class Meta:
#         model = NomenclatureImage
#         fields = ("id", "source", "type", "created")
#         read_only_fields = ("id", "created")

#     def validate_source(self, file):
#         ext = file.name.split(".")[-1].lower()
#         if ext not in ALLOWED_FORMATS:
#             raise serializers.ValidationError(
#                 f"Недопустимый формат файла. Разрешены: {', '.join(ALLOWED_FORMATS)}"
#             )

#         # Проверка размера (пример 15MB)
#         if file.size > 15 * 1024 * 1024:
#             raise serializers.ValidationError("Максимальный размер файла 15MB")

#         return file

#     def validate(self, attrs):
#         nomenclature = self.context.get("nomenclature")
#         if not nomenclature:
#             raise serializers.ValidationError("Номенклатура не передана")

#         # вычисляем md5 хэш для файла
#         file_data = attrs["source"].read()
#         file_hash = hashlib.md5(file_data).hexdigest()
#         attrs["source"].seek(0)  # обязательно вернуть курсор

#         # проверка дубликата по содержимому
#         if NomenclatureImage.objects.filter(nomenclature=nomenclature, hash=file_hash).exists():
#             raise serializers.ValidationError("Эта фотография уже прикреплена к номенклатуре")

#         return attrs

#     def create(self, validated_data):
#         validated_data["nomenclature"] = self.context["nomenclature"]
#         return super().create(validated_data)


# class InNomenclaturePhotoSerializer(serializers.ModelSerializer):
#     """Схема для добавления фотографий к номенклатурам."""

#     class Meta:
#         model = NomenclatureImage

#         fields = ("source", "id",)
#         read_only_fields = ("source", "id",)

# class TypeOfPlaceWebSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TypeOfPlace
#         fields = (
#             "name",
#             "abbreviation"
#         )
#         read_only_fields = fields

# class NomenclatureWebSerializer(serializers.ModelSerializer):
#     brand = BrandCardSerializer(read_only=True)
#     typeOfPlace = TypeOfPlaceWebSerializer(read_only=True)
#     legalEntity = CounterpartiesShortSerializer(read_only=True)
#     exterior = serializers.SerializerMethodField()
#     interior = serializers.SerializerMethodField()
#     contentType = serializers.ChoiceField(
#         choices=list(AVAILABLE_CONTENT_TYPES.keys()),
#         required=False,
#     )
#     worktime_start = serializers.TimeField(format='%H:%M', required=False, allow_null=True)
#     worktime_end = serializers.TimeField(format='%H:%M', required=False, allow_null=True)
#     oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)
#     address = AddressWebResultSerializer(source="address.address", read_only=True)
#     class Meta:
#         model = Nomenclature
#         fields = (
#             "id",
#             "address",
#             "oldCatalogSlug",
#             "typeOfPlace",
#             "address",
#             "worktime_start",
#             "worktime_end",
#             "oldCatalogSlug",
#             "address",
#             "legalEntity",
#             "exterior",
#             "interior",
#             "contentType",
#             "brand",
#             "description",
#             "possibility",
#             "pricePerMonth",
#             "external_video_media",
#             "external_audio_media",
#             "internal_video_media",
#             "internal_audio_media",
#             "responsible_ad",
#             "nomenclature_tenants"
#         )
#         read_only_fields = fields

#     def get_interior(self, obj):
#         return InNomenclaturePhotoSerializer(
#             obj.images.filter(type="interior"), many=True
#         ).data

#     def get_exterior(self, obj):
#         return InNomenclaturePhotoSerializer(
#             obj.images.filter(type="exterior"), many=True
#         ).data

#     def _user_id_name(self, user):
#         if not user:
#             return None

#         # Берём ВСЕ basic телефоны
#         basic_phones = list(
#             user.contacts_cp
#             .filter(type="phone", basic=True)
#             .values_list("meaning", flat=True)
#         )

#         # fallback — если basic нет, но есть phone_number в CustomUser
#         if not basic_phones and user.phone_number:
#             basic_phones = [str(user.phone_number)]

#         # гарантируем строки
#         phones = [str(p) for p in basic_phones if p]

#         return {
#             "id": str(user.id),
#             "full_name": user.first_name,
#             "phone_number": phones,
#         }

#     def to_representation(self, instance):
#         repr_ = super().to_representation(instance)
#         if "contentType" in repr_:
#             key = repr_["contentType"]
#             repr_["contentType"] = AVAILABLE_CONTENT_TYPES.get(key, key)
#         repr_["responsible"] = {
#             "ad": self._user_id_name(instance.responsible_ad),
#         }
#         repr_["tenants_length"] = instance.tenants.count()

#         fields_to_remove = [
#             "responsible_ad",
#             "nomenclature_tenants"
#         ]
#         for field in fields_to_remove:
#             repr_.pop(field, None)

#         return repr_


# class ShortBrandNomenclatureSerializer(serializers.ModelSerializer):
#     """Схема для отображения номенклатуры в списке."""
#     brand_name = serializers.CharField(source='brand.name', default='Без значения')
#     brand_id = serializers.CharField(source='brand.id', default=None)
#     brand_logotype = Base64FileField(source="brand.logotype", default=None)
#     type_of_place = serializers.CharField(source='typeOfPlace.name', default=None)
#     tenants_count = serializers.IntegerField(read_only=True)  # ← из annotate

#     class Meta:
#         model = Nomenclature
#         fields = (
#             "brand_name",
#             "brand_id",
#             "brand_logotype",
#             "type_of_place",
#             "tenants_count",
#         )
#         read_only_fields = fields


# class NomenclatureTenantResponseSerializer(serializers.ModelSerializer):
#     """Сериализатор для ответа с арендаторами номенклатуры"""
#     id = serializers.UUIDField(read_only=True)
#     tenant_id = serializers.SerializerMethodField()
#     brands_list = serializers.SerializerMethodField()
#     logotype = serializers.SerializerMethodField()
#     floor = serializers.CharField(read_only=True)
#     atm = serializers.BooleanField(read_only=True)
#     brand_id = serializers.SerializerMethodField()  # Для отладки
#     # brand = BrandSerializer(read_only=True)
#     # tenant = FullTenantsSerializer(read_only=True)

#     class Meta:
#         model = NomenclatureTenant
#         fields = ('id', 'brands_list', 'logotype', 'floor', 'atm', 'brand_id', 'tenant_id')

#     def get_brands_list(self, obj):
#         """Возвращаем имя бренда"""
#         if obj.brand:
#             return obj.brand.name
#         return f"Бренд не указан (tenant: {obj.tenant.id})"  # Временное сообщение

#     def get_logotype(self, obj):
#         """Возвращаем URL логотипа бренда"""
#         if obj.brand and obj.brand.logotype:
#             if hasattr(obj.brand.logotype, 'url'):
#                 return obj.brand.logotype.url
#             return str(obj.brand.logotype)
#         return None

#     def get_brand_id(self, obj):
#         """Возвращаем ID бренда для отладки"""
#         return str(obj.brand.id) if obj.brand else None

#     def get_tenant_id(self, obj):
#         return str(obj.tenant.id) if obj.tenant else None

# class NomenclatureSearchSerializer(serializers.ModelSerializer):
#     brand_name = serializers.SerializerMethodField()
#     type_of_place_name = serializers.SerializerMethodField()
#     legal_entity_name = serializers.SerializerMethodField()
#     responsible_ad_name = serializers.SerializerMethodField()
#     tenants_names = serializers.SerializerMethodField()

#     class Meta:
#         model = Nomenclature
#         fields = [
#             'id', 'name', 'code1c', 'contentType', 'version',
#             'brand_name', 'type_of_place_name',
#             'legal_entity_name', 'responsible_ad_name', 'tenants_names'
#         ]

#     def get_brand_name(self, obj):
#         return obj.brand.name if obj.brand else None

#     def get_type_of_place_name(self, obj):
#         return obj.typeOfPlace.name if obj.typeOfPlace else None

#     def get_legal_entity_name(self, obj):
#         if not obj.legalEntity:
#             return None
#         try:
#             le = obj.legalEntity
#             parts = []
#             if le.last_name:
#                 parts.append(str(le.last_name))
#             if le.first_name:
#                 parts.append(str(le.first_name))
#             if le.middle_name:
#                 parts.append(str(le.middle_name))
#             if le.additional_name:
#                 parts.append(f"({str(le.additional_name)})")
#             if le.keyword:
#                 parts.append(f"[{str(le.keyword)}]")
#             return ' '.join(parts) if parts else None
#         except:
#             return None

#     def get_responsible_ad_name(self, obj):
#         if not obj.responsible_ad:
#             return None
#         try:
#             return f"{obj.responsible_ad.last_name or ''} {obj.responsible_ad.first_name or ''}".strip() or None
#         except:
#             return None

#     def get_tenants_names(self, obj):
#         try:
#             result = []
#             for t in obj.tenants.all()[:3]:
#                 parts = []
#                 if t.last_name:
#                     parts.append(str(t.last_name))
#                 if t.first_name:
#                     parts.append(str(t.first_name))
#                 if t.middle_name:
#                     parts.append(str(t.middle_name))
#                 if t.additional_name:
#                     parts.append(f"({str(t.additional_name)})")
#                 if t.keyword:
#                     parts.append(f"[{str(t.keyword)}]")
#                 if parts:
#                     result.append(' '.join(parts))
#             return result
#         except:
#             return []

# class TenantWriteSerializer(serializers.Serializer):
#     id = serializers.UUIDField()
#     floor = serializers.CharField(required=False, allow_blank=True)
#     atm = serializers.BooleanField(required=False, default=False)
#     brand = serializers.PrimaryKeyRelatedField(
#         queryset=Brand.objects.all(),
#         write_only=True,
#         required=False,
#         allow_null=True,
#     )

#     def validate_id(self, value):
#         try:
#             Counterparty.objects.get(id=value)
#             return value
#         except Counterparty.DoesNotExist:
#             raise serializers.ValidationError(f"Арендатор с id {value} не найден")

# class TypeOfPlaceSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = TypeOfPlace
#         fields = "__all__"
#         read_only_fields = ("id",)

# # nomenclatures/serializers.py

# class CityNomenclaturesSerializer(serializers.ModelSerializer):
#     """
#     Сериализатор для номенклатуры в ответе по городу.
#     Скрывает детали, оставляет только фронтенд-дружелюбные поля.
#     """
#     nameForFront = serializers.CharField(
#         source="name_for_front",
#         read_only=True
#     )
#     typeOfPlace = serializers.CharField(
#         source='typeOfPlace.name',
#         read_only=True
#     )
#     formattedAddress = serializers.SerializerMethodField()
#     exterior = serializers.SerializerMethodField()
#     brand = BrandListSerializer(read_only=True)
#     class Meta:
#         model = Nomenclature
#         fields = [
#             "id",
#             "nameForFront",
#             "formattedAddress",
#             "pricePerMonth",
#             "exterior",
#             "brand",
#             "typeOfPlace"
#         ]
#     def get_exterior(self, obj):
#         return InNomenclaturePhotoSerializer(
#             obj.images.filter(type="exterior"), many=True
#         ).data

#     def get_formattedAddress(self, obj):
#         """Возвращает объект с отформатированным адресом и координатами"""
#         try:
#             # Пытаемся получить связанный объект NomenclatureAddress
#             nomenclature_address = obj.address
#         except ObjectDoesNotExist:
#             # Если связи нет, возвращаем пустой адрес
#             return {
#                 "name": "",
#                 "coordinates": {
#                     "latitude": None,
#                     "longitude": None
#                 }
#             }

#         # Если связь есть, но нет самого адреса
#         if not nomenclature_address or not nomenclature_address.address:
#             return {
#                 "name": "",
#                 "coordinates": {
#                     "latitude": None,
#                     "longitude": None
#                 }
#             }

#         address = nomenclature_address.address

#         if not address:
#             return {
#                 "name": "",
#                 "coordinates": {
#                     "latitude": None,
#                     "longitude": None
#                 }
#             }

#         # Формируем строку адреса
#         address_parts = []

#         # Город
#         if address.city and address.city.name:
#             address_parts.append(f"г. {address.city.name}")

#         # Улица
#         if address.street and address.street.name:
#             address_parts.append(f"ул. {address.street.name}")

#         # Номер дома/строения
#         house_number = None
#         if address.house and address.house.number:
#             house_number = address.house.number
#         elif address.building and address.building.number:
#             house_number = address.building.number

#         if house_number:
#             address_parts.append(house_number)

#         # 🔥 ИСПРАВЛЕНО: проверяем наличие coordinates и его атрибутов
#         latitude = None
#         longitude = None

#         if hasattr(address, 'coordinates') and address.coordinates:
#             try:
#                 if hasattr(address.coordinates, 'latitude'):
#                     latitude = str(address.coordinates.latitude) if address.coordinates.latitude else None
#                 if hasattr(address.coordinates, 'longitude'):
#                     longitude = str(address.coordinates.longitude) if address.coordinates.longitude else None
#             except (AttributeError, TypeError):
#                 # Если что-то пошло не так, оставляем None
#                 pass

#         # Формируем объект с адресом и координатами
#         return {
#             "name": ', '.join(address_parts),
#             "coordinates": {
#                 "latitude": latitude,
#                 "longitude": longitude
#             }
#         }

# class NomenclatureSerializer(serializers.ModelSerializer):
#     """Сериализация одной номенклатуры."""
#     typeOfPlace = serializers.CharField(
#         source='typeOfPlace.name',
#         read_only=True
#     )
#     typeOfPlace_id = serializers.PrimaryKeyRelatedField(
#         queryset=TypeOfPlace.objects.all(),
#         source="typeOfPlace",
#         write_only=True,
#         required=False,
#         allow_null=True,
#     )
#     nameForFront = serializers.CharField(source="name_for_front", read_only=True)
#     status = serializers.SerializerMethodField()
#     last_answer = serializers.SerializerMethodField()
#     legalEntity = CounterpartiesShortSerializer(read_only=True)
#     legalEntity_id = serializers.PrimaryKeyRelatedField(
#         queryset=Counterparty.objects.all(),
#         source="legalEntity",
#         write_only=True,
#         required=False,
#         allow_null=True,
#     )

#     # WRITE
#     tenants_id = TenantWriteSerializer(
#         many=True,
#         write_only=True,
#         required=False
#     )
#     brand = BrandListSerializer(read_only=True)  # чисто чтение
#     brand_id = serializers.PrimaryKeyRelatedField(
#         queryset=Brand.objects.all(),
#         source="brand",
#         write_only=True,
#         required=False,
#         allow_null=True,
#     )  # только запись по id
#     exterior = serializers.SerializerMethodField()
#     interior = serializers.SerializerMethodField()
#     code1c = serializers.CharField(required=False, allow_null=True, allow_blank=True)
#     contentType = serializers.ChoiceField(
#         choices=list(AVAILABLE_CONTENT_TYPES.keys()),
#         required=False,
#     )
#     article = serializers.IntegerField(read_only=True)
#     address_data = AddressCreateSerializer(
#         source="address.address", required=False, write_only=True
#     )
#     address_id = serializers.PrimaryKeyRelatedField(
#         queryset=AddressBook.objects.all(),
#         source="address.address",
#         write_only=True,
#         required=False,
#         allow_null=True,
#     )
#     address = AddressReadSerializer(source="address.address", read_only=True)
#     formattedAddress = serializers.SerializerMethodField()
#     worktime_start = serializers.TimeField(format='%H:%M', required=False, allow_null=True)
#     worktime_end = serializers.TimeField(format='%H:%M', required=False, allow_null=True)
#     oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)

#     class Meta:
#         fields = "__all__"
#         extra_fields = ("nameForFront",)
#         read_only_fields = (
#             "id",
#             "owner",
#             "hw_info",
#             "version",
#             "created",
#             "status",
#             "last_answer",
#             "legalEntity",
#             "brand",
#             "interior",
#             "exterior",
#             "nameForFront",
#             "typeOfPlace",
#             "formattedAddress",
#         )
#         model = Nomenclature

#     def get_formattedAddress(self, obj):
#         """Возвращает объект с отформатированным адресом и координатами"""
#         try:
#             # Пытаемся получить связанный объект NomenclatureAddress
#             nomenclature_address = obj.address
#         except ObjectDoesNotExist:
#             # Если связи нет, возвращаем пустой адрес
#             return {
#                 "name": "",
#                 "coordinates": {
#                     "latitude": None,
#                     "longitude": None
#                 }
#             }

#         # Если связь есть, но нет самого адреса
#         if not nomenclature_address or not nomenclature_address.address:
#             return {
#                 "name": "",
#                 "coordinates": {
#                     "latitude": None,
#                     "longitude": None
#                 }
#             }

#         address = nomenclature_address.address

#         if not address:
#             return {
#                 "name": "",
#                 "coordinates": {
#                     "latitude": None,
#                     "longitude": None
#                 }
#             }

#         # Формируем строку адреса
#         address_parts = []

#         # Город
#         if address.city and address.city.name:
#             address_parts.append(f"г. {address.city.name}")

#         # Улица
#         if address.street and address.street.name:
#             address_parts.append(f"ул. {address.street.name}")

#         # Номер дома/строения
#         house_number = None
#         if address.house and address.house.number:
#             house_number = address.house.number
#         elif address.building and address.building.number:
#             house_number = address.building.number

#         if house_number:
#             address_parts.append(house_number)

#         # 🔥 ИСПРАВЛЕНО: проверяем наличие coordinates и его атрибутов
#         latitude = None
#         longitude = None

#         if hasattr(address, 'coordinates') and address.coordinates:
#             try:
#                 if hasattr(address.coordinates, 'latitude'):
#                     latitude = str(address.coordinates.latitude) if address.coordinates.latitude else None
#                 if hasattr(address.coordinates, 'longitude'):
#                     longitude = str(address.coordinates.longitude) if address.coordinates.longitude else None
#             except (AttributeError, TypeError):
#                 # Если что-то пошло не так, оставляем None
#                 pass

#         # Формируем объект с адресом и координатами
#         return {
#             "name": ', '.join(address_parts),
#             "coordinates": {
#                 "latitude": latitude,
#                 "longitude": longitude
#             }
#         }

#     def validate_settings(self, value):
#         """
#         Валидация настроек.

#         Проверяется:
#         1. Наличие обязательных ключей worktime и default_volume
#         2. Корректность значений этих ключей
#         3. При наличии опциональных значений custom_volume - всё то же самое,
#             а также они дополнительно преверяются на пересечение
#         """

#         def _translate_error(err):
#             """Это нужно для перевода стандартной ошибки time"""
#             time_val = str()
#             e_list = str(err).split()
#             match e_list[0]:
#                 case "second":
#                     time_val = "секунд"
#                 case "minute":
#                     time_val = "минут"
#                 case "hour":
#                     time_val = "часов"
#             raise serializers.ValidationError(
#                 f"Количество {time_val} должно быть "
#                 f"в пределах {e_list[-1]}"
#             )

#         def _validate_time(interval: str) -> None:
#             """Валидация промежутков времени."""
#             if not isinstance(interval, str):
#                 raise serializers.ValidationError(
#                     "Интервал времени имеет не правильный формат!"
#                 )
#             split_interval = interval.split("-")
#             if len(split_interval) != 2:
#                 raise serializers.ValidationError(
#                     "Интервал времени должен содержать ровно два значения!"
#                 )
#             start = list(map(int, split_interval[0].split(":")))
#             end = list(map(int, split_interval[1].split(":")))
#             try:
#                 start_time = time(*start)
#                 end_time = time(*end)
#             except ValueError as e:
#                 if "must be" in str(e):
#                     _translate_error(e)
#                 else:
#                     raise e
#             if not time(0, 0, 0) <= start_time < end_time <= time(23, 59, 59):
#                 raise serializers.ValidationError(
#                     "Время начала не может быть больше времени окончания "
#                     "и должно быть в промежутке 00:00:00 - 23:59:59"
#                 )

#         def _validate_volume(volume: tuple) -> None:
#             """Валидация настроек громкости."""
#             length = 4
#             if len(volume) != length:
#                 raise serializers.ValidationError(
#                     f"Значений громкости должно быть ровно {length}"
#                 )
#             if not all(isinstance(vol, int) for vol in volume):
#                 raise serializers.ValidationError(
#                     "Громкость должна передаваться целочисленным значением"
#                 )
#             if not all(0 <= vol <= 100 for vol in volume):
#                 raise serializers.ValidationError(
#                     "Громкость может быть только от 0 до 100"
#                 )

#         def _validate_collision(custom_settings: dict) -> None:
#             """Валидация пересечения временных отрезков для custom_volume."""
#             sorted_settings = sorted(custom_settings)
#             for curr, next_ in zip(sorted_settings, sorted_settings[1:]):
#                 split_curr = curr.split("-")
#                 end_curr = list(map(int, split_curr[1].split(":")))
#                 split_next = next_.split("-")
#                 start_next = list(map(int, split_next[0].split(":")))
#                 if time(*end_curr) > time(*start_next):
#                     raise serializers.ValidationError(
#                         "Обнаружено пересечение в часах "
#                         "пользовательских настроек громкости"
#                     )

#         for day, settings in value.items():
#             # 1
#             try:
#                 req_keys = {
#                     "worktime": settings["worktime"],
#                     "default_volume": tuple(settings["default_volume"]),
#                 }
#             except KeyError as ke:
#                 raise serializers.ValidationError(f"{ke} не передан")
#             except TypeError:
#                 raise serializers.ValidationError(
#                     "Список значений громкости имеет не правильный формат"
#                 )
#             # 2
#             _validate_time(req_keys["worktime"])
#             _validate_volume(req_keys["default_volume"])
#             # 3
#             if "custom_volume" in settings:
#                 for interval, volume in settings["custom_volume"].items():
#                     _validate_time(interval)
#                     _validate_volume(tuple(volume))
#                 _validate_collision(settings["custom_volume"])
#         return value

#     # def _set_tenants(self, nomenclature, tenants_data):
#     #     if not tenants_data:
#     #         return
#     #
#     #     unique_ids = set()
#     #     objs = []
#     #
#     #     for t in tenants_data:
#     #         tenant_id = t["id"]
#     #
#     #         if tenant_id in unique_ids:
#     #             continue
#     #
#     #         unique_ids.add(tenant_id)
#     #
#     #         objs.append(
#     #             NomenclatureTenant(
#     #                 nomenclature=nomenclature,
#     #                 tenant_id=tenant_id,
#     #                 floor=t.get("floor", "")
#     #             )
#     #         )
#     #
#     #     NomenclatureTenant.objects.bulk_create(objs)

#     def _set_tenants(self, nomenclature, tenants_data):
#         """Установка арендаторов для номенклатуры"""
#         for tenant_data in tenants_data:
#             tenant_id = tenant_data.get('id')
#             floor = tenant_data.get('floor', '')
#             brand = tenant_data.get('brand')  # Здесь brand должен быть объектом Brand или ID

#             # Получаем Counterparty (арендатора)
#             try:
#                 counterparty = Counterparty.objects.get(id=tenant_id)
#             except Counterparty.DoesNotExist:
#                 raise Exception(f"Арендатор с id {tenant_id} не найден")

#             # Если brand передан как ID, получаем объект Brand
#             brand_obj = None
#             if brand:
#                 if isinstance(brand, str):
#                     try:
#                         brand_obj = Brand.objects.get(id=brand)
#                     except Brand.DoesNotExist:
#                         raise Exception(f"Бренд с id {brand} не найден")
#                 else:
#                     brand_obj = brand

#             # Создаем связь
#             NomenclatureTenant.objects.create(
#                 nomenclature=nomenclature,
#                 tenant=counterparty,
#                 floor=floor,
#                 brand=brand_obj,  # 👈 Убедитесь, что передается объект Brand
#             )

#     def create(self, validated_data):
#         # Извлекаем все поля, которые нужно обработать отдельно
#         address_data = None
#         address_id = None

#         # Вариант 1: через address_data
#         if "address_data" in validated_data:
#             address_data = validated_data.pop("address_data")

#         # Вариант 2: через address_id
#         elif "address_id" in validated_data:
#             address_id = validated_data.pop("address_id")

#         # Вариант 3: через старую структуру address.address
#         elif "address" in validated_data:
#             address_relation = validated_data.pop("address", {})
#             address_data = address_relation.get("address") if address_relation else None

#         tenants_id = validated_data.pop("tenants_id", [])

#         # Извлекаем поля внешних ключей для отдельной обработки
#         brand_id = validated_data.pop("brand_id", None)
#         legalEntity_id = validated_data.pop("legalEntity_id", None)
#         typeOfPlace_id = validated_data.pop("typeOfPlace_id", None)

#         # Получаем данные для проверок
#         code1c = validated_data.get("code1c")
#         price_per_month = validated_data.get("pricePerMonth")
#         name = validated_data.get("name")

#         # Проверка code1c на уникальность
#         if code1c:
#             old_item = Nomenclature.objects.filter(code1c=code1c).first()
#             if old_item:
#                 log_path = "/app/network_logs/nomenclature_conflicts.log"
#                 try:
#                     with open(log_path, "a", encoding="utf-8") as f:
#                         f.write(f"{name}: {old_item.id}, {getattr(old_item, 'code1c', '—')}\n")
#                 except Exception:
#                     pass

#                 raise serializers.ValidationError({
#                     "code1c": f"Номенклатура с кодом '{code1c}' уже существует (id={old_item.id})"
#                 })

#         # Проверка pricePerMonth
#         if price_per_month is not None:
#             try:
#                 if price_per_month < 0:
#                     raise serializers.ValidationError({
#                         "pricePerMonth": "Стоимость аренды не может быть меньше 0."
#                     })
#             except TypeError:
#                 raise serializers.ValidationError({
#                     "pricePerMonth": "Стоимость аренды должна быть числом."
#                 })

#         # СОЗДАЕМ НОМЕНКЛАТУРУ (после всех проверок)
#         try:
#             nomenclature = Nomenclature.objects.create(**validated_data)
#         except Exception as e:
#             raise serializers.ValidationError({
#                 "non_field_errors": f"Ошибка при создании номенклатуры: {str(e)}"
#             })

#         # Обработка brand_id
#         if brand_id:
#             try:
#                 brand = Brand.objects.get(id=brand_id)
#                 nomenclature.brand = brand
#                 nomenclature.save(update_fields=['brand'])
#             except Brand.DoesNotExist:
#                 nomenclature.delete()
#                 raise serializers.ValidationError({
#                     "brand_id": "Бренд с таким ID не найден"
#                 })
#             except Exception as e:
#                 nomenclature.delete()
#                 raise serializers.ValidationError({
#                     "brand_id": f"Ошибка при установке бренда: {str(e)}"
#                 })

#         # Обработка legalEntity_id
#         if legalEntity_id:
#             try:
#                 legal_entity = Counterparty.objects.get(id=legalEntity_id)
#                 nomenclature.legalEntity = legal_entity
#                 nomenclature.save(update_fields=['legalEntity'])
#             except Counterparty.DoesNotExist:
#                 nomenclature.delete()
#                 raise serializers.ValidationError({
#                     "legalEntity_id": "Юр. лицо с таким ID не найдено"
#                 })
#             except Exception as e:
#                 nomenclature.delete()
#                 raise serializers.ValidationError({
#                     "legalEntity_id": f"Ошибка при установке юр. лица: {str(e)}"
#                 })

#         # Обработка typeOfPlace_id
#         if typeOfPlace_id:
#             try:
#                 type_of_place = TypeOfPlace.objects.get(id=typeOfPlace_id)
#                 nomenclature.typeOfPlace = type_of_place
#                 nomenclature.save(update_fields=['typeOfPlace'])
#             except TypeOfPlace.DoesNotExist:
#                 nomenclature.delete()
#                 raise serializers.ValidationError({
#                     "typeOfPlace_id": "Тип места с таким ID не найден"
#                 })
#             except Exception as e:
#                 nomenclature.delete()
#                 raise serializers.ValidationError({
#                     "typeOfPlace_id": f"Ошибка при установке типа места: {str(e)}"
#                 })

#         # --- ОБРАБОТКА АДРЕСА ПРИ СОЗДАНИИ ---

#         # Если передан ID существующего адреса
#         if address_id is not None:
#             try:
#                 address_obj = AddressBook.objects.get(id=address_id)
#                 NomenclatureAddress.objects.create(
#                     nomenclature=nomenclature,
#                     address=address_obj
#                 )
#             except AddressBook.DoesNotExist:
#                 raise serializers.ValidationError(
#                     {"address_id": "Адрес с таким ID не найден"}
#                 )

#         # Если переданы данные адреса для создания нового
#         elif address_data is not None and address_data != {}:
#             if isinstance(address_data, dict):
#                 try:
#                     address_serializer = AddressCreateSerializer(data=address_data)
#                     address_serializer.is_valid(raise_exception=True)
#                     address_obj = address_serializer.save()

#                     NomenclatureAddress.objects.create(
#                         nomenclature=nomenclature,
#                         address=address_obj
#                     )
#                 except Exception as e:
#                     raise serializers.ValidationError({
#                         "address_data": f"Ошибка при создании адреса: {str(e)}"
#                     })
#             elif isinstance(address_data, AddressBook):
#                 NomenclatureAddress.objects.create(
#                     nomenclature=nomenclature,
#                     address=address_data
#                 )


#         # Обработка арендаторов
#         if tenants_id:
#             try:
#                 # Передаем каждому TenantWriteSerializer контекст с арендатором
#                 self._set_tenants(nomenclature, tenants_id)
#             except Exception as e:
#                 nomenclature.delete()
#                 raise serializers.ValidationError({
#                     "tenants_id": f"Ошибка при добавлении арендаторов: {str(e)}"
#                 })

#         return nomenclature

#     # def _set_tenants(self, nomenclature, tenants_data):
#     #     """
#     #     Установка арендаторов для номенклатуры с проверкой брендов.
#     #     """
#     #     for tenant_data in tenants_data:
#     #         tenant_id = tenant_data.get('id')
#     #         floor = tenant_data.get('floor', '')
#     #         brand = tenant_data.get('brand')  # или brand_id
#     #
#     #         # Получаем Counterparty (арендатора)
#     #         try:
#     #             counterparty = Counterparty.objects.get(id=tenant_id)
#     #         except Counterparty.DoesNotExist:
#     #             raise Exception(f"Арендатор с id {tenant_id} не найден")

#             # Проверяем бренд
#             # brand_obj = None
#             # if brand:
#             #     # Проверяем, что бренд принадлежит этому арендатору
#             #     # Важно: brand может быть объектом или ID
#             #     if hasattr(brand, 'id'):
#             #         # Если brand уже объект
#             #         if brand not in counterparty.brands.all():
#             #             raise Exception(
#             #                 f"Бренд '{brand.name}' не принадлежит арендатору {counterparty}"
#             #             )
#             #         brand_obj = brand
#             #     else:
#             #         # Если brand это ID
#             #         try:
#             #             brand_obj = Brand.objects.get(id=brand.id if hasattr(brand, 'id') else brand)
#             #             if brand_obj not in counterparty.brands.all():
#             #                 raise Exception(
#             #                     f"Бренд '{brand_obj.name}' не принадлежит арендатору {counterparty}"
#             #                 )
#             #         except Brand.DoesNotExist:
#             #             raise Exception(f"Бренд с id {brand} не найден")

#             # Создаем связь (проверьте, есть ли поле brand в NomenclatureTenant)
#             # NomenclatureTenant.objects.create(
#             #     nomenclature=nomenclature,
#             #     tenant=counterparty,
#             #     floor=floor,
#             #     brand=brand_obj  # если поле brand существует
#             # )

#     from django.db import transaction
#     from rest_framework import serializers

#     @transaction.atomic
#     def update(self, instance, validated_data):
#         # =========================================================
#         # 1. ВЫТАСКИВАЕМ СПЕЦ-ПОЛЯ ДО ОБНОВЛЕНИЯ
#         # =========================================================

#         # --- tenants ---
#         tenants_provided = "tenants_id" in validated_data
#         tenants_id = validated_data.pop("tenants_id", serializers.empty)

#         # --- address ---
#         address_data = serializers.empty
#         address_id = serializers.empty

#         if "address_data" in validated_data:
#             address_data = validated_data.pop("address_data")
#         elif "address_id" in validated_data:
#             address_id = validated_data.pop("address_id")
#         elif "address" in validated_data:
#             address_relation = validated_data.pop("address", {})
#             if isinstance(address_relation, dict):
#                 address_data = address_relation.get("address", serializers.empty)
#             elif isinstance(address_relation, AddressBook):
#                 address_id = address_relation.id

#         # --- foreign keys ---
#         brand_provided = "brand" in validated_data
#         brand_value = validated_data.pop("brand", serializers.empty)

#         legal_entity_provided = "legalEntity" in validated_data
#         legal_entity_value = validated_data.pop("legalEntity", serializers.empty)

#         type_of_place_provided = "typeOfPlace" in validated_data
#         type_of_place_value = validated_data.pop("typeOfPlace", serializers.empty)

#         # =========================================================
#         # 2. ЧИСТИМ ЛЕВЫЕ / READONLY ПОЛЯ
#         # =========================================================
#         validated_data.pop("type_of_place_display", None)
#         validated_data.pop("name_for_front", None)
#         validated_data.pop("tenants", None)
#         validated_data.pop("legalEntity", None)
#         validated_data.pop("brand", None)
#         validated_data.pop("address", None)

#         # =========================================================
#         # 3. ДОП. ВАЛИДАЦИЯ
#         # =========================================================
#         code1c = validated_data.get("code1c")
#         if code1c is not None:
#             conflict = (
#                 Nomenclature.objects
#                 .filter(code1c=code1c)
#                 .exclude(id=instance.id)
#                 .first()
#             )
#             if conflict:
#                 raise serializers.ValidationError({
#                     "code1c": f"Код '{code1c}' уже используется в другой номенклатуре (id={conflict.id})"
#                 })

#         if "pricePerMonth" in validated_data:
#             price_per_month = validated_data.get("pricePerMonth")
#             if price_per_month is not None:
#                 try:
#                     if price_per_month < 0:
#                         raise serializers.ValidationError({
#                             "pricePerMonth": "Стоимость аренды не может быть меньше 0."
#                         })
#                 except TypeError:
#                     raise serializers.ValidationError({
#                         "pricePerMonth": "Стоимость аренды должна быть числом."
#                     })

#         # =========================================================
#         # 4. ОБНОВЛЯЕМ ПРОСТЫЕ ПОЛЯ
#         # =========================================================
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)

#         # =========================================================
#         # 5. ОБНОВЛЯЕМ FK ПОЛЯ
#         # =========================================================
#         if brand_provided:
#             instance.brand = brand_value if brand_value not in ["", serializers.empty] else None

#         if legal_entity_provided:
#             instance.legalEntity = (
#                 legal_entity_value if legal_entity_value not in ["", serializers.empty] else None
#             )

#         if type_of_place_provided:
#             instance.typeOfPlace = (
#                 type_of_place_value if type_of_place_value not in ["", serializers.empty] else None
#             )

#         instance.save()

#         # =========================================================
#         # 6. ОБРАБОТКА АДРЕСА
#         # =========================================================

#         # Явное удаление адреса через null
#         if address_id is None:
#             if hasattr(instance, "address") and instance.address:
#                 instance.address.delete()

#         elif address_data is None:
#             if hasattr(instance, "address") and instance.address:
#                 instance.address.delete()

#         # Установка адреса по ID
#         elif address_id is not serializers.empty:
#             try:
#                 address_obj = AddressBook.objects.get(id=address_id)
#             except AddressBook.DoesNotExist:
#                 raise serializers.ValidationError({
#                     "address_id": "Адрес с таким ID не найден"
#                 })

#             NomenclatureAddress.objects.update_or_create(
#                 nomenclature=instance,
#                 defaults={"address": address_obj}
#             )

#         # Создание нового адреса по данным
#         elif address_data is not serializers.empty and address_data != {}:
#             if isinstance(address_data, dict):
#                 address_serializer = AddressCreateSerializer(data=address_data)
#                 address_serializer.is_valid(raise_exception=True)
#                 address_obj = address_serializer.save()

#                 NomenclatureAddress.objects.update_or_create(
#                     nomenclature=instance,
#                     defaults={"address": address_obj}
#                 )

#             elif isinstance(address_data, AddressBook):
#                 NomenclatureAddress.objects.update_or_create(
#                     nomenclature=instance,
#                     defaults={"address": address_data}
#                 )

#         # =========================================================
#         # 7. ПОЛНАЯ СИНХРОНИЗАЦИЯ АРЕНДАТОРОВ
#         # =========================================================
#         if tenants_provided:
#             # null или [] => удалить всех
#             if tenants_id is None or tenants_id == []:
#                 NomenclatureTenant.objects.filter(nomenclature=instance).delete()

#             else:
#                 new_rows = []
#                 seen_keys = set()

#                 for tenant_data in tenants_id:
#                     tenant_id = tenant_data.get("id")
#                     floor = tenant_data.get("floor", "")
#                     brand_obj = tenant_data.get("brand")  # уже объект Brand после сериализатора
#                     atm = tenant_data.get("atm", False)

#                     if not tenant_id:
#                         raise serializers.ValidationError({
#                             "tenants_id": "У арендатора отсутствует id"
#                         })

#                     try:
#                         counterparty = Counterparty.objects.get(id=tenant_id)
#                     except Counterparty.DoesNotExist:
#                         raise serializers.ValidationError({
#                             "tenants_id": f"Арендатор с id {tenant_id} не найден"
#                         })

#                     # Ключ уникальности будущей строки
#                     unique_key = (
#                         str(counterparty.id),
#                         str(brand_obj.id) if brand_obj else None,
#                         floor,
#                         atm,
#                     )

#                     # Если фронт прислал дубль в одном и том же PATCH — не плодим дичь
#                     if unique_key in seen_keys:
#                         continue

#                     seen_keys.add(unique_key)

#                     new_rows.append(
#                         NomenclatureTenant(
#                             nomenclature=instance,
#                             tenant=counterparty,
#                             floor=floor,
#                             brand=brand_obj,
#                             atm=atm,
#                         )
#                     )

#                 # Полная замена: удаляем старые, записываем новые
#                 NomenclatureTenant.objects.filter(nomenclature=instance).delete()
#                 NomenclatureTenant.objects.bulk_create(new_rows)

#         # =========================================================
#         # 8. ФИНАЛ
#         # =========================================================
#         instance.save()
#         return instance

#     # def get_tenants(self, obj):
#     #     """
#     #     Возвращает список арендаторов с количеством арендуемых номенклатур
#     #     """
#     #     tenants = obj.tenants.annotate(
#     #         places_count=Count("rented_nomenclatures")  # Исправлено!
#     #     ).order_by("-places_count")

#     #     return TenantsShortSerializer(tenants, many=True, context=self.context).data

#     def get_status(self, obj) -> int | None:
#         try:
#             return obj.availability.status
#         except AttributeError:
#             return None

#     def get_last_answer(self, obj) -> str:
#         try:
#             return format_local_datetime(obj.availability.last_answer_date)
#         except AttributeError:
#             return "Не выходила в сеть"

#     # def get_last_answer(self, obj) -> str:
#     #     try:
#     #         # TODO: ответ приходит на -7 часов от крск (по UTC) - исправить
#     #         return f"{obj.availability.last_answer_date:%Y-%m-%d %H:%M:%S}"

#     #     except AttributeError:
#     #         return "Не выходила в сеть"

#     def get_interior(self, obj):
#         return InNomenclaturePhotoSerializer(
#             obj.images.filter(type="interior"), many=True
#         ).data

#     def get_exterior(self, obj):
#         return InNomenclaturePhotoSerializer(
#             obj.images.filter(type="exterior"), many=True
#         ).data

#     def _user_id_name(self, user):
#         if not user:
#             return None

#         # Берём ВСЕ basic телефоны
#         basic_phones = list(
#             user.contacts_cp
#             .filter(type="phone", basic=True)
#             .values_list("meaning", flat=True)
#         )

#         # fallback — если basic нет, но есть phone_number в CustomUser
#         if not basic_phones and user.phone_number:
#             basic_phones = [str(user.phone_number)]

#         # гарантируем строки
#         phones = [str(p) for p in basic_phones if p]

#         return {
#             "id": str(user.id),
#             "full_name": user.first_name,
#             "phone_number": phones,
#         }

#     def to_representation(self, obj):
#         repr_ = super().to_representation(obj)

#         # Создаем main_info точно как в оригинале
#         repr_["main_info"] = {
#             "description": obj.description,
#             "owner": obj.owner.full_name,
#             "timezone": TIMEZONES[obj.timezone],
#             "status": self.get_status(obj),
#             "last_answer": self.get_last_answer(obj),
#             "version": obj.version,
#             "created": f"{obj.created:%Y-%m-%d %H:%M:%S}",
#         }

#         repr_["responsible"] = {
#             "ad": self._user_id_name(obj.responsible_ad),
#             "radio": self._user_id_name(obj.responsible_radio),
#             "technic": self._user_id_name(obj.responsible_technic),
#             "technic_on_address": self._user_id_name(obj.responsible_technic_on_address),
#             "placement_marketing": self._user_id_name(obj.responsible_placement_marketing),
#         }

#         repr_["tenants_length"] = obj.tenants.count()

#         # if 'tenants' in repr_ and repr_['tenants']:
#         #     transformed_tenants = []
#         #     for tenant_item in repr_['tenants']:
#         #         # Извлекаем данные из вложенной структуры
#         #         tenant_data = tenant_item.get('tenant', {})
#         #         floor = tenant_item.get('floor')
#         #
#         #         # Создаем новую структуру
#         #         transformed_tenant = {
#         #             'id': tenant_data.get('id'),
#         #             'brands_list': tenant_data.get('brands_list'),
#         #             'logotypes': tenant_data.get('logotypes', []),
#         #             'floor': floor
#         #         }
#         #         transformed_tenants.append(transformed_tenant)
#         #
#         #     repr_['tenants'] = transformed_tenants

#         # Добавляем broadcast
#         repr_["broadcast"] = getattr(obj.legalEntity, "broadcast", None)

#         # ✅ FIXED: Create a list of keys to remove instead of modifying while iterating
#         fields_to_remove = []
#         for field in repr_["main_info"]:
#             if field in repr_:
#                 fields_to_remove.append(field)

#         # Remove the fields after iteration
#         for field in fields_to_remove:
#             repr_.pop(field)

#         # Remove responsibility fields
#         fields_to_remove = [
#             "responsible_ad",
#             "responsible_radio",
#             "responsible_technic",
#             "responsible_technic_on_address",
#             "responsible_placement_marketing",
#         ]
#         for field in fields_to_remove:
#             repr_.pop(field, None)

#         # Обработка settings (точная копия оригинала)
#         if "settings" in repr_ and repr_["settings"]:
#             # ✅ FIXED: Create a copy of items or use list() to avoid modification during iteration
#             for day, setting in list(repr_["settings"].items()):
#                 repr_["settings"][day] = {
#                     "worktime": setting["worktime"],
#                     "default_volume": setting["default_volume"],
#                     "custom_volume": (
#                         setting["custom_volume"]
#                         if "custom_volume" in setting
#                         else {}
#                     ),
#                 }

#         if "address" in repr_:
#             repr_.pop("address")

#         # Преобразование contentType (точная копия оригинала)
#         if "contentType" in repr_:
#             key = repr_["contentType"]
#             repr_["contentType"] = AVAILABLE_CONTENT_TYPES.get(key, key)

#         return repr_


# class NomenclatureListSerializer(serializers.ModelSerializer):
#     """Сериализация списка номенклатур."""
#     typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)

#     brand = BrandListSerializer()
#     legalEntity = CounterpartiesShortSerializer()
#     exterior = serializers.SerializerMethodField()

#     formattedAddress = serializers.CharField(
#         source="formatted_address",
#         read_only=True
#     )

#     nameForFront = serializers.CharField(
#         source="name_for_front",
#         read_only=True
#     )

#     oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)

#     class Meta:

#         fields = (
#             "id",
#             "name",
#             "nameForFront",
#             # "timezone",
#             # "status",
#             "legalEntity",
#             "brand",
#             "exterior",
#             "formattedAddress",
#             # "contentType",
#             "typeOfPlace",
#             "pricePerMonth",
#             "code1c",
#             "oldCatalogSlug",
#         )
#         extra_fields = ("nameForFront", "formattedAddress", "oldCatalogSlug")
#         read_only_fields = fields
#         model = Nomenclature

#     def get_exterior(self, obj):
#         return InNomenclaturePhotoSerializer(
#             obj.images.filter(type="exterior"), many=True
#         ).data

#     def get_status(self, obj):
#         try:
#             return obj.availability.status
#         except AttributeError:
#             return None

#     def get_last_answer(self, obj):
#         try:
#             return format_local_datetime(obj.availability.last_answer_date)
#         except AttributeError:
#             return "Не выходила в сеть"

#     # def get_last_answer(self, obj):
#     #     try:
#     #         return f"{obj.availability.last_answer_date:%Y-%m-%d %H:%M:%S}"
#     #     except AttributeError:
#     #         return "Не выходила в сеть"



# from django.utils import timezone as dj_timezone

# class StatusHistorySerializer(serializers.ModelSerializer):
#     """Сериализация истории доступности."""

#     class Meta:
#         fields = ("change_time", "status")
#         read_only_fields = fields
#         model = StatusHistory

#     def to_representation(self, value):
#         repr_ = super().to_representation(value)
#         repr_["change_time"] = format_local_datetime(value.change_time)
#         repr_["timezone"] = dj_timezone.get_current_timezone_name()
#         return repr_


# class NomenclatureCardSerializer(serializers.ModelSerializer):
#     """Минимальный сериализатор для карточек каталога и корзины."""
#     brand = BrandCardSerializer()
#     exterior = serializers.SerializerMethodField()
#     formattedAddress = serializers.SerializerMethodField()
#     typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
#     nameForFront = serializers.CharField(source="name_for_front", read_only=True)
#     slotsPerHour = serializers.CharField(source="slots_per_hour", read_only=True)
#     oldCatalogSlug = serializers.CharField(source="old_catalog_slug", read_only=True)

#     class Meta:
#         model = Nomenclature
#         fields = (
#             "id",
#             "nameForFront",
#             "brand",
#             "exterior",
#             "formattedAddress",
#             "typeOfPlace",
#             "pricePerMonth",
#             "slotsPerHour",
#             "oldCatalogSlug"
#         )
#         read_only_fields = fields

#     def get_exterior(self, obj):
#         image = obj.images.filter(type="exterior").first()
#         if not image:
#             return []
#         return InNomenclaturePhotoSerializer([image], many=True).data

#     def get_formattedAddress(self, obj):
#         try:
#             nomenclature_address = obj.address
#         except ObjectDoesNotExist:
#             return ""

#         if not nomenclature_address or not nomenclature_address.address:
#             return ""

#         address = nomenclature_address.address
#         address_parts = []

#         if address.city and address.city.name:
#             address_parts.append(f"г. {address.city.name}")

#         if address.street and address.street.name:
#             address_parts.append(f"ул. {address.street.name}")

#         house_number = None
#         if address.house and address.house.number:
#             house_number = address.house.number
#         elif address.building and address.building.number:
#             house_number = address.building.number

#         if house_number:
#             address_parts.append(house_number)

#         return ', '.join(address_parts)

# class NomenclatureShortSerializer(serializers.ModelSerializer):
#     nameForFront = serializers.SerializerMethodField()
#     formattedAddress = serializers.SerializerMethodField()
#     exterior = serializers.SerializerMethodField()
#     typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
#     class Meta:
#         model = Nomenclature
#         fields = ["id", "nameForFront", "formattedAddress", "exterior",  "typeOfPlace", "pricePerMonth"]

#     def get_nameForFront(self, obj):
#         parts = []

#         if obj.typeOfPlace:
#             parts.append(obj.typeOfPlace.name)

#         if obj.brand:
#             parts.append(obj.brand.name)

#         if obj.address and obj.address.address:
#             addr = obj.address.address
#             address_parts = []
#             if addr.city:
#                 address_parts.append(f"г. {addr.city.name}")
#             if addr.street:
#                 address_parts.append(f"ул. {addr.street.name}")
#             if addr.house:
#                 address_parts.append(addr.house.number)
#             if address_parts:
#                 parts.append(", ".join(address_parts))

#         return " | ".join(filter(None, parts)) or None

#     def get_formattedAddress(self, obj):
#         try:
#             nomenclature_address = obj.address
#         except ObjectDoesNotExist:
#             return ""

#         if not nomenclature_address or not nomenclature_address.address:
#             return ""

#         address = nomenclature_address.address
#         address_parts = []

#         if address.city and address.city.name:
#             address_parts.append(f"г. {address.city.name}")

#         if address.street and address.street.name:
#             address_parts.append(f"ул. {address.street.name}")

#         house_number = None
#         if address.house and address.house.number:
#             house_number = address.house.number
#         elif address.building and address.building.number:
#             house_number = address.building.number

#         if house_number:
#             address_parts.append(house_number)

#         return ', '.join(address_parts)

#     def get_exterior(self, obj):
#         image = obj.images.filter(type="exterior").first()
#         if not image:
#             return []
#         return InNomenclaturePhotoSerializer([image], many=True).data
