# """
# Тесты для модуля addresses.
#
# Содержит тесты для моделей, сериализаторов и вьюсетов.
# """
#
# from django.test import TestCase
# from django.contrib.auth import get_user_model
# from rest_framework.test import APITestCase, APIClient
# from rest_framework import status
# from uuid import uuid4
#
# from .models import (
#     Country, FederalDistrict, TypeRegion, Timezone, Region,
#     LocalityType, City, AdministrativeTerritory,
#     AdministrativeTerritorialUnit, StreetType, Street,
#     House, Building, Address, Coordinates
# )
#
#
# class AddressModelsTest(TestCase):
#     """Тесты для моделей адресов."""
#
#     def setUp(self):
#         """Создание тестовых данных."""
#         # Создаем страну
#         self.country = Country.objects.create(name="Россия")
#
#         # Создаем федеральный округ
#         self.federal_district = FederalDistrict.objects.create(
#             country=self.country,
#             name="Центральный",
#             abbreviated_name="ЦФО"
#         )
#
#         # Создаем тип региона
#         self.type_region = TypeRegion.objects.create(
#             name="область",
#             abbreviated_name="обл."
#         )
#
#         # Создаем регион
#         self.region = Region.objects.create(
#             name="Московская",
#             federal_district=self.federal_district,
#             type_region=self.type_region
#         )
#
#         # Создаем тип населенного пункта
#         self.locality_type = LocalityType.objects.create(
#             name="город",
#             abbreviated_name="г."
#         )
#
#         # Создаем город
#         self.city = City.objects.create(
#             name="Москва",
#             region=self.region,
#             locality_type=self.locality_type
#         )
#
#         # Создаем тип улицы
#         self.street_type = StreetType.objects.create(
#             name="улица",
#             abbreviated_name="ул."
#         )
#
#         # Создаем улицу
#         self.street = Street.objects.create(
#             name="Ленина",
#             city=self.city,
#             street_type=self.street_type
#         )
#
#         # Создаем дом
#         self.house = House.objects.create(
#             number="1",
#             street=self.street
#         )
#
#         # Создаем строение
#         self.building = Building.objects.create(
#             number="А",
#             house=self.house
#         )
#
#         # Создаем координаты
#         self.coordinates = Coordinates.objects.create(
#             latitude="55.7558",
#             longitude="37.6173"
#         )
#
#         # Создаем адрес
#         self.address = Address.objects.create(
#             country=self.country,
#             region=self.region,
#             city=self.city,
#             street=self.street,
#             house=self.house,
#             building=self.building,
#             coordinates=self.coordinates,
#             index="101000",
#             microdistrict="Центральный"
#         )
#
#     def test_country_str(self):
#         """Тест строкового представления страны."""
#         self.assertEqual(str(self.country), "Россия")
#
#     def test_federal_district_str(self):
#         """Тест строкового представления федерального округа."""
#         self.assertEqual(str(self.federal_district), "Центральный (Россия)")
#
#     def test_region_str(self):
#         """Тест строкового представления региона."""
#         self.assertEqual(str(self.region), "Московская обл.")
#
#     def test_city_str(self):
#         """Тест строкового представления города."""
#         self.assertEqual(str(self.city), "г. Москва")
#
#     def test_street_str(self):
#         """Тест строкового представления улицы."""
#         self.assertEqual(str(self.street), "ул. Ленина")
#
#     def test_house_str(self):
#         """Тест строкового представления дома."""
#         self.assertEqual(str(self.house), "ул. Ленина, д. 1")
#
#     def test_building_str(self):
#         """Тест строкового представления строения."""
#         self.assertEqual(str(self.building), "ул. Ленина, д. 1, стр. А")
#
#     def test_address_full_address(self):
#         """Тест полного адреса."""
#         expected = "101000, Россия, Московская обл., г. Москва, ул. Ленина, д. 1, стр. А, Центральный"
#         self.assertEqual(self.address.full_address, expected)
#
#     def test_address_get_components(self):
#         """Тест получения компонентов адреса."""
#         components = self.address.get_components()
#         self.assertEqual(components['country'], "Россия")
#         self.assertEqual(components['region'], "Московская обл.")
#         self.assertEqual(components['city'], "г. Москва")
#         self.assertEqual(components['street'], "ул. Ленина")
#         self.assertEqual(components['house'], "1")
#         self.assertEqual(components['building'], "А")
#         self.assertEqual(components['index'], "101000")
#         self.assertEqual(components['coordinates'], "55.7558, 37.6173")
#
#
# class AddressSerializersTest(TestCase):
#     """Тесты для сериализаторов адресов."""
#
#     def setUp(self):
#         """Создание тестовых данных."""
#         self.country = Country.objects.create(name="Россия")
#         self.federal_district = FederalDistrict.objects.create(
#             country=self.country,
#             name="Центральный",
#             abbreviated_name="ЦФО"
#         )
#         self.type_region = TypeRegion.objects.create(
#             name="область",
#             abbreviated_name="обл."
#         )
#         self.region = Region.objects.create(
#             name="Московская",
#             federal_district=self.federal_district,
#             type_region=self.type_region
#         )
#         self.locality_type = LocalityType.objects.create(
#             name="город",
#             abbreviated_name="г."
#         )
#         self.city = City.objects.create(
#             name="Москва",
#             region=self.region,
#             locality_type=self.locality_type
#         )
#         self.street_type = StreetType.objects.create(
#             name="улица",
#             abbreviated_name="ул."
#         )
#         self.street = Street.objects.create(
#             name="Ленина",
#             city=self.city,
#             street_type=self.street_type
#         )
#         self.house = House.objects.create(
#             number="1",
#             street=self.street
#         )
#         self.building = Building.objects.create(
#             number="А",
#             house=self.house
#         )
#         self.coordinates = Coordinates.objects.create(
#             latitude="55.7558",
#             longitude="37.6173"
#         )
#
#     def test_nested_country_serializer(self):
#         """Тест вложенного сериализатора страны."""
#         from .serializers import NestedCountrySerializer
#
#         data = {"name": "Россия"}
#         serializer = NestedCountrySerializer(data=data)
#         self.assertTrue(serializer.is_valid())
#         country = serializer.save()
#         self.assertEqual(country.name, "Россия")
#
#         # Проверка, что не создается дубликат
#         serializer2 = NestedCountrySerializer(data=data)
#         self.assertTrue(serializer2.is_valid())
#         country2 = serializer2.save()
#         self.assertEqual(country.id, country2.id)
#
#     def test_nested_region_serializer(self):
#         """Тест вложенного сериализатора региона."""
#         from .serializers import NestedRegionSerializer
#
#         data = {"name": "Московская"}
#         serializer = NestedRegionSerializer(
#             data=data,
#             context={
#                 'federal_district': self.federal_district,
#                 'type_region': self.type_region
#             }
#         )
#         self.assertTrue(serializer.is_valid())
#         region = serializer.save()
#         self.assertEqual(region.name, "Московская")
#         self.assertEqual(region.federal_district, self.federal_district)
#         self.assertEqual(region.type_region, self.type_region)
#
#     def test_address_create_serializer(self):
#         """Тест сериализатора создания адреса."""
#         from .serializers import AddressCreateSerializer
#
#         data = {
#             "country": {"name": "Россия"},
#             "region": {"name": "Московская"},
#             "city": {"name": "Москва"},
#             "street": {"name": "Ленина"},
#             "house": {"number": "1"},
#             "building": {"number": "А"},
#             "coordinates": {"latitude": "55.7558", "longitude": "37.6173"},
#             "index": "101000",
#             "microdistrict": "Центральный"
#         }
#
#         serializer = AddressCreateSerializer(data=data)
#         self.assertTrue(serializer.is_valid())
#         address = serializer.save()
#
#         self.assertEqual(address.country.name, "Россия")
#         self.assertEqual(address.region.name, "Московская")
#         self.assertEqual(address.city.name, "Москва")
#         self.assertEqual(address.street.name, "Ленина")
#         self.assertEqual(address.house.number, "1")
#         self.assertEqual(address.building.number, "А")
#         self.assertEqual(address.coordinates.latitude, "55.7558")
#         self.assertEqual(address.coordinates.longitude, "37.6173")
#         self.assertEqual(address.index, "101000")
#         self.assertEqual(address.microdistrict, "Центральный")
#
#     def test_address_read_serializer(self):
#         """Тест сериализатора чтения адреса."""
#         from .serializers import AddressReadSerializer
#
#         address = Address.objects.create(
#             country=self.country,
#             region=self.region,
#             city=self.city,
#             street=self.street,
#             house=self.house,
#             building=self.building,
#             coordinates=self.coordinates,
#             index="101000",
#             microdistrict="Центральный"
#         )
#
#         serializer = AddressReadSerializer(address)
#         data = serializer.data
#
#         self.assertEqual(data['country']['name'], "Россия")
#         self.assertEqual(data['region']['name'], "Московская")
#         self.assertEqual(data['city']['name'], "Москва")
#         self.assertEqual(data['street']['name'], "Ленина")
#         self.assertEqual(data['house']['number'], "1")
#         self.assertEqual(data['building']['number'], "А")
#         self.assertEqual(data['coordinates']['latitude'], "55.7558")
#         self.assertEqual(data['coordinates']['longitude'], "37.6173")
#         self.assertEqual(data['index'], "101000")
#         self.assertEqual(data['microdistrict'], "Центральный")
#         self.assertIn("101000", data['full_address'])
#         self.assertIn("Россия", data['full_address'])
#         self.assertIn("Московская", data['full_address'])
#         self.assertIn("Москва", data['full_address'])
#         self.assertIn("Ленина", data['full_address'])
#         self.assertIn("1", data['full_address'])
#         self.assertIn("А", data['full_address'])
#         self.assertIn("Центральный", data['full_address'])
#
#
# class AddressViewsTest(APITestCase):
#     """Тесты для вьюсетов адресов."""
#
#     def setUp(self):
#         """Создание тестовых данных и клиента."""
#         User = get_user_model()
#         self.user = User.objects.create_user(
#             email='testuser@test.com',
#             password='testpass',
#             phone_number='+79001234567'
#         )
#         self.client = APIClient()
#         self.client.force_authenticate(user=self.user)
#
#         # Создаем тестовые данные
#         self.country = Country.objects.create(name="Россия")
#         self.federal_district = FederalDistrict.objects.create(
#             country=self.country,
#             name="Центральный",
#             abbreviated_name="ЦФО"
#         )
#         self.type_region = TypeRegion.objects.create(
#             name="область",
#             abbreviated_name="обл."
#         )
#         self.region = Region.objects.create(
#             name="Московская",
#             federal_district=self.federal_district,
#             type_region=self.type_region
#         )
#         self.locality_type = LocalityType.objects.create(
#             name="город",
#             abbreviated_name="г."
#         )
#         self.city = City.objects.create(
#             name="Москва",
#             region=self.region,
#             locality_type=self.locality_type
#         )
#         self.street_type = StreetType.objects.create(
#             name="улица",
#             abbreviated_name="ул."
#         )
#         self.street = Street.objects.create(
#             name="Ленина",
#             city=self.city,
#             street_type=self.street_type
#         )
#         self.house = House.objects.create(
#             number="1",
#             street=self.street
#         )
#         self.building = Building.objects.create(
#             number="А",
#             house=self.house
#         )
#         self.coordinates = Coordinates.objects.create(
#             latitude="55.7558",
#             longitude="37.6173"
#         )
#
#         # Создаем адрес через API
#         data = {
#             "country": {"name": "Россия"},
#             "region": {"name": "Московская"},
#             "city": {"name": "Москва"},
#             "street": {"name": "Ленина"},
#             "house": {"number": "1"},
#             "building": {"number": "А"},
#             "coordinates": {"latitude": "55.7558", "longitude": "37.6173"},
#             "index": "101000",
#             "microdistrict": "Центральный"
#         }
#         response = self.client.post('/api/addresses/addresses/', data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.address_id = response.data['id']
#
#     def test_create_address_by_uuid(self):
#         """Тест создания адреса по UUID."""
#         data = {
#             "country": str(self.country.id),
#             "city": str(self.city.id),
#             "street": str(self.street.id),
#             "house": str(self.house.id),
#             "building": str(self.building.id),
#             "coordinates": str(self.coordinates.id),
#             "index": "101001",
#             "microdistrict": "Новый микрорайон"
#         }
#         response = self.client.post('/api/addresses/addresses/create_by_uuid/', data, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(response.data['index'], "101001")
#         self.assertEqual(response.data['microdistrict'], "Новый микрорайон")
#
#     def test_address_statistics(self):
#         """Тест статистики адресов."""
#         response = self.client.get('/api/addresses/addresses/statistics/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn('total', response.data)
#         self.assertIn('with_coordinates', response.data)
#         self.assertIn('with_index', response.data)
#         self.assertIn('by_country', response.data)
#         self.assertIn('by_city', response.data)
#         self.assertIn('recent', response.data)
#
#         # Проверяем, что статистика корректна
#         self.assertEqual(response.data['total'], 1)
#         self.assertEqual(response.data['with_coordinates']['count'], 1)
#         self.assertEqual(response.data['with_index']['count'], 1)
#
#         # Проверяем, что есть данные по странам и городам
#         self.assertEqual(len(response.data['by_country']), 1)
#         self.assertEqual(response.data['by_country'][0]['country__name'], "Россия")
#         self.assertEqual(response.data['by_country'][0]['count'], 1)
#
#         self.assertEqual(len(response.data['by_city']), 1)
#         self.assertEqual(response.data['by