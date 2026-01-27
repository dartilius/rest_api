"""
ФИЛЬТРЫ ДЛЯ НОМЕНКЛАТУР С ПОДДЕРЖКОЙ АДРЕСОВ (УПРОЩЕННАЯ ВЕРСИЯ)

ОСНОВНАЯ ИДЕЯ:
• Сохраняем ВСЮ существующую логику фильтрации номенклатур
• Добавляем простую фильтрацию по адресам
• Используем короткие имена параметров (без префикса 'address_')
• Убираем сложные географические фильтры
• Добавляем поддержку множественных значений для текстовых фильтров
"""

import uuid
from django.db import models
from django_filters import (
    AllValuesMultipleFilter, CharFilter, FilterSet, UUIDFilter,
    BaseInFilter, OrderingFilter, BooleanFilter
)
from nomenclatures.models import Nomenclature


class UUIDCommaInFilter(BaseInFilter, UUIDFilter):
    """Поддерживает фильтрацию UUID через запятую (в URL)."""

    def filter(self, qs, value):
        if value and isinstance(value, str):
            # Убираем пустые значения
            value = [v.strip() for v in value.split(",") if v.strip()]
        return super().filter(qs, value)


class CharCommaInFilter(BaseInFilter, CharFilter):
    """
    Поддерживает фильтрацию строковых значений через запятую.

    ПРИМЕР:
        ?city_name=Москва,Санкт-Петербург → города Москва ИЛИ Санкт-Петербург
    """

    def filter(self, qs, value):
        if value and isinstance(value, str):
            # Убираем пустые значения
            values = [v.strip() for v in value.split(",") if v.strip()]
            if values:
                # Создаем OR-условие для каждого значения
                q_objects = models.Q()
                for val in values:
                    q_objects |= models.Q(**{self.field_name: val})
                return qs.filter(q_objects)
        return qs


