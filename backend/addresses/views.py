# addresses/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from .serializers import *

@extend_schema(tags=["Адрес"])
class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return AddressCreateSerializer
        return AddressReadSerializer

    def create(self, request, *args, **kwargs):
        # Обрабатываем вложенную структуру
        if 'address' in request.data:
            address_data = request.data['address']
        else:
            address_data = request.data
        serializer = self.get_serializer(data=address_data)
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        # Всегда возвращаем полную расшифровку адреса
        read = AddressReadSerializer(address)
        headers = self.get_success_headers(read.data)
        return Response(read.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['post'])
    def create_by_uuid(self, request):
        """
        Создание адреса по UUID существующих объектов
        """
        data = request.data.copy()

        # Проверяем иерархию
        errors = self._validate_hierarchy(data)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        # Получаем объекты по UUID
        address_data = {}
        address_data['code1c'] = data.get('code1c', '')
        address_data['microdistrict'] = data.get('microdistrict')
        address_data['index'] = data.get('index')
        address_data['coordinates'] = data.get('coordinates')

        # Получаем связанные объекты
        if data.get('country'):
            try:
                address_data['country'] = Country.objects.get(id=data['country'])
            except Country.DoesNotExist:
                return Response(
                    {'country': 'Страна с указанным UUID не найдена'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if data.get('region'):
            try:
                address_data['region'] = Region.objects.get(id=data['region'])
            except Region.DoesNotExist:
                return Response(
                    {'region': 'Регион с указанным UUID не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if data.get('city'):
            try:
                address_data['city'] = City.objects.get(id=data['city'])
            except City.DoesNotExist:
                return Response(
                    {'city': 'Город с указанным UUID не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if data.get('street'):
            try:
                address_data['street'] = Street.objects.get(id=data['street'])
            except Street.DoesNotExist:
                return Response(
                    {'street': 'Улица с указанным UUID не найдена'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if data.get('house'):
            try:
                address_data['house'] = House.objects.get(id=data['house'])
            except House.DoesNotExist:
                return Response(
                    {'house': 'Дом с указанным UUID не найден'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        if data.get('building'):
            try:
                address_data['building'] = Building.objects.get(id=data['building'])
            except Building.DoesNotExist:
                return Response(
                    {'building': 'Строение с указанным UUID не найдено'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Создаем или получаем адрес используя сериализатор (он сам вернёт существующий при совпадении)
        serializer = AddressCreateSerializer(data=address_data)
        serializer.is_valid(raise_exception=True)
        address = serializer.save()
        read = AddressReadSerializer(address)
        return Response(read.data, status=status.HTTP_201_CREATED)

    def _validate_hierarchy(self, data):
        """Проверка иерархии объектов"""
        errors = {}

        # Если указан дом, должна быть указана улица
        if data.get('house') and not data.get('street'):
            errors['house'] = 'Для дома должна быть указана улица'

        # Если указано строение, должен быть указан дом
        if data.get('building') and not data.get('house'):
            errors['building'] = 'Для строения должен быть указан дом'

        # Если указана улица, должен быть указан город
        if data.get('street') and not data.get('city'):
            errors['street'] = 'Для улицы должен быть указан город'

        # Если указан город, должен быть указан регион
        if data.get('city') and not data.get('region'):
            errors['city'] = 'Для города должен быть указан регион'

        return errors


# Базовые вьюсеты для всех моделей
@extend_schema(tags=["Адрес (страна)"])
class CountryViewSet(viewsets.ModelViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

@extend_schema(tags=["Адрес (Фед. округ)"])
class FederalDistrictViewSet(viewsets.ModelViewSet):
    queryset = FederalDistrict.objects.all()
    serializer_class = FederalDistrictSerializer

@extend_schema(tags=["Адрес (тип региона)"])
class TypeRegionViewSet(viewsets.ModelViewSet):
    queryset = TypeRegion.objects.all()
    serializer_class = TypeRegionSerializer

@extend_schema(tags=["Адрес (часовой пояс)"])
class TimezoneViewSet(viewsets.ModelViewSet):
    queryset = Timezone.objects.all()
    serializer_class = TimezoneSerializer

@extend_schema(tags=["Адрес (регион)"])
class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

@extend_schema(tags=["Адрес (населенный пункт)"])
class LocalityTypeViewSet(viewsets.ModelViewSet):
    queryset = LocalityType.objects.all()
    serializer_class = LocalityTypeSerializer

@extend_schema(tags=["Адрес (город)"])
class CityViewSet(viewsets.ModelViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer

@extend_schema(tags=["Адрес (адм. округ)"])
class AdministrativeTerritoryViewSet(viewsets.ModelViewSet):
    queryset = AdministrativeTerritory.objects.all()
    serializer_class = AdministrativeTerritorySerializer

@extend_schema(tags=["Адрес (Административно-территориальная единица (АТЕ))"])
class AdministrativeTerritorialUnitViewSet(viewsets.ModelViewSet):
    queryset = AdministrativeTerritorialUnit.objects.all()
    serializer_class = AdministrativeUnitSerializer  # Используем существующий сериализатор

@extend_schema(tags=["Адрес (тип улицы)"])
class StreetTypeViewSet(viewsets.ModelViewSet):
    queryset = StreetType.objects.all()
    serializer_class = StreetTypeSerializer

@extend_schema(tags=["Адрес (улица)"])
class StreetViewSet(viewsets.ModelViewSet):
    queryset = Street.objects.all()
    serializer_class = StreetSerializer

@extend_schema(tags=["Адрес (дом)"])
class HouseViewSet(viewsets.ModelViewSet):
    queryset = House.objects.all()
    serializer_class = HouseSerializer

@extend_schema(tags=["Адрес (строение)"])
class BuildingViewSet(viewsets.ModelViewSet):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer