"""
Административный интерфейс (Django Admin) для справочника адресов.

МОДУЛЬ ADMIN:
─────────────────────────────────────────────────────────────────────────────────────
Этот модуль настраивает отображение моделей адресов в административном интерфейсе Django.
Использует django-autocomplete-light (DAL) для улучшения пользовательского опыта.

СТРУКТУРА МОДУЛЯ:
─────────────────────────────────────────────────────────────────────────────────────
1. Autocomplete Views
   • Для всех моделей с зависимостями
   • Поддержка цепочек зависимостей (например, улица зависит от города)
   • Поиск по текстовым полям

2. ModelAdmin классы
   • Для каждой модели адреса
   • Настройка отображения, поиска, фильтрации
   • Использование autocomplete_fields для связанных полей

3. Особенности
   • Иерархическое отображение адресов
   • Быстрый поиск по всем полям
   • Автозаполнение зависимых полей
   • Валидация целостности данных

ИСПОЛЬЗУЕМЫЕ БИБЛИОТЕКИ:
• django.contrib.admin
• dal (django-autocomplete-light)
"""

from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.utils.html import format_html
from dal import autocomplete

from .models import (
    Country, FederalDistrict, TypeRegion, Timezone, Region,
    LocalityType, City, AdministrativeTerritory,
    AdministrativeTerritorialUnit, StreetType, Street,
    House, Building, Address
)


# ====================================================================================
# МОДУЛЬ 1: КЛАССЫ ДЛЯ АВТОКОМПЛИТА (AUTOCOMPLETE)
# ====================================================================================

class FederalDistrictAutocomplete(autocomplete.Select2QuerySetView):
    """
    АВТОКОМПЛИТ ДЛЯ ФЕДЕРАЛЬНЫХ ОКРУГОВ.

    ОСОБЕННОСТИ:
        • Фильтрация по стране (если передана в forwarded)
        • Поиск по названию федерального округа
        • Сортировка по названию

    ИСПОЛЬЗУЕТСЯ В:
        • Административном интерфейсе для поля FederalDistrict
        • Формах создания/редактирования регионов
    """

    def get_queryset(self):
        """
        ПОЛУЧЕНИЕ QUERYSET ДЛЯ АВТОКОМПЛИТА.

        ЛОГИКА:
            1. Начинаем с всех федеральных округов
            2. Фильтруем по стране, если она передана
            3. Фильтруем по поисковому запросу
            4. Сортируем по названию

        ВОЗВРАЩАЕТ:
            QuerySet: Отфильтрованный queryset федеральных округов
        """
        qs = FederalDistrict.objects.all().select_related('country')

        # Фильтрация по стране (если передана)
        country_id = self.forwarded.get('country', None)
        if country_id:
            qs = qs.filter(country_id=country_id)

        # Поиск по названию
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by('country__name', 'name')


class RegionAutocomplete(autocomplete.Select2QuerySetView):
    """
    АВТОКОМПЛИТ ДЛЯ РЕГИОНОВ.

    ОСОБЕННОСТИ:
        • Фильтрация по федеральному округу
        • Поиск по названию региона
        • Учет типа региона в отображении
    """

    def get_queryset(self):
        """Получение queryset для регионов с фильтрацией."""
        qs = Region.objects.all().select_related(
            'federal_district', 'type_region', 'timezone'
        )

        # Фильтрация по федеральному округу
        fd_id = self.forwarded.get('federal_district', None)
        if fd_id:
            qs = qs.filter(federal_district_id=fd_id)

        # Поиск по названию
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by('federal_district__name', 'name')

    def get_result_label(self, result):
        """
        ФОРМАТИРОВАНИЕ НАЗВАНИЯ РЕГИОНА ДЛЯ ОТОБРАЖЕНИЯ.

        АРГУМЕНТЫ:
            result : Region
                Объект региона

        ВОЗВРАЩАЕТ:
            str: Отформатированное название региона
        """
        return str(result)


class CityAutocomplete(autocomplete.Select2QuerySetView):
    """
    АВТОКОМПЛИТ ДЛЯ ГОРОДОВ.

    ОСОБЕННОСТИ:
        • Фильтрация по региону
        • Поиск по названию города
        • Учет типа населенного пункта в отображении
    """

    def get_queryset(self):
        """Получение queryset для городов с фильтрацией."""
        qs = City.objects.all().select_related('region', 'locality_type', 'timezone')

        # Фильтрация по региону
        region_id = self.forwarded.get('region', None)
        if region_id:
            qs = qs.filter(region_id=region_id)

        # Поиск по названию
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by('region__name', 'name')

    def get_result_label(self, result):
        """Форматирование названия города для отображения."""
        return str(result)


