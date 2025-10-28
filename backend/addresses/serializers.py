from rest_framework import serializers
from .models import *


# Базовые сериализаторы для чтения
class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['id', 'name', 'code1c']


class FederalDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = FederalDistrict
        fields = ['id', 'name', 'abbreviated_name', 'code1c']


class TypeRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeRegion
        fields = ['id', 'name', 'abbreviated_name', 'show_before_name', 'skip_in_name', 'code1c']


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['id', 'name', 'abbreviated_name', 'code1c']


class LocalityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalityType
        fields = ['id', 'name', 'abbreviated_name', 'show_before_name', 'has_administrative_territory', 'code1c']


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['id', 'name', 'code1c']


class AdministrativeTerritorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdministrativeTerritory
        fields = ['id', 'name', 'code1c']


class AdministrativeUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdministrativeTerritorialUnit
        fields = ['id', 'name', 'code1c']


class StreetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreetType
        fields = ['id', 'name', 'abbreviated_name', 'show_before_name', 'code1c']


class StreetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Street
        fields = ['id', 'name', 'code1c']


class HouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ['id', 'number', 'code1c']


class BuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['id', 'number', 'code1c']


class TimezoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timezone
        fields = ['id', 'name', 'offset_utc', 'offset_moscow']


# Вложенные сериализаторы для создания (БЕЗ валидации unique)
class NestedCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ['name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},  # Отключаем валидацию unique
            'code1c': {'validators': []}  # Отключаем валидацию unique
        }

    def create(self, validated_data):
        code = validated_data.get('code1c')
        if code:
            country, created = Country.objects.get_or_create(
                code1c=code,
                defaults=validated_data
            )
        else:
            # Try to match by name
            country, created = Country.objects.get_or_create(
                name=validated_data.get('name'),
                defaults=validated_data
            )
        return country


class NestedFederalDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = FederalDistrict
        fields = ['name', 'abbreviated_name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'abbreviated_name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        country = self.context.get('country')
        if not country:
            raise serializers.ValidationError("Country is required for FederalDistrict")
        code = validated_data.get('code1c')
        if code:
            federal_district, created = FederalDistrict.objects.get_or_create(
                code1c=code,
                defaults={**validated_data, 'country': country}
            )
        else:
            federal_district, created = FederalDistrict.objects.get_or_create(
                name=validated_data.get('name'),
                defaults={**validated_data, 'country': country}
            )
        return federal_district


class NestedTypeRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeRegion
        fields = ['name', 'abbreviated_name', 'show_before_name', 'skip_in_name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        type_region, created = TypeRegion.objects.get_or_create(
            code1c=validated_data['code1c'],
            defaults=validated_data
        )
        return type_region


class NestedRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['name', 'abbreviated_name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        federal_district = self.context.get('federal_district')
        type_region = self.context.get('type_region')

        if not federal_district or not type_region:
            raise serializers.ValidationError("FederalDistrict and TypeRegion are required for Region")

        code = validated_data.get('code1c')
        if code:
            region, created = Region.objects.get_or_create(
                code1c=code,
                defaults={
                    **validated_data,
                    'federal_district': federal_district,
                    'type_region': type_region
                }
            )
        else:
            region, created = Region.objects.get_or_create(
                name=validated_data.get('name'),
                federal_district=federal_district,
                defaults={**validated_data, 'type_region': type_region}
            )
        return region


class NestedLocalityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalityType
        fields = ['name', 'abbreviated_name', 'show_before_name', 'has_administrative_territory', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        locality_type, created = LocalityType.objects.get_or_create(
            code1c=validated_data['code1c'],
            defaults=validated_data
        )
        return locality_type


class NestedCitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ['name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        region = self.context.get('region')
        locality_type = self.context.get('locality_type')

        if not region:
            raise serializers.ValidationError("Region is required for City")
        code = validated_data.get('code1c')
        if code:
            city, created = City.objects.get_or_create(
                code1c=code,
                defaults={
                    **validated_data,
                    'region': region,
                    'locality_type': locality_type
                }
            )
        else:
            city, created = City.objects.get_or_create(
                name=validated_data.get('name'),
                region=region,
                defaults={**validated_data, 'locality_type': locality_type}
            )
        return city


class NestedAdministrativeTerritorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AdministrativeTerritory
        fields = ['name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        city = self.context.get('city')
        if not city:
            raise serializers.ValidationError("City is required for AdministrativeTerritory")
        code = validated_data.get('code1c')
        if code:
            administrative_territory, created = AdministrativeTerritory.objects.get_or_create(
                code1c=code,
                defaults={**validated_data, 'city': city}
            )
        else:
            administrative_territory, created = AdministrativeTerritory.objects.get_or_create(
                name=validated_data.get('name'),
                city=city,
                defaults={**validated_data}
            )
        return administrative_territory


class NestedAdministrativeUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdministrativeTerritorialUnit
        fields = ['name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        city = self.context.get('city')
        administrative_territory = self.context.get('administrative_territory')

        if not city:
            raise serializers.ValidationError("City is required for AdministrativeUnit")
        code = validated_data.get('code1c')
        if code:
            administrative_unit, created = AdministrativeTerritorialUnit.objects.get_or_create(
                code1c=code,
                defaults={
                    **validated_data,
                    'city': city,
                    'administrative_territory': administrative_territory
                }
            )
        else:
            administrative_unit, created = AdministrativeTerritorialUnit.objects.get_or_create(
                name=validated_data.get('name'),
                city=city,
                defaults={
                    **validated_data,
                    'administrative_territory': administrative_territory
                }
            )
        return administrative_unit


class NestedStreetTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StreetType
        fields = ['name', 'abbreviated_name', 'show_before_name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        code = validated_data.get('code1c')
        if code:
            street_type, created = StreetType.objects.get_or_create(
                code1c=code,
                defaults=validated_data
            )
        else:
            street_type, created = StreetType.objects.get_or_create(
                name=validated_data.get('name'),
                defaults=validated_data
            )
        return street_type


class NestedStreetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Street
        fields = ['name', 'code1c']
        extra_kwargs = {
            'name': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        city = self.context.get('city')
        street_type = self.context.get('street_type')

        if not city:
            raise serializers.ValidationError("City is required for Street")
        code = validated_data.get('code1c')
        if code:
            street, created = Street.objects.get_or_create(
                code1c=code,
                defaults={
                    **validated_data,
                    'city': city,
                    'street_type': street_type
                }
            )
        else:
            street, created = Street.objects.get_or_create(
                name=validated_data.get('name'),
                city=city,
                defaults={**validated_data, 'street_type': street_type}
            )
        return street


class NestedHouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = House
        fields = ['number', 'code1c']
        extra_kwargs = {
            'number': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        street = self.context.get('street')
        if not street:
            raise serializers.ValidationError("Street is required for House")
        code = validated_data.get('code1c')
        if code:
            house, created = House.objects.get_or_create(
                code1c=code,
                defaults={**validated_data, 'street': street}
            )
        else:
            house, created = House.objects.get_or_create(
                number=validated_data.get('number'),
                street=street,
                defaults={**validated_data}
            )
        return house


class NestedBuildingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Building
        fields = ['number', 'code1c']
        extra_kwargs = {
            'number': {'validators': []},
            'code1c': {'validators': []}
        }

    def create(self, validated_data):
        house = self.context.get('house')
        if not house:
            raise serializers.ValidationError("House is required for Building")
        code = validated_data.get('code1c')
        if code:
            building, created = Building.objects.get_or_create(
                code1c=code,
                defaults={**validated_data, 'house': house}
            )
        else:
            building, created = Building.objects.get_or_create(
                number=validated_data.get('number'),
                house=house,
                defaults={**validated_data}
            )
        return building


# Основной сериализатор для создания адреса
class AddressCreateSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = Address
        fields = [
            'id', 'code1c', 'country', 'federal_district', 'type_region', 'region',
            'locality_type', 'city', 'administrative_territory', 'administrative_unit',
            'street_type', 'street', 'house', 'building', 'microdistrict', 'index', 'coordinates'
        ]
        extra_kwargs = {
            'code1c': {'required': False, 'allow_null': True}  # Делаем необязательным
        }

    def create(self, validated_data):
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

        # Создаем объекты в правильном порядке с учетом иерархии
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

        # Страна
        if country_data:
            country_serializer = NestedCountrySerializer(data=country_data)
            country_serializer.is_valid(raise_exception=True)
            country = country_serializer.save()

        # Федеральный округ
        if federal_district_data:
            federal_district_serializer = NestedFederalDistrictSerializer(
                data=federal_district_data,
                context={'country': country}
            )
            federal_district_serializer.is_valid(raise_exception=True)
            federal_district = federal_district_serializer.save()

        # Тип региона
        if type_region_data:
            type_region_serializer = NestedTypeRegionSerializer(data=type_region_data)
            type_region_serializer.is_valid(raise_exception=True)
            type_region = type_region_serializer.save()

        # Регион
        if region_data:
            region_serializer = NestedRegionSerializer(
                data=region_data,
                context={
                    'federal_district': federal_district,
                    'type_region': type_region
                }
            )
            region_serializer.is_valid(raise_exception=True)
            region = region_serializer.save()

        # Тип населенного пункта
        if locality_type_data:
            locality_type_serializer = NestedLocalityTypeSerializer(data=locality_type_data)
            locality_type_serializer.is_valid(raise_exception=True)
            locality_type = locality_type_serializer.save()

        # Город
        if city_data:
            city_serializer = NestedCitySerializer(
                data=city_data,
                context={
                    'region': region,
                    'locality_type': locality_type
                }
            )
            city_serializer.is_valid(raise_exception=True)
            city = city_serializer.save()

        # Административная территория
        if administrative_territory_data:
            administrative_territory_serializer = NestedAdministrativeTerritorySerializer(
                data=administrative_territory_data,
                context={'city': city}
            )
            administrative_territory_serializer.is_valid(raise_exception=True)
            administrative_territory = administrative_territory_serializer.save()

        # Административная единица
        if administrative_unit_data:
            administrative_unit_serializer = NestedAdministrativeUnitSerializer(
                data=administrative_unit_data,
                context={
                    'city': city,
                    'administrative_territory': administrative_territory
                }
            )
            administrative_unit_serializer.is_valid(raise_exception=True)
            administrative_unit = administrative_unit_serializer.save()

        # Тип улицы
        if street_type_data:
            street_type_serializer = NestedStreetTypeSerializer(data=street_type_data)
            street_type_serializer.is_valid(raise_exception=True)
            street_type = street_type_serializer.save()

        # Улица
        if street_data:
            street_serializer = NestedStreetSerializer(
                data=street_data,
                context={
                    'city': city,
                    'street_type': street_type
                }
            )
            street_serializer.is_valid(raise_exception=True)
            street = street_serializer.save()

        # Дом
        if house_data:
            house_serializer = NestedHouseSerializer(
                data=house_data,
                context={'street': street}
            )
            house_serializer.is_valid(raise_exception=True)
            house = house_serializer.save()

        # Строение
        if building_data:
            building_serializer = NestedBuildingSerializer(
                data=building_data,
                context={'house': house}
            )
            building_serializer.is_valid(raise_exception=True)
            building = building_serializer.save()

        # Попробуем найти существующий адрес по code1c
        code = validated_data.get('code1c')
        if code:
            try:
                return Address.objects.get(code1c=code)
            except Address.DoesNotExist:
                pass

        # Если code1c не указан или не найден, ищем по иерархии и полям
        lookup = {
            'country': country,
            'federal_district': federal_district,
            'region': region,
            'city': city,
            'administrative_territory': administrative_territory,
            'administrative_unit': administrative_unit,
            'street': street,
            'house': house,
            'building': building,
            'microdistrict': validated_data.get('microdistrict'),
            'index': validated_data.get('index'),
            'coordinates': validated_data.get('coordinates')
        }

        # Remove None values from lookup
        lookup = {k: v for k, v in lookup.items() if v is not None}

        existing = Address.objects.filter(**lookup).first()
        if existing:
            return existing

        # Создаем новый
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
            **validated_data
        )

        return address


# Сериализатор для чтения адреса
class AddressReadSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    federal_district = FederalDistrictSerializer(read_only=True)
    region = RegionSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    administrative_territory = AdministrativeTerritorySerializer(read_only=True)
    administrative_unit = AdministrativeUnitSerializer(read_only=True)
    street = StreetSerializer(read_only=True)
    house = HouseSerializer(read_only=True)
    building = BuildingSerializer(read_only=True)
    # Явное поле для полного адреса — помогает drf-spectacular определить тип
    full_address = serializers.CharField(read_only=True)

    class Meta:
        model = Address
        fields = [
            'id', 'code1c', 'country', 'federal_district', 'region', 'city',
            'administrative_territory', 'administrative_unit', 'street', 'house',
            'building', 'microdistrict', 'index', 'coordinates', 'full_address'
        ]