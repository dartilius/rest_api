"""
Сериализаторы для справочника адресов.

МОДУЛЬ СЕРИАЛИЗАТОРОВ:
─────────────────────────────────────────────────────────────────────────────────────
Этот модуль содержит все сериализаторы для работы с моделями адресов через Django REST Framework.
Сериализаторы обеспечивают преобразование между объектами Python и форматами данных (JSON, XML).

СТРУКТУРА СЕРИАЛИЗАТОРОВ:
─────────────────────────────────────────────────────────────────────────────────────
1. Базовые сериализаторы для чтения (Read-Only)
   • CountrySerializer, FederalDistrictSerializer, TypeRegionSerializer и т.д.
   • Используются для отображения данных в API

2. Вложенные сериализаторы для создания (Nested Serializers)
   • NestedCountrySerializer, NestedFederalDistrictSerializer и т.д.
   • Используются для обработки вложенных структур при создании адреса
   • Автоматически создают или находят существующие объекты

3. Основные сериализаторы для адреса
   • AddressReadSerializer - для чтения полного адреса
   • AddressCreateSerializer - для создания адреса с вложенной структурой

ОСОБЕННОСТИ:
• Использование get_or_create для избежания дублирования
• Контекстная передача зависимых объектов
• Гибкая валидация иерархии адресов
• Поддержка как создания новых объектов, так и использования существующих
"""

from rest_framework import serializers
from .models import (
    Country, FederalDistrict, TypeRegion, Timezone, Region,
    LocalityType, City, AdministrativeTerritory,
    AdministrativeTerritorialUnit, StreetType, Street,
    House, Building, Address, Coordinates
)


# ====================================================================================
# МОДУЛЬ 1: БАЗОВЫЕ СЕРИАЛИЗАТОРЫ ДЛЯ ЧТЕНИЯ
# ====================================================================================

class CountrySerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ СТРАНЫ.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения списка стран в API
        • Представления страны в составе адреса
        • Поиска и фильтрации стран

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор страны

        name : string
            Название страны

    ПРИМЕР ВЫВОДА JSON:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "Россия"
        }
    """

    class Meta:
        model = Country
        fields = ['id', 'name']
        read_only_fields = ['id']


class FederalDistrictSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ ФЕДЕРАЛЬНОГО ОКРУГА.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения федеральных округов
        • Вложенного представления в регионе

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Название федерального округа

        abbreviated_name : string
            Сокращенное название

        country : UUID (только для чтения)
            Идентификатор страны
    """

    country = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = FederalDistrict
        fields = ['id', 'name', 'abbreviated_name', 'country']
        read_only_fields = ['id']


class TypeRegionSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ ТИПА РЕГИОНА.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения типов регионов
        • Настройки отображения регионов

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Тип региона

        abbreviated_name : string
            Сокращенное название

        show_before_name : boolean
            Показывать ли тип перед названием

        skip_in_name : boolean
            Пропускать ли тип в названии
    """

    class Meta:
        model = TypeRegion
        fields = ['id', 'name', 'abbreviated_name', 'show_before_name', 'skip_in_name']
        read_only_fields = ['id']


class TimezoneSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ ЧАСОВОГО ПОЯСА.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения часовых поясов
        • Выбора часового пояса для региона/города

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Наименование часового пояса

        offset_utc : integer
            Смещение относительно UTC

        offset_moscow : integer
            Смещение относительно Москвы
    """

    class Meta:
        model = Timezone
        fields = ['id', 'name', 'offset_utc', 'offset_moscow']
        read_only_fields = ['id']


class RegionSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ РЕГИОНА.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения списка регионов
        • Вложенного представления в городе

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Наименование региона

        abbreviated_name : string
            Сокращенное наименование

        federal_district : UUID
            Идентификатор федерального округа

        type_region : UUID
            Идентификатор типа региона

        timezone : UUID (опционально)
            Идентификатор часового пояса
    """

    federal_district = serializers.PrimaryKeyRelatedField(read_only=True)
    type_region = serializers.PrimaryKeyRelatedField(read_only=True)
    timezone = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Region
        fields = [
            'id', 'name', 'abbreviated_name',
            'federal_district', 'type_region', 'timezone'
        ]
        read_only_fields = ['id']


class LocalityTypeSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ ТИПА НАСЕЛЕННОГО ПУНКТА.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения типов населенных пунктов
        • Настройки отображения городов

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Тип населённого пункта

        abbreviated_name : string
            Сокращённое наименование

        show_before_name : boolean
            Отображать ли тип до наименования

        has_administrative_territory : boolean
            Имеет ли административный округ
    """

    class Meta:
        model = LocalityType
        fields = [
            'id', 'name', 'abbreviated_name',
            'show_before_name', 'has_administrative_territory'
        ]
        read_only_fields = ['id']


class CitySerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ ГОРОДА.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения списка городов
        • Вложенного представления в адресе

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Наименование города

        region : UUID
            Идентификатор региона

        locality_type : UUID
            Идентификатор типа населенного пункта

        timezone : UUID (опционально)
            Идентификатор часового пояса
    """

    region = serializers.PrimaryKeyRelatedField(read_only=True)
    locality_type = serializers.PrimaryKeyRelatedField(read_only=True)
    timezone = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    nomenclature_count = serializers.IntegerField(read_only=True, default=0)
    class Meta:
        model = City
        fields = [
            'id', 'name', 'region',
            'locality_type', 'timezone',
            'slug', 'nomenclature_count'
        ]
        read_only_fields = ['id']


class AdministrativeTerritorySerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ АДМИНИСТРАТИВНОГО ОКРУГА.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения административных округов
        • Вложенного представления в адресе

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Административный округ

        city : UUID
            Идентификатор города
    """

    city = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AdministrativeTerritory
        fields = ['id', 'name', 'city']
        read_only_fields = ['id']


class AdministrativeUnitSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНОЙ ЕДИНИЦЫ.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения районов/округов
        • Вложенного представления в адресе

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Район / округ

        city : UUID
            Идентификатор города

        administrative_territory : UUID (опционально)
            Идентификатор административного округа
    """

    city = serializers.PrimaryKeyRelatedField(read_only=True)
    administrative_territory = serializers.PrimaryKeyRelatedField(
        read_only=True, allow_null=True
    )

    class Meta:
        model = AdministrativeTerritorialUnit
        fields = ['id', 'name', 'city', 'administrative_territory']
        read_only_fields = ['id']


class StreetTypeSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ ТИПА УЛИЦЫ.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения типов улиц
        • Настройки отображения улиц

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Тип улицы

        abbreviated_name : string
            Сокращённое наименование

        show_before_name : boolean
            Отображать ли тип до наименования
    """

    class Meta:
        model = StreetType
        fields = ['id', 'name', 'abbreviated_name', 'show_before_name']
        read_only_fields = ['id']


class StreetSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ УЛИЦЫ.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения списка улиц
        • Вложенного представления в адресе

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        name : string
            Наименование улицы

        city : UUID
            Идентификатор города

        street_type : UUID (опционально)
            Идентификатор типа улицы
    """

    city = serializers.PrimaryKeyRelatedField(read_only=True)
    street_type = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Street
        fields = ['id', 'name', 'city', 'street_type']
        read_only_fields = ['id']


class HouseSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ ДОМА.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения домов на улице
        • Вложенного представления в адресе

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        number : string
            Номер дома

        street : UUID
            Идентификатор улицы
    """

    street = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = House
        fields = ['id', 'number', 'street']
        read_only_fields = ['id']


class BuildingSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ СТРОЕНИЯ.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения строений/корпусов
        • Вложенного представления в адресе

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        number : string
            Корпус / строение

        house : UUID
            Идентификатор дома
    """

    house = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Building
        fields = ['id', 'number', 'house']
        read_only_fields = ['id']



class CoordinatesSerializers(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ КООРДИНАТ.

    ИСПОЛЬЗУЕТСЯ ДЛЯ:
        • Отображения Координат

    ПОЛЯ:
        id : UUID
            Уникальный идентификатор

        latitude : string
            Обозначение Широты

        longitude : string
            Обозначение Долготы
    """

    class Meta:
        model = Coordinates
        fields = ['id', 'latitude', 'longitude']
        read_only_fields = ['id']


# ====================================================================================
# МОДУЛЬ 2: ВЛОЖЕННЫЕ СЕРИАЛИЗАТОРЫ ДЛЯ СОЗДАНИЯ
# ====================================================================================

class NestedCountrySerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ СТРАНЫ.

    ОСОБЕННОСТИ:
        • Отключает валидацию уникальности (для использования get_or_create)
        • Автоматически находит существующую страну или создает новую
        • Используется только в контексте создания адреса

    ПОЛЯ ДЛЯ СОЗДАНИЯ:
        name : string (обязательно)
            Название страны

    ЛОГИКА СОЗДАНИЯ:
        1. Ищет страну по названию
        2. Если находит - возвращает существующую
        3. Если не находит - создает новую

    ПРИМЕР ИСПОЛЬЗОВАНИЯ:
        {
            "name": "Россия"
        }
    """

    class Meta:
        model = Country
        fields = ['name']
        extra_kwargs = {
            'name': {'validators': []}  # Отключаем валидацию уникальности
        }

    def create(self, validated_data):
        """
        СОЗДАНИЕ ИЛИ ПОЛУЧЕНИЕ СУЩЕСТВУЮЩЕЙ СТРАНЫ.

        АЛГОРИТМ:
            1. Получаем название страны из validated_data
            2. Ищем страну с таким названием
            3. Если находим - возвращаем существующую
            4. Если не находим - создаем новую

        АРГУМЕНТЫ:
            validated_data : dict
                Валидированные данные из запроса

        ВОЗВРАЩАЕТ:
            Country : Объект страны

        ИСКЛЮЧЕНИЯ:
            serializers.ValidationError: Если название страны не указано
        """
        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название страны обязательно для создания'
            })

        # Используем get_or_create для избежания дублирования
        country, created = Country.objects.get_or_create(
            name=name,
            defaults=validated_data
        )

        return country


class NestedFederalDistrictSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ ФЕДЕРАЛЬНОГО ОКРУГА.

    ОСОБЕННОСТИ:
        • Требует страну в контексте
        • Автоматически связывает с переданной страной
        • Ищет существующий федеральный округ в рамках страны

    ПОЛЯ ДЛЯ СОЗДАНИЯ:
        name : string (обязательно)
            Название федерального округа

        abbreviated_name : string (обязательно)
            Сокращенное название

    КОНТЕКСТ:
        • country: объект Country (обязательно)
    """

    class Meta:
        model = FederalDistrict
        fields = ['name', 'abbreviated_name']
        extra_kwargs = {
            'name': {'validators': []},
            'abbreviated_name': {'validators': []}
        }

    def create(self, validated_data):
        """
        СОЗДАНИЕ ИЛИ ПОЛУЧЕНИЕ ФЕДЕРАЛЬНОГО ОКРУГА.

        ТРЕБОВАНИЯ:
            • В контексте должна быть передана страна
            • Федеральный округ создается только для России

        АЛГОРИТМ:
            1. Получаем страну из контекста
            2. Проверяем, что страна - Россия
            3. Ищем федеральный округ в рамках страны
            4. Создаем новый если не нашли

        ВОЗВРАЩАЕТ:
            FederalDistrict : Объект федерального округа

        ИСКЛЮЧЕНИЯ:
            serializers.ValidationError: Если страна не указана или не Россия
        """
        country = self.context.get('country')

        if not country:
            raise serializers.ValidationError({
                'country': 'Страна обязательна для создания федерального округа'
            })

        if country.name != "Россия":
            raise serializers.ValidationError({
                'country': 'Федеральные округа существуют только в России'
            })

        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название федерального округа обязательно'
            })

        # Ищем существующий федеральный округ в рамках страны
        federal_district, created = FederalDistrict.objects.get_or_create(
            country=country,
            name=name,
            defaults={
                **validated_data,
                'country': country
            }
        )

        return federal_district


class NestedTypeRegionSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ ТИПА РЕГИОНА.

    ПОЛЯ ДЛЯ СОЗДАНИЯ:
        name : string (обязательно)
            Тип региона

        abbreviated_name : string
            Сокращенное название

        show_before_name : boolean
            Показывать ли тип перед названием

        skip_in_name : boolean
            Пропускать ли тип в названии
    """

    class Meta:
        model = TypeRegion
        fields = ['name', 'abbreviated_name', 'show_before_name', 'skip_in_name']
        extra_kwargs = {
            'name': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение типа региона."""
        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название типа региона обязательно'
            })

        type_region, created = TypeRegion.objects.get_or_create(
            name=name,
            defaults=validated_data
        )

        return type_region


class NestedRegionSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ РЕГИОНА.

    ТРЕБОВАНИЯ:
        • В контексте должны быть переданы федеральный округ и тип региона

    ПОЛЯ ДЛЯ СОЗДАНИЯ:
        name : string (обязательно)
            Наименование региона

        abbreviated_name : string
            Сокращенное наименование
    """

    class Meta:
        model = Region
        fields = ['name', 'abbreviated_name']
        extra_kwargs = {
            'name': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение региона."""
        federal_district = self.context.get('federal_district')
        type_region = self.context.get('type_region')

        if not federal_district:
            raise serializers.ValidationError({
                'federal_district': 'Федеральный округ обязателен для создания региона'
            })

        if not type_region:
            raise serializers.ValidationError({
                'type_region': 'Тип региона обязателен для создания региона'
            })

        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название региона обязательно'
            })

        # Ищем регион в рамках федерального округа
        region, created = Region.objects.get_or_create(
            federal_district=federal_district,
            name=name,
            defaults={
                **validated_data,
                'federal_district': federal_district,
                'type_region': type_region
            }
        )

        return region


class NestedLocalityTypeSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ ТИПА НАСЕЛЕННОГО ПУНКТА.
    """

    class Meta:
        model = LocalityType
        fields = ['name', 'abbreviated_name', 'show_before_name', 'has_administrative_territory']
        extra_kwargs = {
            'name': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение типа населенного пункта."""
        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название типа населенного пункта обязательно'
            })

        locality_type, created = LocalityType.objects.get_or_create(
            name=name,
            defaults=validated_data
        )

        return locality_type


class NestedCitySerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ ГОРОДА.

    ТРЕБОВАНИЯ:
        • В контексте должен быть передан регион
        • Тип населенного пункта может быть передан в контексте или данных
    """

    class Meta:
        model = City
        fields = ['name']
        extra_kwargs = {
            'name': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение города."""
        region = self.context.get('region')
        locality_type = self.context.get('locality_type')

        if not region:
            raise serializers.ValidationError({
                'region': 'Регион обязателен для создания города'
            })

        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название города обязательно'
            })

        # Ищем город в рамках региона
        city, created = City.objects.get_or_create(
            region=region,
            name=name,
            defaults={
                **validated_data,
                'region': region,
                'locality_type': locality_type
            }
        )

        return city


class NestedAdministrativeTerritorySerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ АДМИНИСТРАТИВНОГО ОКРУГА.

    ТРЕБОВАНИЯ:
        • В контексте должен быть передан город
        • Город должен иметь has_administrative_territory=True
    """

    class Meta:
        model = AdministrativeTerritory
        fields = ['name']
        extra_kwargs = {
            'name': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение административного округа."""
        city = self.context.get('city')

        if not city:
            raise serializers.ValidationError({
                'city': 'Город обязателен для создания административного округа'
            })

        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название административного округа обязательно'
            })

        administrative_territory, created = AdministrativeTerritory.objects.get_or_create(
            city=city,
            name=name,
            defaults={
                **validated_data,
                'city': city
            }
        )

        return administrative_territory


class NestedAdministrativeUnitSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ АДМИНИСТРАТИВНО-ТЕРРИТОРИАЛЬНОЙ ЕДИНИЦЫ.

    ТРЕБОВАНИЯ:
        • В контексте должен быть передан город
        • Административный округ может быть передан в контексте
    """

    class Meta:
        model = AdministrativeTerritorialUnit
        fields = ['name']
        extra_kwargs = {
            'name': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение административно-территориальной единицы."""
        city = self.context.get('city')
        administrative_territory = self.context.get('administrative_territory')

        if not city:
            raise serializers.ValidationError({
                'city': 'Город обязателен для создания АТЕ'
            })

        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название АТЕ обязательно'
            })

        administrative_unit, created = AdministrativeTerritorialUnit.objects.get_or_create(
            city=city,
            name=name,
            defaults={
                **validated_data,
                'city': city,
                'administrative_territory': administrative_territory
            }
        )

        return administrative_unit


class NestedStreetTypeSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ ТИПА УЛИЦЫ.
    """

    class Meta:
        model = StreetType
        fields = ['name', 'abbreviated_name', 'show_before_name']
        extra_kwargs = {
            'name': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение типа улицы."""
        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название типа улицы обязательно'
            })

        street_type, created = StreetType.objects.get_or_create(
            name=name,
            defaults=validated_data
        )

        return street_type


class NestedStreetSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ УЛИЦЫ.

    ТРЕБОВАНИЯ:
        • В контексте должен быть передан город
        • Тип улицы может быть передан в контексте
    """

    class Meta:
        model = Street
        fields = ['name']
        extra_kwargs = {
            'name': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение улицы."""
        city = self.context.get('city')
        street_type = self.context.get('street_type')

        if not city:
            raise serializers.ValidationError({
                'city': 'Город обязателен для создания улицы'
            })

        name = validated_data.get('name')

        if not name:
            raise serializers.ValidationError({
                'name': 'Название улицы обязательно'
            })

        street, created = Street.objects.get_or_create(
            city=city,
            name=name,
            defaults={
                **validated_data,
                'city': city,
                'street_type': street_type
            }
        )

        return street


class NestedHouseSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ ДОМА.

    ТРЕБОВАНИЯ:
        • В контексте должна быть передана улица
    """

    class Meta:
        model = House
        fields = ['number']
        extra_kwargs = {
            'number': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение дома."""
        street = self.context.get('street')

        if not street:
            raise serializers.ValidationError({
                'street': 'Улица обязательна для создания дома'
            })

        number = validated_data.get('number')

        if not number:
            raise serializers.ValidationError({
                'number': 'Номер дома обязателен'
            })

        house, created = House.objects.get_or_create(
            street=street,
            number=number,
            defaults={
                **validated_data,
                'street': street
            }
        )

        return house


class NestedBuildingSerializer(serializers.ModelSerializer):
    """
    ВЛОЖЕННЫЙ СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ СТРОЕНИЯ.

    ТРЕБОВАНИЯ:
        • В контексте должен быть передан дом
    """

    class Meta:
        model = Building
        fields = ['number']
        extra_kwargs = {
            'number': {'validators': []}
        }

    def create(self, validated_data):
        """Создание или получение строения."""
        house = self.context.get('house')

        if not house:
            raise serializers.ValidationError({
                'house': 'Дом обязателен для создания строения'
            })

        number = validated_data.get('number')

        if not number:
            raise serializers.ValidationError({
                'number': 'Номер строения обязателен'
            })

        building, created = Building.objects.get_or_create(
            house=house,
            number=number,
            defaults={
                **validated_data,
                'house': house
            }
        )

        return building


class NestedCoordinatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coordinates
        fields = ['latitude', 'longitude']
        extra_kwargs = {
            'latitude': {'required': False},
            'longitude': {'required': False},
        }

    def validate(self, data):
        """
        Кастомная валидация: если указана одна координата,
        должна быть и вторая.
        """
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        # Если указана широта, но нет долготы
        if latitude and not longitude:
            raise serializers.ValidationError({
                'longitude': 'Если указана широта, должна быть и долгота'
            })

        # Если указана долгота, но нет широты
        if longitude and not latitude:
            raise serializers.ValidationError({
                'latitude': 'Если указана долгота, должна быть и широта'
            })

        return data


# ====================================================================================
# МОДУЛЬ 3: ОСНОВНЫЕ СЕРИАЛИЗАТОРЫ ДЛЯ АДРЕСА
# ====================================================================================

class AddressCreateSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ СОЗДАНИЯ АДРЕСА С ВЛОЖЕННОЙ СТРУКТУРОЙ.

    ОПИСАНИЕ:
        Позволяет создавать полный адрес с глубоко вложенной структурой.
        Автоматически создает или находит все связанные объекты.
        Поддерживает как создание новых объектов, так и использование существующих.

    ОСОБЕННОСТИ:
        • Автоматическое создание иерархии объектов
        • Использование get_or_create для избежания дублирования
        • Проверка целостности иерархии
        • Автоматическое заполнение недостающих полей

    ПОЛЯ ДЛЯ СОЗДАНИЯ:
        • Поля самого адреса (microdistrict, index, latitude, longitude)
        • Вложенные сериализаторы для всех компонентов адреса
        • Каждый компонент является необязательным

    СТРУКТУРА ЗАПРОСА JSON:
        {
            "country": {"name": "Россия"},
            "federal_district": {"name": "ЦФО", "abbreviated_name": "ЦФО"},
            "type_region": {"name": "область", "abbreviated_name": "обл."},
            "region": {"name": "Московская"},
            "locality_type": {"name": "город", "abbreviated_name": "г."},
            "city": {"name": "Москва"},
            "street": {"name": "Ленина"},
            "street_type": {"name": "улица", "abbreviated_name": "ул."},
            "house": {"number": "1"},
            "building": {"number": "А"},
            "microdistrict": "Центральный",
            "index": "101000",
            "latitude": "55.7558
            "longitude":"37.6173"
        }
    """

    # Вложенные сериализаторы для всех компонентов адреса
    country = NestedCountrySerializer(required=False)
    federal_district = NestedFederalDistrictSerializer(required=False)
    type_region = NestedTypeRegionSerializer(required=False)
    region = NestedRegionSerializer(required=False)
    locality_type = NestedLocalityTypeSerializer(required=False)
    city = NestedCitySerializer(required=False)
    administrative_territory = NestedAdministrativeTerritorySerializer(required=False)
    administrative_unit = NestedAdministrativeUnitSerializer(required=False)
    street_type = NestedStreetTypeSerializer(required=False)
    street = NestedStreetSerializer(required=False)
    house = NestedHouseSerializer(required=False)
    building = NestedBuildingSerializer(required=False)
    coordinates = NestedCoordinatesSerializer(required=False)

    class Meta:
        model = Address
        fields = [
            'id',
            # Компоненты адреса
            'country', 'federal_district', 'type_region', 'region',
            'locality_type', 'city', 'administrative_territory', 'administrative_unit',
            'street_type', 'street', 'house', 'building', 'coordinates',
            # Дополнительные поля
            'microdistrict', 'index',
        ]
        read_only_fields = ['id']

    def create(self, validated_data):
        """
        СОЗДАНИЕ АДРЕСА С ВЛОЖЕННОЙ СТРУКТУРОЙ.

        АЛГОРИТМ:
            1. Извлекаем данные для каждого компонента адреса
            2. Создаем объекты в правильном порядке (от страны к строению)
            3. Передаем контекст (созданные объекты) для зависимых компонентов
            4. Создаем или находим адрес
            5. Проверяем существование такого же адреса

        АРГУМЕНТЫ:
            validated_data : dict
                Валидированные данные запроса

        ВОЗВРАЩАЕТ:
            Address : Созданный или найденный адрес

        ИСКЛЮЧЕНИЯ:
            serializers.ValidationError: При нарушении иерархии или валидации
        """
        # Извлекаем вложенные данные
        country_data = validated_data.pop('country', None)
        federal_district_data = validated_data.pop('federal_district', None)
        type_region_data = validated_data.pop('type_region', None)
        region_data = validated_data.pop('region', None)
        locality_type_data = validated_data.pop('locality_type', None)
        city_data = validated_data.pop('city', None)
        administrative_territory_data = validated_data.pop('administrative_territory', None)
        administrative_unit_data = validated_data.pop('administrative_unit', None)
        street_type_data = validated_data.pop('street_type', None)
        street_data = validated_data.pop('street', None)
        house_data = validated_data.pop('house', None)
        building_data = validated_data.pop('building', None)
        coordinates_data = validated_data.pop('coordinates', None)

        # Создаем объекты в правильном порядке
        country = None
        federal_district = None
        type_region = None
        region = None
        locality_type = None
        city = None
        administrative_territory = None
        administrative_unit = None
        street_type = None
        street = None
        house = None
        building = None
        coordinates = None

        # 1. Страна (если указана)
        if country_data:
            country_serializer = NestedCountrySerializer(data=country_data)
            country_serializer.is_valid(raise_exception=True)
            country = country_serializer.save()

        # 2. Федеральный округ (требует страну)
        if federal_district_data:
            if not country:
                raise serializers.ValidationError({
                    'federal_district': 'Для создания федерального округа требуется страна'
                })

            federal_district_serializer = NestedFederalDistrictSerializer(
                data=federal_district_data,
                context={'country': country}
            )
            federal_district_serializer.is_valid(raise_exception=True)
            federal_district = federal_district_serializer.save()

        # 3. Тип региона
        if type_region_data:
            type_region_serializer = NestedTypeRegionSerializer(data=type_region_data)
            type_region_serializer.is_valid(raise_exception=True)
            type_region = type_region_serializer.save()

        # 4. Регион (требует федеральный округ и тип региона)
        if region_data:
            if not federal_district:
                raise serializers.ValidationError({
                    'region': 'Для создания региона требуется федеральный округ'
                })

            if not type_region:
                raise serializers.ValidationError({
                    'region': 'Для создания региона требуется тип региона'
                })

            region_serializer = NestedRegionSerializer(
                data=region_data,
                context={
                    'federal_district': federal_district,
                    'type_region': type_region
                }
            )
            region_serializer.is_valid(raise_exception=True)
            region = region_serializer.save()

        # 5. Тип населенного пункта
        if locality_type_data:
            locality_type_serializer = NestedLocalityTypeSerializer(data=locality_type_data)
            locality_type_serializer.is_valid(raise_exception=True)
            locality_type = locality_type_serializer.save()

        # 6. Город (требует регион и может требовать тип населенного пункта)
        if city_data:
            if not region:
                raise serializers.ValidationError({
                    'city': 'Для создания города требуется регион'
                })

            city_serializer = NestedCitySerializer(
                data=city_data,
                context={
                    'region': region,
                    'locality_type': locality_type
                }
            )
            city_serializer.is_valid(raise_exception=True)
            city = city_serializer.save()

        # 7. Административный округ (требует город)
        if administrative_territory_data:
            if not city:
                raise serializers.ValidationError({
                    'administrative_territory': 'Для создания административного округа требуется город'
                })

            administrative_territory_serializer = NestedAdministrativeTerritorySerializer(
                data=administrative_territory_data,
                context={'city': city}
            )
            administrative_territory_serializer.is_valid(raise_exception=True)
            administrative_territory = administrative_territory_serializer.save()

        # 8. Административная единица (требует город)
        if administrative_unit_data:
            if not city:
                raise serializers.ValidationError({
                    'administrative_unit': 'Для создания АТЕ требуется город'
                })

            administrative_unit_serializer = NestedAdministrativeUnitSerializer(
                data=administrative_unit_data,
                context={
                    'city': city,
                    'administrative_territory': administrative_territory
                }
            )
            administrative_unit_serializer.is_valid(raise_exception=True)
            administrative_unit = administrative_unit_serializer.save()

        # 9. Тип улицы
        if street_type_data:
            street_type_serializer = NestedStreetTypeSerializer(data=street_type_data)
            street_type_serializer.is_valid(raise_exception=True)
            street_type = street_type_serializer.save()

        # 10. Улица (требует город)
        if street_data:
            if not city:
                raise serializers.ValidationError({
                    'street': 'Для создания улицы требуется город'
                })

            street_serializer = NestedStreetSerializer(
                data=street_data,
                context={
                    'city': city,
                    'street_type': street_type
                }
            )
            street_serializer.is_valid(raise_exception=True)
            street = street_serializer.save()

        # 11. Дом (требует улицу)
        if house_data:
            if not street:
                raise serializers.ValidationError({
                    'house': 'Для создания дома требуется улица'
                })

            house_serializer = NestedHouseSerializer(
                data=house_data,
                context={'street': street}
            )
            house_serializer.is_valid(raise_exception=True)
            house = house_serializer.save()

        # 12. Строение (требует дом)
        if building_data:
            if not house:
                raise serializers.ValidationError({
                    'building': 'Для создания строения требуется дом'
                })

            building_serializer = NestedBuildingSerializer(
                data=building_data,
                context={'house': house}
            )
            building_serializer.is_valid(raise_exception=True)
            building = building_serializer.save()
        # 13 Координаты
        if coordinates_data:
            coordinates_serializer = NestedCoordinatesSerializer(data=coordinates_data)
            coordinates_serializer.is_valid(raise_exception=True)
            coordinates = coordinates_serializer.save()


        # Формируем условия для поиска существующего адреса
        address_lookup = {}

        if country:
            address_lookup['country'] = country
        if federal_district:
            address_lookup['federal_district'] = federal_district
        if region:
            address_lookup['region'] = region
        if city:
            address_lookup['city'] = city
        if administrative_territory:
            address_lookup['administrative_territory'] = administrative_territory
        if administrative_unit:
            address_lookup['administrative_unit'] = administrative_unit
        if street:
            address_lookup['street'] = street
        if house:
            address_lookup['house'] = house
        if building:
            address_lookup['building'] = building
        if coordinates:
            address_lookup['coordinates'] = coordinates

        # Добавляем дополнительные поля
        if validated_data.get('microdistrict'):
            address_lookup['microdistrict'] = validated_data['microdistrict']
        if validated_data.get('index'):
            address_lookup['index'] = validated_data['index']

        # Ищем существующий адрес
        existing_address = None
        if address_lookup:
            existing_address = Address.objects.filter(**address_lookup).first()

        # Если нашли существующий адрес - возвращаем его
        if existing_address:
            return existing_address

        # Создаем новый адрес
        address = Address.objects.create(
            country=country,
            federal_district=federal_district,
            region=region,
            city=city,
            administrative_territory=administrative_territory,
            administrative_unit=administrative_unit,
            street=street,
            house=house,
            building=building,
            coordinates=coordinates,
            **validated_data
        )

        return address


class AddressReadSerializer(serializers.ModelSerializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ЧТЕНИЯ ПОЛНОГО АДРЕСА.

    ОПИСАНИЕ:
        Используется для отображения полного адреса со всеми связанными объектами.
        Каждый компонент адреса представлен соответствующим сериализатором для чтения.
        Включает вычисляемое поле full_address.

    ОСОБЕННОСТИ:
        • Вложенные сериализаторы для всех компонентов
        • Полный адрес в строковом формате
        • Только для чтения

    ПРИМЕР ВЫВОДА JSON:
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "country": {"id": "...", "name": "Россия"},
            "region": {"id": "...", "name": "Московская область"},
            "city": {"id": "...", "name": "г. Москва"},
            "street": {"id": "...", "name": "ул. Ленина"},
            "house": {"id": "...", "number": "1"},
            "building": {"id": "...", "number": "А"},
            "microdistrict": "Центральный",
            "index": "101000",
            "latitude": "55.7558",
            "longitude":"37.6173",
            "full_address": "101000, Россия, Московская область, г. Москва, ул. Ленина, д. 1, стр. А, Центральный"
        }
    """

    # Вложенные сериализаторы для чтения
    country = CountrySerializer(read_only=True)
    federal_district = FederalDistrictSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    administrative_territory = AdministrativeTerritorySerializer(read_only=True)
    administrative_unit = AdministrativeUnitSerializer(read_only=True)
    street = StreetSerializer(read_only=True)
    house = HouseSerializer(read_only=True)
    building = BuildingSerializer(read_only=True)
    coordinates = CoordinatesSerializers(read_only=True)

    # Вычисляемое поле для полного адреса
    full_address = serializers.CharField(
        read_only=True,
        help_text="Полный адрес в строковом формате"
    )

    class Meta:
        model = Address
        fields = [
            'id',
            # Компоненты адреса
            'country', 'federal_district', 'region', 'city',
            'administrative_territory', 'administrative_unit',
            'street', 'house', 'building', 'coordinates',
            # Дополнительные поля
            'microdistrict', 'index',
            # Вычисляемое поле
            'full_address'
        ]
        read_only_fields = fields