class AdministrativeTerritoryAutocomplete(autocomplete.Select2QuerySetView):
    """
    АВТОКОМПЛИТ ДЛЯ АДМИНИСТРАТИВНЫХ ОКРУГОВ.

    ОСОБЕННОСТИ:
        • Фильтрация по городу
        • Поиск по названию округа
        • Только для городов с has_administrative_territory=True
    """

    def get_queryset(self):
        """Получение queryset для административных округов."""
        qs = AdministrativeTerritory.objects.all().select_related('city')

        # Фильтрация по городу
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)

        # Поиск по названию
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by('city__name', 'name')


class AdministrativeUnitAutocomplete(autocomplete.Select2QuerySetView):
    """
    АВТОКОМПЛИТ ДЛЯ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНЫХ ЕДИНИЦ.

    ОСОБЕННОСТИ:
        • Фильтрация по городу
        • Фильтрация по административному округу (опционально)
        • Поиск по названию АТЕ
    """

    def get_queryset(self):
        """Получение queryset для административно-территориальных единиц."""
        qs = AdministrativeTerritorialUnit.objects.all().select_related(
            'city', 'administrative_territory'
        )

        # Фильтрация по городу
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)

        # Фильтрация по административному округу
        admin_territory_id = self.forwarded.get('administrative_territory', None)
        if admin_territory_id:
            qs = qs.filter(administrative_territory_id=admin_territory_id)

        # Поиск по названию
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by('city__name', 'name')


class StreetAutocomplete(autocomplete.Select2QuerySetView):
    """
    АВТОКОМПЛИТ ДЛЯ УЛИЦ.

    ОСОБЕННОСТИ:
        • Фильтрация по городу
        • Поиск по названию улицы
        • Учет типа улицы в отображении
    """

    def get_queryset(self):
        """Получение queryset для улиц."""
        qs = Street.objects.all().select_related('city', 'street_type')

        # Фильтрация по городу
        city_id = self.forwarded.get('city', None)
        if city_id:
            qs = qs.filter(city_id=city_id)

        # Поиск по названию
        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by('city__name', 'name')

    def get_result_label(self, result):
        """Форматирование названия улицы для отображения."""
        return str(result)


class HouseAutocomplete(autocomplete.Select2QuerySetView):
    """
    АВТОКОМПЛИТ ДЛЯ ДОМОВ.

    ОСОБЕННОСТИ:
        • Фильтрация по улице
        • Поиск по номеру дома
        • Отображение с названием улицы
    """

    def get_queryset(self):
        """Получение queryset для домов."""
        qs = House.objects.all().select_related('street')

        # Фильтрация по улице
        street_id = self.forwarded.get('street', None)
        if street_id:
            qs = qs.filter(street_id=street_id)

        # Поиск по номеру дома
        if self.q:
            qs = qs.filter(number__icontains=self.q)

        return qs.order_by('street__name', 'number')

    def get_result_label(self, result):
        """Форматирование дома для отображения."""
        return f"{result.street}, д. {result.number}"


class BuildingAutocomplete(autocomplete.Select2QuerySetView):
    """
    АВТОКОМПЛИТ ДЛЯ СТРОЕНИЙ.

    ОСОБЕННОСТИ:
        • Фильтрация по дому
        • Поиск по номеру строения
        • Отображение с полным адресом дома
    """

    def get_queryset(self):
        """Получение queryset для строений."""
        qs = Building.objects.all().select_related('house', 'house__street')

        # Фильтрация по дому
        house_id = self.forwarded.get('house', None)
        if house_id:
            qs = qs.filter(house_id=house_id)

        # Поиск по номеру строения
        if self.q:
            qs = qs.filter(number__icontains=self.q)

        return qs.order_by('house__street__name', 'house__number', 'number')

    def get_result_label(self, result):
        """Форматирование строения для отображения."""
        return f"{result.house.street}, д. {result.house.number}, стр. {result.number}"


# ====================================================================================
# МОДУЛЬ 2: КЛАССЫ ФИЛЬТРОВ ДЛЯ АДМИНКИ
# ====================================================================================

class CountryFilter(SimpleListFilter):
    """
    ФИЛЬТР ПО СТРАНЕ для связанных моделей.

    ИСПОЛЬЗУЕТСЯ В:
        • Федеральных округах
        • Регионах
        • Городах
        • Адресах
    """

    title = 'Страна'
    parameter_name = 'country'

    def lookups(self, request, model_admin):
        """
        ВОЗВРАЩАЕТ СПИСОК ВАРИАНТОВ ДЛЯ ФИЛЬТРА.

        ВОЗВРАЩАЕТ:
            list: Список кортежей (id, name) стран
        """
        countries = Country.objects.all().order_by('name')
        return [(country.id, country.name) for country in countries]

    def queryset(self, request, queryset):
        """
        ФИЛЬТРАЦИЯ QUERYSET ПО ВЫБРАННОЙ СТРАНЕ.

        ВОЗВРАЩАЕТ:
            QuerySet: Отфильтрованный queryset
        """
        if self.value():
            # Для каждой модели свой способ фильтрации по стране
            if hasattr(queryset.model, 'country'):
                return queryset.filter(country_id=self.value())
            elif hasattr(queryset.model, 'federal_district'):
                return queryset.filter(federal_district__country_id=self.value())
            elif hasattr(queryset.model, 'region'):
                return queryset.filter(region__federal_district__country_id=self.value())
            elif hasattr(queryset.model, 'city'):
                return queryset.filter(city__region__federal_district__country_id=self.value())
            elif hasattr(queryset.model, 'street'):
                return queryset.filter(street__city__region__federal_district__country_id=self.value())
        return queryset


class RegionFilter(SimpleListFilter):
    """ФИЛЬТР ПО РЕГИОНУ."""

    title = 'Регион'
    parameter_name = 'region'

    def lookups(self, request, model_admin):
        regions = Region.objects.all().order_by('name')
        return [(region.id, str(region)) for region in regions]

    def queryset(self, request, queryset):
        if self.value():
            if hasattr(queryset.model, 'region'):
                return queryset.filter(region_id=self.value())
            elif hasattr(queryset.model, 'city'):
                return queryset.filter(city__region_id=self.value())
            elif hasattr(queryset.model, 'street'):
                return queryset.filter(street__city__region_id=self.value())
        return queryset


class CityFilter(SimpleListFilter):
    """ФИЛЬТР ПО ГОРОДУ."""

    title = 'Город'
    parameter_name = 'city'

    def lookups(self, request, model_admin):
        cities = City.objects.all().order_by('name')
        return [(city.id, str(city)) for city in cities]

    def queryset(self, request, queryset):
        if self.value():
            if hasattr(queryset.model, 'city'):
                return queryset.filter(city_id=self.value())
            elif hasattr(queryset.model, 'street'):
                return queryset.filter(street__city_id=self.value())
        return queryset


# ====================================================================================
# МОДУЛЬ 3: КЛАССЫ MODELADMIN ДЛЯ ВСЕХ МОДЕЛЕЙ
# ====================================================================================

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ СТРАНАМИ.

    НАСТРОЙКИ:
        • Отображение: название страны
        • Поиск: по названию страны
        • Сортировка: по названию
        • Фильтры: нет

    ОСОБЕННОСТИ:
        • Базовая модель, не имеет зависимостей
        • Простой интерфейс управления
    """

    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

    # GIN индексы уже созданы в модели
    # Django автоматически использует их для поиска


@admin.register(FederalDistrict)
class FederalDistrictAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ФЕДЕРАЛЬНЫМИ ОКРУГАМИ.

    НАСТРОЙКИ:
        • Отображение: название, сокращение, страна
        • Поиск: по названию и сокращению
        • Фильтры: по стране
        • Autocomplete: для поля country

    ОСОБЕННОСТИ:
        • Использует autocomplete для выбора страны
        • Фильтрация по стране
        • Отображение связанной страны
    """

    list_display = ('name', 'abbreviated_name', 'country')
    search_fields = ('name', 'abbreviated_name')
    list_filter = (CountryFilter,)
    autocomplete_fields = ('country',)
    ordering = ('country__name', 'name')

    def get_queryset(self, request):
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related('country')