class NomenclatureFilter(FilterSet):
    """
    Фильтрация номенклатур с поддержкой адресов.

    КОРОТКИЕ ИМЕНА ПАРАМЕТРОВ ДЛЯ АДРЕСОВ:
    • country, region, city, street - фильтрация по UUID
    • country_name, region_name, city_name, street_name - поиск по названиям
    • has_address - есть ли адрес у номенклатуры

    ПОДДЕРЖИВАЕТ МНОЖЕСТВЕННЫЕ ЗНАЧЕНИЯ:
    • ?city_name=Москва,Санкт-Петербург
    • ?country=uuid1,uuid2
    """

    # ==========================================================================
    # СУЩЕСТВУЮЩИЕ ФИЛЬТРЫ НОМЕНКЛАТУР (БЕЗ ИЗМЕНЕНИЙ)
    # ==========================================================================

    search = CharFilter(method='universal_search', label='Универсальный поиск')

    versions = AllValuesMultipleFilter(field_name='version')
    version = CharFilter(field_name='version', lookup_expr='icontains')
    status = CharFilter(method='get_status', label='Статус')
    name = CharFilter(field_name='name', lookup_expr='icontains')
    id = CharFilter(field_name='id', lookup_expr='iexact')
    timezone = CharFilter(field_name='timezone', lookup_expr='iexact')
    brand_id = UUIDCommaInFilter(field_name='brand_id', lookup_expr='in')
    code1c = CharFilter(field_name='code1c', lookup_expr='iexact')

    # Новые поля для фильтрации
    legal_entity_name = CharFilter(
        field_name='legalEntity__name',
        lookup_expr='icontains',
        label='Название юридического лица'
    )

    brand_name = CharFilter(
        field_name='brand__name',
        lookup_expr='icontains',
        label='Название бренда'
    )

    type_of_place = CharFilter(
        field_name='typeOfPlace',
        lookup_expr='icontains',
        label='Тип места размещения'
    )

    # ==========================================================================
    # НОВЫЕ ФИЛЬТРЫ ДЛЯ АДРЕСОВ (КОРОТКИЕ ИМЕНА)
    # ==========================================================================

    # 1. UUID фильтры для адресов (списком через запятую) - КОРОТКИЕ ИМЕНА
    address_id = UUIDCommaInFilter(
        field_name='address__address_id',
        lookup_expr='in',
        label='ID адреса',
        help_text='Фильтрация по ID адреса через запятую'
    )

    country = UUIDCommaInFilter(
        field_name='address__address__country_id',
        lookup_expr='in',
        label='ID страны',
        help_text='Фильтрация по странам (UUID через запятую)'
    )

    region = UUIDCommaInFilter(
        field_name='address__address__region_id',
        lookup_expr='in',
        label='ID региона',
        help_text='Фильтрация по регионам (UUID через запятую)'
    )

    city = UUIDCommaInFilter(
        field_name='address__address__city_id',
        lookup_expr='in',
        label='ID города',
        help_text='Фильтрация по городам (UUID через запятую)'
    )

    street = UUIDCommaInFilter(
        field_name='address__address__street_id',
        lookup_expr='in',
        label='ID улицы',
        help_text='Фильтрация по улицам (UUID через запятую)'
    )

    # 2. Текстовые фильтры для адресов - ПОДДЕРЖИВАЮТ МНОЖЕСТВЕННЫЕ ЗНАЧЕНИЯ
    country_name = CharCommaInFilter(
        field_name='address__address__country__name__icontains',
        label='Страна',
        help_text='Поиск по странам (названия через запятую)'
    )

    region_name = CharCommaInFilter(
        field_name='address__address__region__name__icontains',
        label='Регион',
        help_text='Поиск по регионам (названия через запятую)'
    )

    city_name = CharCommaInFilter(
        field_name='address__address__city__name__icontains',
        label='Город',
        help_text='Поиск по городам (названия через запятую)'
    )

    street_name = CharCommaInFilter(
        field_name='address__address__street__name__icontains',
        label='Улица',
        help_text='Поиск по улицам (названия через запятую)'
    )

    house_number = CharCommaInFilter(
        field_name='address__address__house__number__icontains',
        label='Номер дома',
        help_text='Поиск по номерам домов (через запятую)'
    )

    index = CharCommaInFilter(
        field_name='address__address__index__icontains',
        label='Почтовый индекс',
        help_text='Поиск по почтовым индексам (через запятую)'
    )

    microdistrict = CharCommaInFilter(
        field_name='address__address__microdistrict__icontains',
        label='Микрорайон',
        help_text='Поиск по микрорайонам (через запятую)'
    )

    # 3. Текстовые фильтры с icontains (для точного поиска по одному значению)
    city_name_contains = CharFilter(
        field_name='address__address__city__name',
        lookup_expr='icontains',
        label='Город (поиск)',
        help_text='Поиск по части названия города'
    )

    street_name_contains = CharFilter(
        field_name='address__address__street__name',
        lookup_expr='icontains',
        label='Улица (поиск)',
        help_text='Поиск по части названия улицы'
    )

    # 4. Простые булевы фильтры
    has_address = BooleanFilter(
        field_name='address__address',
        lookup_expr='isnull',
        exclude=True,
        label='Есть адрес',
        help_text='Только номенклатуры с привязанным адресом'
    )

    has_index = BooleanFilter(
        field_name='address__address__index',
        lookup_expr='isnull',
        exclude=True,
        label='Есть индекс',
        help_text='Только адреса с почтовым индексом'
    )

    has_house = BooleanFilter(
        field_name='address__address__house',
        lookup_expr='isnull',
        exclude=True,
        label='Есть дом',
        help_text='Только адреса с указанным домом'
    )

    # ==========================================================================
    # СОРТИРОВКА (РАСШИРЯЕМ СУЩЕСТВУЮЩУЮ)
    # ==========================================================================

    ordering = OrderingFilter(
        fields=(
            # Существующие поля номенклатур
            ('name', 'name'),
            ('version', 'version'),
            ('timezone', 'timezone'),
            ('pricePerMonth', 'pricePerMonth'),
            ('created', 'created'),
            ('brand__name', 'brand_name'),
            ('legalEntity__name', 'legal_entity_name'),
            ('typeOfPlace', 'type_place'),

            # Новые поля для адресов (короткие имена)
            ('address__address__country__name', 'country'),
            ('address__address__region__name', 'region'),
            ('address__address__city__name', 'city'),
            ('address__address__street__name', 'street'),
            ('address__address__house__number', 'house'),
            ('address__address__index', 'index'),
        ),
        field_labels={
            # Существующие метки
            'name': 'Название',
            'version': 'Версия ПО',
            'timezone': 'Часовой пояс',
            'pricePerMonth': 'Цена',
            'created': 'Дата создания',
            'brand__name': 'Бренд',
            'legalEntity__name': 'Юр.лицо',
            'typeOfPlace': 'Тип места',

            # Новые метки для адресов
            'address__address__country__name': 'Страна',
            'address__address__region__name': 'Регион',
            'address__address__city__name': 'Город',
            'address__address__street__name': 'Улица',
            'address__address__house__number': 'Дом',
            'address__address__index': 'Индекс',
        }
    )

    class Meta:
        model = Nomenclature
        fields = (
            # Существующие поля
            'search', 'name', 'id', 'timezone', 'versions', 'status',
            'brand_id', 'code1c', 'legal_entity_name', 'brand_name',
            'type_of_place',

            # Новые поля для адресов (короткие имена)
            'address_id', 'country', 'region', 'city', 'street',
            'country_name', 'region_name', 'city_name', 'street_name',
            'house_number', 'index', 'microdistrict',
            'city_name_contains', 'street_name_contains',
            'has_address', 'has_index', 'has_house'
        )

    # ==========================================================================
    # СУЩЕСТВУЮЩИЕ МЕТОДЫ (БЕЗ ИЗМЕНЕНИЙ)
    # ==========================================================================

    def get_status(self, queryset, name, value):
        """
        Специальный метод для фильтрации по статусам.
        """
        if value.lower() == 'null':
            return queryset.filter(availability__status=None)
        elif value in ('0', '1', '2'):
            return queryset.filter(availability__status=value)
        else:
            return queryset

    # ==========================================================================
    # ОБНОВЛЕННЫЙ МЕТОД UNIVERSAL_SEARCH
    # ==========================================================================

    def universal_search(self, queryset, name, value):
        """
        Универсальный поиск по номенклатурам и связанным сущностям.
        Теперь ищет и по адресам тоже!
        """
        if not value:
            return queryset

        q = models.Q()

        # =========================
        # Nomenclature (свои поля) - СУЩЕСТВУЮЩИЙ КОД
        # =========================
        q |= models.Q(name__icontains=value)
        q |= models.Q(version__icontains=value)
        q |= models.Q(code1c__icontains=value)
        q |= models.Q(typeOfPlace__icontains=value)

        # =========================
        # Brand - СУЩЕСТВУЮЩИЙ КОД
        # =========================
        q |= models.Q(brand__name__icontains=value)

        # =========================
        # LegalEntity (Counterparty FK) - СУЩЕСТВУЮЩИЙ КОД
        # =========================
        q |= models.Q(legalEntity__first_name__icontains=value)
        q |= models.Q(legalEntity__middle_name__icontains=value)
        q |= models.Q(legalEntity__last_name__icontains=value)
        q |= models.Q(legalEntity__keyword__icontains=value)
        q |= models.Q(legalEntity__description__icontains=value)
        q |= models.Q(legalEntity__brands__name__icontains=value)

        # =========================
        # Tenants (Counterparty M2M) - СУЩЕСТВУЮЩИЙ КОД
        # =========================
        q |= models.Q(tenants__first_name__icontains=value)
        q |= models.Q(tenants__middle_name__icontains=value)
        q |= models.Q(tenants__last_name__icontains=value)
        q |= models.Q(tenants__keyword__icontains=value)
        q |= models.Q(tenants__description__icontains=value)
        q |= models.Q(tenants__brands__name__icontains=value)

        # =========================
        # Responsible radio - СУЩЕСТВУЮЩИЙ КОД
        # =========================
        q |= models.Q(responsible_radio__email__icontains=value)
        q |= models.Q(responsible_radio__first_name__icontains=value)
        q |= models.Q(responsible_radio__middle_name__icontains=value)
        q |= models.Q(responsible_radio__last_name__icontains=value)
        q |= models.Q(responsible_radio__phone_number__icontains=value)
        q |= models.Q(responsible_radio__code1c__icontains=value)

        # =========================
        # Responsible ad - СУЩЕСТВУЮЩИЙ КОД
        # =========================
        q |= models.Q(responsible_ad__email__icontains=value)
        q |= models.Q(responsible_ad__first_name__icontains=value)
        q |= models.Q(responsible_ad__middle_name__icontains=value)
        q |= models.Q(responsible_ad__last_name__icontains=value)
        q |= models.Q(responsible_ad__phone_number__icontains=value)
        q |= models.Q(responsible_ad__code1c__icontains=value)

        # =========================
        # АДРЕСЫ (НОВОЕ!) - ДОБАВЛЯЕМ ПОИСК ПО ВСЕМ ПОЛЯМ АДРЕСА
        # =========================
        q |= models.Q(address__address__country__name__icontains=value)
        q |= models.Q(address__address__region__name__icontains=value)
        q |= models.Q(address__address__city__name__icontains=value)
        q |= models.Q(address__address__street__name__icontains=value)
        q |= models.Q(address__address__house__number__icontains=value)
        q |= models.Q(address__address__building__number__icontains=value)
        q |= models.Q(address__address__index__icontains=value)
        q |= models.Q(address__address__microdistrict__icontains=value)

        return queryset.filter(q).distinct()

    @property
    def qs(self):
        """
        ОПТИМИЗАЦИЯ QUERYSET ДЛЯ ВСЕХ ЗАПРОСОВ.
        """
        queryset = super().qs

        # Оптимизация только для списковых запросов
        if not self.request or 'pk' not in self.request.parser_context.get('kwargs', {}):
            queryset = queryset.select_related(
                # Существующие связи
                'brand',
                'legalEntity',
                'responsible_radio',
                'responsible_ad',
                'availability',

                # Новые связи для адресов
                'address__address',
                'address__address__country',
                'address__address__region',
                'address__address__city',
                'address__address__street',
                'address__address__house',
                'address__address__building'
            ).prefetch_related(
                'tenants'
            )

        return queryset