class AddressWebResultSerializer(serializers.ModelSerializer):
    city = serializers.CharField(read_only=True, source="adress.city.name")
    localityType = serializers.CharField(read_only=True, source="adress.city.locality_type.name")
    street = serializers.CharField(read_only=True, source="adress.street.name")
    streetType = serializers.CharField(read_only=True, source="adress.street.street_type.name")
    class Meta:
        model = Address
        fields = ("id", "city", "localityType", "street", "streetType")
        read_only_fields = fields

# ====================================================================================
# МОДУЛЬ 4: ДОПОЛНИТЕЛЬНЫЕ СЕРИАЛИЗАТОРЫ ДЛЯ ПОИСКА И ФИЛЬТРАЦИИ
# ====================================================================================

class AddressSearchSerializer(serializers.Serializer):
    """
    СЕРИАЛИЗАТОР ДЛЯ ПОИСКА АДРЕСОВ.

    ОПИСАНИЕ:
        Используется для поиска адресов по различным критериям.
        Поддерживает поиск по всем компонентам адреса.

    ПОЛЯ ДЛЯ ПОИСКА:
        • query: общий поисковый запрос
        • country: фильтр по стране (UUID)
        • region: фильтр по региону (UUID)
        • city: фильтр по городу (UUID)
        • street: фильтр по улице (UUID)
        • index: фильтр по почтовому индексу
        • limit: ограничение количества результатов
        • offset: смещение для пагинации
    """

    query = serializers.CharField(
        required=False,
        help_text="Общий поисковый запрос по всем текстовым полям"
    )

    country = serializers.UUIDField(
        required=False,
        help_text="Фильтр по стране (UUID)"
    )

    region = serializers.UUIDField(
        required=False,
        help_text="Фильтр по региону (UUID)"
    )

    city = serializers.UUIDField(
        required=False,
        help_text="Фильтр по городу (UUID)"
    )

    street = serializers.UUIDField(
        required=False,
        help_text="Фильтр по улице (UUID)"
    )

    index = serializers.CharField(
        required=False,
        max_length=6,
        help_text="Фильтр по почтовому индексу"
    )

    limit = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=100,
        default=20,
        help_text="Количество результатов (1-100)"
    )

    offset = serializers.IntegerField(
        required=False,
        min_value=0,
        default=0,
        help_text="Смещение для пагинации"
    )

    def validate(self, data):
        """Валидация параметров поиска."""
        # Проверка, что указан хотя бы один параметр поиска
        if not any([
            data.get('query'),
            data.get('country'),
            data.get('region'),
            data.get('city'),
            data.get('street'),
            data.get('index')
        ]):
            raise serializers.ValidationError({
                'non_field_errors': [
                    'Необходимо указать хотя бы один параметр поиска'
                ]
            })

        return data