@admin.register(TypeRegion)
class TypeRegionAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ТИПАМИ РЕГИОНОВ.

    НАСТРОЙКИ:
        • Отображение: название, сокращение, правила отображения
        • Поиск: по названию и сокращению
        • Фильтры: по правилам отображения
    """

    list_display = ('name', 'abbreviated_name', 'show_before_name', 'skip_in_name')
    search_fields = ('name', 'abbreviated_name')
    list_filter = ('show_before_name', 'skip_in_name')
    ordering = ('name',)


@admin.register(Timezone)
class TimezoneAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ЧАСОВЫМИ ПОЯСАМИ.

    НАСТРОЙКИ:
        • Отображение: название, смещения UTC и Москвы
        • Поиск: по названию
        • Сортировка: по смещению UTC
    """

    list_display = ('name', 'offset_utc', 'offset_moscow')
    search_fields = ('name',)
    ordering = ('offset_utc', 'name')

    def offset_utc(self, obj):
        """Форматирование смещения UTC."""
        return f"UTC{obj.offset_utc:+d}"

    def offset_moscow(self, obj):
        """Форматирование смещения относительно Москвы."""
        return f"МСК{obj.offset_moscow:+d}"

    offset_utc.short_description = 'Смещение UTC'
    offset_moscow.short_description = 'Смещение МСК'


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ РЕГИОНАМИ.

    НАСТРОЙКИ:
        • Отображение: название, тип, федеральный округ
        • Поиск: по названию и сокращению
        • Фильтры: по федеральному округу, типу региона, часовому поясу
        • Autocomplete: для всех связанных полей

    ОСОБЕННОСТИ:
        • Использует autocomplete для зависимых полей
        • Отображает форматированное название региона
        • Поддерживает фильтрацию по всем связанным моделям
    """

    list_display = ('get_display_name', 'type_region', 'federal_district', 'timezone')
    search_fields = ('name', 'abbreviated_name')
    list_filter = ('federal_district', 'type_region', 'timezone')
    autocomplete_fields = ('federal_district', 'type_region', 'timezone')
    ordering = ('federal_district__name', 'name')

    def get_display_name(self, obj):
        """Форматированное название региона для отображения."""
        return str(obj)

    get_display_name.short_description = 'Регион'
    get_display_name.admin_order_field = 'name'

    def get_queryset(self, request):
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related(
            'federal_district', 'type_region', 'timezone'
        )


@admin.register(LocalityType)
class LocalityTypeAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ТИПАМИ НАСЕЛЕННЫХ ПУНКТОВ.

    НАСТРОЙКИ:
        • Отображение: название, сокращение, правила отображения
        • Поиск: по названию и сокращению
        • Фильтры: по наличию административных округов
    """

    list_display = ('name', 'abbreviated_name', 'show_before_name', 'has_administrative_territory')
    search_fields = ('name', 'abbreviated_name')
    list_filter = ('show_before_name', 'has_administrative_territory')
    ordering = ('name',)


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ГОРОДАМИ.

    НАСТРОЙКИ:
        • Отображение: название, тип, регион
        • Поиск: по названию города
        • Фильтры: по региону, типу населенного пункта, часовому поясу
        • Autocomplete: для всех связанных полей
    """

    list_display = ('get_display_name', 'locality_type', 'region', 'timezone')
    search_fields = ('name',)
    list_filter = (RegionFilter, 'locality_type', 'timezone', 'has_administrative_territory')
    autocomplete_fields = ('region', 'locality_type', 'timezone')
    ordering = ('region__name', 'name')

    def get_display_name(self, obj):
        """Форматированное название города для отображения."""
        return str(obj)

    get_display_name.short_description = 'Город'
    get_display_name.admin_order_field = 'name'

    def get_queryset(self, request):
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related(
            'region', 'locality_type', 'timezone'
        )


@admin.register(AdministrativeTerritory)
class AdministrativeTerritoryAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТИВНЫМИ ОКРУГАМИ.

    НАСТРОЙКИ:
        • Отображение: название, город
        • Поиск: по названию округа
        • Фильтры: по городу
        • Autocomplete: для поля city
    """

    list_display = ('name', 'city')
    search_fields = ('name',)
    list_filter = (CityFilter,)
    autocomplete_fields = ('city',)
    ordering = ('city__name', 'name')

    def get_queryset(self, request):
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related('city')