# ==============================================================================
# ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ
# ==============================================================================

"""
ВСЕ СУЩЕСТВУЮЩИЕ ЗАПРОСЫ ПРОДОЛЖАЮТ РАБОТАТЬ:

1. Поиск по названию номенклатуры:
   GET /api/nomenclatures/?search=Станция1

2. Фильтрация по бренду:
   GET /api/nomenclatures/?brand_id=uuid1,uuid2

3. Фильтрация по статусу:
   GET /api/nomenclatures/?status=0

НОВЫЕ ВОЗМОЖНОСТИ С АДРЕСАМИ (ПРОСТЫЕ И КОРОТКИЕ ПАРАМЕТРЫ):

1. Поиск по нескольким городам:
   GET /api/nomenclatures/?city_name=Москва,Санкт-Петербург

2. Фильтрация по ID страны:
   GET /api/nomenclatures/?country=uuid_россии,uuid_казахстана

3. Поиск по нескольким странам (по названию):
   GET /api/nomenclatures/?country_name=Россия,Казахстан

4. Поиск по улице:
   GET /api/nomenclatures/?street_name=Ленина,Победы

5. Фильтрация по наличию адреса:
   GET /api/nomenclatures/?has_address=true

6. Поиск по почтовому индексу:
   GET /api/nomenclatures/?index=101000,102000

7. Поиск по микрорайону:
   GET /api/nomenclatures/?microdistrict=Центральный,Северный

8. Частичный поиск по городу (icontains):
   GET /api/nomenclatures/?city_name_contains=Моск

9. Сортировка по городу:
   GET /api/nomenclatures/?ordering=city

10. Сортировка по стране и названию:
    GET /api/nomenclatures/?ordering=country,-name

КОМБИНИРОВАННЫЕ ЗАПРОСЫ:

1. Номенклатуры в Москве или СПб от бренда "Ростелеком":
   GET /api/nomenclatures/?city_name=Москва,Санкт-Петербург&brand_name=Ростелеком

2. Онлайн номенклатуры с адресом в России:
   GET /api/nomenclatures/?status=0&has_address=true&country_name=Россия

3. Номенклатуры без адреса:
   GET /api/nomenclatures/?has_address=false

4. Поиск "Москва Ленина" в универсальном поиске:
   GET /api/nomenclatures/?search=Москва Ленина

5. Номенклатуры с почтовым индексом в диапазоне:
   GET /api/nomenclatures/?has_index=true&index=101,102,103

ПРЕИМУЩЕСТВА ЭТОЙ ВЕРСИИ:
• Короткие имена параметров (city вместо address_city_name)
• Поддержка множественных значений через запятую
• Нет сложных географических фильтров
• Простота использования для фронтенда
• Все старые запросы работают
"""