@admin.register(AdministrativeTerritorialUnit)
class AdministrativeUnitAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНЫМИ ЕДИНИЦАМИ.

    НАСТРОЙКИ:
        • Отображение: название, город, административный округ
        • Поиск: по названию АТЕ
        • Фильтры: по городу, административному округу
        • Autocomplete: для всех связанных полей
    """

    list_display = ('name', 'city', 'administrative_territory')
    search_fields = ('name',)
    list_filter = (CityFilter, 'administrative_territory')
    autocomplete_fields = ('city', 'administrative_territory')
    ordering = ('city__name', 'name')

    def get_queryset(self, request):
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related(
            'city', 'administrative_territory'
        )


@admin.register(StreetType)
class StreetTypeAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ТИПАМИ УЛИЦ.

    НАСТРОЙКИ:
        • Отображение: название, сокращение, правило отображения
        • Поиск: по названию и сокращению
        • Фильтры: по правилу отображения
    """

    list_display = ('name', 'abbreviated_name', 'show_before_name')
    search_fields = ('name', 'abbreviated_name')
    list_filter = ('show_before_name',)
    ordering = ('name',)


@admin.register(Street)
class StreetAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ УЛИЦАМИ.

    НАСТРОЙКИ:
        • Отображение: название, тип, город
        • Поиск: по названию улицы
        • Фильтры: по городу, типу улицы
        • Autocomplete: для всех связанных полей
    """

    list_display = ('get_display_name', 'street_type', 'city')
    search_fields = ('name',)
    list_filter = (CityFilter, 'street_type')
    autocomplete_fields = ('city', 'street_type')
    ordering = ('city__name', 'name')

    def get_display_name(self, obj):
        """Форматированное название улицы для отображения."""
        return str(obj)

    get_display_name.short_description = 'Улица'
    get_display_name.admin_order_field = 'name'

    def get_queryset(self, request):
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related('city', 'street_type')


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ ДОМАМИ.

    НАСТРОЙКИ:
        • Отображение: номер, улица, город
        • Поиск: по номеру дома
        • Фильтры: по улице
        • Autocomplete: для поля street
    """

    list_display = ('number', 'street', 'get_city')
    search_fields = ('number',)
    list_filter = ('street',)
    autocomplete_fields = ('street',)
    ordering = ('street__name', 'number')

    def get_city(self, obj):
        """Город для отображения (вычисляемое поле)."""
        return obj.street.city

    get_city.short_description = 'Город'
    get_city.admin_order_field = 'street__city__name'

    def get_queryset(self, request):
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related('street', 'street__city')


@admin.register(Building)
class BuildingAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ СТРОЕНИЯМИ.

    НАСТРОЙКИ:
        • Отображение: номер, дом, улица
        • Поиск: по номеру строения
        • Фильтры: по дому
        • Autocomplete: для поля house
    """

    list_display = ('number', 'house', 'get_street', 'get_city')
    search_fields = ('number',)
    list_filter = ('house',)
    autocomplete_fields = ('house',)
    ordering = ('house__street__name', 'house__number', 'number')

    def get_street(self, obj):
        """Улица для отображения (вычисляемое поле)."""
        return obj.house.street

    def get_city(self, obj):
        """Город для отображения (вычисляемое поле)."""
        return obj.house.street.city

    get_street.short_description = 'Улица'
    get_street.admin_order_field = 'house__street__name'

    get_city.short_description = 'Город'
    get_city.admin_order_field = 'house__street__city__name'

    def get_queryset(self, request):
        """Оптимизация запроса с select_related."""
        return super().get_queryset(request).select_related(
            'house', 'house__street', 'house__street__city'
        )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """
    АДМИНИСТРАТИВНЫЙ КЛАСС ДЛЯ УПРАВЛЕНИЯ АДРЕСАМИ.

    НАСТРОЙКИ:
        • Отображение: полный адрес, страна, регион, город, улица, дом, строение, индекс
        • Поиск: по всем компонентам адреса
        • Фильтры: по всем связанным моделям
        • Autocomplete: для всех связанных полей
        • Readonly: вычисляемое поле full_address

    ОСОБЕННОСТИ:
        • Отображает полный адрес в удобном формате
        • Поддерживает сложную фильтрацию по всем компонентам
        • Использует autocomplete для улучшения UX
        • Оптимизированные запросы с select_related
    """

    # Поля для отображения в списке
    list_display = (
        'full_address_display',
        'country',
        'region',
        'city',
        'street',
        'house',
        'building',
        'index'
    )

    # Поля для поиска
    search_fields = (
        'country__name',
        'region__name',
        'city__name',
        'administrative_territory__name',
        'administrative_unit__name',
        'street__name',
        'house__number',
        'building__number',
        'microdistrict',
        'index'
    )

    # Фильтры
    list_filter = (
        CountryFilter,
        'federal_district',
        RegionFilter,
        CityFilter,
        'administrative_territory',
        'administrative_unit',
        'street',
        'house',
        'building',
    )

    # Поля с autocomplete
    autocomplete_fields = (
        'country',
        'federal_district',
        'region',
        'city',
        'administrative_territory',
        'administrative_unit',
        'street',
        'house',
        'building'
    )

    # Только для чтения
    readonly_fields = ('full_address',)

    # Сортировка
    ordering = (
        'country__name',
        'region__name',
        'city__name',
        'street__name',
        'house__number',
        'building__number'
    )

    # Группировка полей в форме
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'country',
                'federal_district',
                'region',
                'city',
                'full_address'
            )
        }),
        ('Административное деление', {
            'fields': (
                'administrative_territory',
                'administrative_unit',
            ),
            'classes': ('collapse',)
        }),
        ('Улично-домовая сеть', {
            'fields': (
                'street',
                'house',
                'building',
            )
        }),
        ('Дополнительная информация', {
            'fields': (
                'microdistrict',
                'index',
                'coordinates',
            ),
            'classes': ('collapse',)
        }),
    )

    def full_address_display(self, obj):
        """
        ОТОБРАЖЕНИЕ ПОЛНОГО АДРЕСА В СПИСКЕ.

        АРГУМЕНТЫ:
            obj : Address
                Объект адреса

        ВОЗВРАЩАЕТ:
            str: Отформатированный полный адрес
        """
        return obj.full_address

    full_address_display.short_description = 'Полный адрес'
    full_address_display.admin_order_field = 'city__name'

    def get_queryset(self, request):
        """
        ОПТИМИЗАЦИЯ ЗАПРОСА ДЛЯ АДРЕСОВ.

        ИСПОЛЬЗУЕТ select_related для всех связанных моделей
        чтобы избежать N+1 проблем при отображении списка.
        """
        return super().get_queryset(request).select_related(
            'country',
            'federal_district',
            'region',
            'city',
            'administrative_territory',
            'administrative_unit',
            'street',
            'house',
            'building'
        )

    def save_model(self, request, obj, form, change):
        """
        СОХРАНЕНИЕ МОДЕЛИ АДРЕСА С ДОПОЛНИТЕЛЬНОЙ ОБРАБОТКОЙ.

        ДЕЙСТВИЯ:
            1. Автоматическое заполнение недостающих полей из иерархии
            2. Проверка существования такого же адреса
            3. Вызов родительского метода сохранения

        АРГУМЕНТЫ:
            request : HttpRequest
                Запрос

            obj : Address
                Объект адреса

            form : Form
                Форма

            change : bool
                Флаг изменения (True) или создания (False)
        """
        # Автоматически заполняем недостающие поля из иерархии
        if obj.region and not obj.country:
            obj.country = obj.region.federal_district.country

        if obj.region and not obj.federal_district:
            obj.federal_district = obj.region.federal_district

        if obj.city and not obj.region:
            obj.region = obj.city.region

        if obj.street and not obj.city:
            obj.city = obj.street.city

        if obj.house and not obj.street:
            obj.street = obj.house.street

        if obj.building and not obj.house:
            obj.house = obj.building.house

        # Проверяем существование такого же адреса
        if not change:  # Только при создании
            existing = obj._find_existing_address()
            if existing:
                # Если нашли существующий, можно показать сообщение
                # или выполнить другие действия
                pass

        super().save_model(request, obj, form, change)

    def full_address(self, obj):
        """
        ОТОБРАЖЕНИЕ ПОЛНОГО АДРЕСА В ФОРМЕ РЕДАКТИРОВАНИЯ.

        АРГУМЕНТЫ:
            obj : Address
                Объект адреса

        ВОЗВРАЩАЕТ:
            str: Отформатированный полный адрес
        """
        return format_html('<strong>{}</strong>', obj.full_address)

    full_address.short_description = 'Полный адрес (автоматически)'