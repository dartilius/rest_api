import hashlib
from datetime import time
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from rest_framework import serializers
from brands.models import Brand
from brands.serializers import BrandSerializer
from counterparties.models import Counterparty
from counterparties.serializers import CounterpartiesShortSerializer, TenantsShortSerializer
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
)
from addresses.models import Address as AddressBook
from addresses.serializers import AddressCreateSerializer, AddressReadSerializer
from api.base_objects import Article

serializers.ModelSerializer.serializer_field_mapping[Article] = serializers.IntegerField



serializers.ModelSerializer.serializer_field_mapping[Article] = serializers.IntegerField

ALLOWED_FORMATS = ("jpg", "jpeg", "png", "webp")

# class TenantShortSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Counterparty
#         fields = (
#             'id',
#             'first_name',
#             'last_name',
#             'additional_name',
#             'keyword',
#         )


class PhotoSerializer(serializers.ModelSerializer):
    source = Base64FileField()

    class Meta:
        model = NomenclatureImage
        fields = ("id", "source", "type", "created")
        read_only_fields = ("id", "created")

    def validate_source(self, file):
        ext = file.name.split(".")[-1].lower()
        if ext not in ALLOWED_FORMATS:
            raise serializers.ValidationError(
                f"Недопустимый формат файла. Разрешены: {', '.join(ALLOWED_FORMATS)}"
            )

        # Проверка размера (пример 15MB)
        if file.size > 15 * 1024 * 1024:
            raise serializers.ValidationError("Максимальный размер файла 15MB")

        return file

    def validate(self, attrs):
        nomenclature = self.context.get("nomenclature")
        if not nomenclature:
            raise serializers.ValidationError("Номенклатура не передана")

        # вычисляем md5 хэш для файла
        file_data = attrs["source"].read()
        file_hash = hashlib.md5(file_data).hexdigest()
        attrs["source"].seek(0)  # обязательно вернуть курсор

        # проверка дубликата по содержимому
        if NomenclatureImage.objects.filter(nomenclature=nomenclature, hash=file_hash).exists():
            raise serializers.ValidationError("Эта фотография уже прикреплена к номенклатуре")

        return attrs

    def create(self, validated_data):
        validated_data["nomenclature"] = self.context["nomenclature"]
        return super().create(validated_data)


class InNomenclaturePhotoSerializer(serializers.ModelSerializer):
    """Схема для добавления фотографий к номенклатурам."""

    class Meta:
        model = NomenclatureImage
        fields = ("source", "id",)
        read_only_fields = ("source", "id",)


class ShortBrandNomenclatureSerializer(serializers.ModelSerializer):
    """Схема для отображения номенклатуры в списке."""

    brand_name = serializers.CharField(source='brand.name', default='Без значения')
    brand_id = serializers.CharField(source='brand.id', default=None)
    brand_logotype = serializers.CharField(source='brand.logotype', default=None)

    class Meta:
        model = Nomenclature
        fields = (
            "brand_name",
            "brand_id",
            "brand_logotype",
        )
        read_only_fields = fields


class NomenclatureTenantResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа с арендаторами номенклатуры"""
    id = serializers.UUIDField(source='tenant.id', read_only=True)
    name = serializers.SerializerMethodField()
    logotype = serializers.SerializerMethodField()
    floor = serializers.CharField(read_only=True)
    atm = serializers.BooleanField(read_only=True)
    brand_id = serializers.SerializerMethodField()  # Для отладки

    class Meta:
        model = NomenclatureTenant
        fields = ('id', 'name', 'logotype', 'floor', 'atm', 'brand_id')

    def get_name(self, obj):
        """Возвращаем имя бренда"""
        if obj.brand:
            return obj.brand.name
        return f"Бренд не указан (tenant: {obj.tenant.id})"  # Временное сообщение

    def get_logotype(self, obj):
        """Возвращаем URL логотипа бренда"""
        if obj.brand and obj.brand.logotype:
            if hasattr(obj.brand.logotype, 'url'):
                return obj.brand.logotype.url
            return str(obj.brand.logotype)
        return None

    def get_brand_id(self, obj):
        """Возвращаем ID бренда для отладки"""
        return str(obj.brand.id) if obj.brand else None

class NomenclatureSearchSerializer(serializers.ModelSerializer):
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
        return obj.brand.name if obj.brand else None

    def get_type_of_place_name(self, obj):
        return obj.typeOfPlace.name if obj.typeOfPlace else None

    def get_legal_entity_name(self, obj):
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
        except:
            return None

    def get_responsible_ad_name(self, obj):
        if not obj.responsible_ad:
            return None
        try:
            return f"{obj.responsible_ad.last_name or ''} {obj.responsible_ad.first_name or ''}".strip() or None
        except:
            return None

    def get_tenants_names(self, obj):
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
        except:
            return []

class TenantWriteSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    floor = serializers.CharField(required=False, allow_blank=True)
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    def validate_id(self, value):
        """Валидация ID арендатора"""
        try:
            Counterparty.objects.get(id=value)
            return value
        except Counterparty.DoesNotExist:
            raise serializers.ValidationError(f"Арендатор с id {value} не найден")

    def validate_brand(self, value):
        """Валидация бренда"""
        if value:
            # Проверяем, существует ли бренд
            if not Brand.objects.filter(id=value.id).exists():
                raise serializers.ValidationError(f"Бренд с id {value.id} не найден")
        return value

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #
    #     # Получаем арендатора из контекста
    #     counterparty = self.context.get('counterparty')
    #
    #     if counterparty:
    #         # Устанавливаем queryset для brand только из брендов этого арендатора
    #         self.fields['brand'].queryset = counterparty.brands.all()
    #
    # def validate_brand(self, value):
    #     """Валидация бренда"""
    #     if value:
    #         counterparty = self.context.get('counterparty')
    #         if counterparty and value not in counterparty.brands.all():
    #             raise serializers.ValidationError(
    #                 f"Бренд '{value}' не принадлежит арендатору"
    #             )
    #     return value
    #
    # def validate_id(self, value):
    #     """Валидация ID арендатора"""
    #     try:
    #         counterparty = Counterparty.objects.get(id=value)
    #         # Добавляем в контекст для валидации бренда
    #         if 'counterparty' not in self.context:
    #             self.context['counterparty'] = counterparty
    #         return value
    #     except Counterparty.DoesNotExist:
    #         raise serializers.ValidationError(f"Арендатор с id {value} не найден")
    #
    # def to_representation(self, instance):
    #     """Если нужно вернуть данные (но обычно для write_only это не нужно)"""
    #     return {
    #         'id': instance.id,
    #         'floor': instance.floor if hasattr(instance, 'floor') else None
    #     }

class TypeOfPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeOfPlace
        fields = "__all__"
        read_only_fields = ("id",)

class NomenclatureSerializer(serializers.ModelSerializer):
    """Сериализация одной номенклатуры."""
    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
    typeOfPlace_id = serializers.PrimaryKeyRelatedField(
        queryset=TypeOfPlace.objects.all(),
        source="typeOfPlace",
        write_only=True,
        required=False,
        allow_null=True,
    )
    nameForFront = serializers.CharField(source="name_for_front", read_only=True)
    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()
    legalEntity = CounterpartiesShortSerializer(read_only=True)
    legalEntity_id = serializers.PrimaryKeyRelatedField(
        queryset=Counterparty.objects.all(),
        source="legalEntity",
        write_only=True,
        required=False,
        allow_null=True,
    )
    # READ
    tenants = NomenclatureTenantResponseSerializer(
        source='nomenclature_tenants',
        many=True,
        read_only=True
    )

    # WRITE
    tenants_id = TenantWriteSerializer(
        many=True,
        write_only=True,
        required=False
    )
    brand = BrandSerializer(read_only=True)  # чисто чтение
    brand_id = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        source="brand",
        write_only=True,
        required=False,
        allow_null=True,
    )  # только запись по id
    exterior = serializers.SerializerMethodField()
    interior = serializers.SerializerMethodField()
    code1c = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    contentType = serializers.ChoiceField(
        choices=list(AVAILABLE_CONTENT_TYPES.keys()),
        required=False,
    )
    article = serializers.IntegerField(read_only=True)
    address_data = AddressCreateSerializer(
        source="address.address", required=False, write_only=True
    )
    address_id = serializers.PrimaryKeyRelatedField(
        queryset=AddressBook.objects.all(),
        source="address.address",
        write_only=True,
        required=False,
        allow_null=True,
    )
    address = AddressReadSerializer(source="address.address", read_only=True)
    formattedAddress = serializers.SerializerMethodField()

    class Meta:
        fields = "__all__"
        extra_fields = ("nameForFront",)
        read_only_fields = (
            "id",
            "owner",
            "hw_info",
            "version",
            "created",
            "status",
            "last_answer",
            "legalEntity",
            'tenants',
            "brand",
            "interior",
            "exterior",
            "nameForFront",
            "typeOfPlace",
            "formattedAddress",
        )
        model = Nomenclature

    def get_formattedAddress(self, obj):
        """Возвращает объект с отформатированным адресом и координатами"""
        try:
            # Пытаемся получить связанный объект NomenclatureAddress
            nomenclature_address = obj.address
        except ObjectDoesNotExist:
            # Если связи нет, возвращаем пустой адрес
            return {
                "name": "",
                "coordinates": {
                    "latitude": None,
                    "longitude": None
                }
            }

        # Если связь есть, но нет самого адреса
        if not nomenclature_address or not nomenclature_address.address:
            return {
                "name": "",
                "coordinates": {
                    "latitude": None,
                    "longitude": None
                }
            }
    
        address = nomenclature_address.address

        if not address:
            return {
                "name": "",
                "coordinates": {
                    "latitude": None,
                    "longitude": None
                }
            }

        # Формируем строку адреса
        address_parts = []

        # Город
        if address.city and address.city.name:
            address_parts.append(f"г. {address.city.name}")

        # Улица
        if address.street and address.street.name:
            address_parts.append(f"ул. {address.street.name}")

        # Номер дома/строения
        house_number = None
        if address.house and address.house.number:
            house_number = address.house.number
        elif address.building and address.building.number:
            house_number = address.building.number

        if house_number:
            address_parts.append(house_number)

        # 🔥 ИСПРАВЛЕНО: проверяем наличие coordinates и его атрибутов
        latitude = None
        longitude = None
    
        if hasattr(address, 'coordinates') and address.coordinates:
            try:
                if hasattr(address.coordinates, 'latitude'):
                    latitude = str(address.coordinates.latitude) if address.coordinates.latitude else None
                if hasattr(address.coordinates, 'longitude'):
                    longitude = str(address.coordinates.longitude) if address.coordinates.longitude else None
            except (AttributeError, TypeError):
                # Если что-то пошло не так, оставляем None
                pass

        # Формируем объект с адресом и координатами
        return {
            "name": ', '.join(address_parts),
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            }
        }


    def get_tenants(self, obj):
        """Возвращаем арендаторов с этажом"""
        return NomenclatureTenantSerializer(
            obj.nomenclature_tenants.select_related('tenant').prefetch_related('tenant__brands').all(),
            many=True,
            context=self.context
        ).data

    def validate_settings(self, value):
        """
        Валидация настроек.

        Проверяется:
        1. Наличие обязательных ключей worktime и default_volume
        2. Корректность значений этих ключей
        3. При наличии опциональных значений custom_volume - всё то же самое,
            а также они дополнительно преверяются на пересечение
        """

        def _translate_error(err):
            """Это нужно для перевода стандартной ошибки time"""
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
                f"Количество {time_val} должно быть "
                f"в пределах {e_list[-1]}"
            )

        def _validate_time(interval: str) -> None:
            """Валидация промежутков времени."""
            if not isinstance(interval, str):
                raise serializers.ValidationError(
                    "Интервал времени имеет не правильный формат!"
                )
            split_interval = interval.split("-")
            if len(split_interval) != 2:
                raise serializers.ValidationError(
                    "Интервал времени должен содержать ровно два значения!"
                )
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
            """Валидация настроек громкости."""
            length = 4
            if len(volume) != length:
                raise serializers.ValidationError(
                    f"Значений громкости должно быть ровно {length}"
                )
            if not all(isinstance(vol, int) for vol in volume):
                raise serializers.ValidationError(
                    "Громкость должна передаваться целочисленным значением"
                )
            if not all(0 <= vol <= 100 for vol in volume):
                raise serializers.ValidationError(
                    "Громкость может быть только от 0 до 100"
                )

        def _validate_collision(custom_settings: dict) -> None:
            """Валидация пересечения временных отрезков для custom_volume."""
            sorted_settings = sorted(custom_settings)
            for curr, next_ in zip(sorted_settings, sorted_settings[1:]):
                split_curr = curr.split("-")
                end_curr = list(map(int, split_curr[1].split(":")))
                split_next = next_.split("-")
                start_next = list(map(int, split_next[0].split(":")))
                if time(*end_curr) > time(*start_next):
                    raise serializers.ValidationError(
                        "Обнаружено пересечение в часах "
                        "пользовательских настроек громкости"
                    )

        for day, settings in value.items():
            # 1
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
            # 2
            _validate_time(req_keys["worktime"])
            _validate_volume(req_keys["default_volume"])
            # 3
            if "custom_volume" in settings:
                for interval, volume in settings["custom_volume"].items():
                    _validate_time(interval)
                    _validate_volume(tuple(volume))
                _validate_collision(settings["custom_volume"])
        return value

    # def _set_tenants(self, nomenclature, tenants_data):
    #     if not tenants_data:
    #         return
    #
    #     unique_ids = set()
    #     objs = []
    #
    #     for t in tenants_data:
    #         tenant_id = t["id"]
    #
    #         if tenant_id in unique_ids:
    #             continue
    #
    #         unique_ids.add(tenant_id)
    #
    #         objs.append(
    #             NomenclatureTenant(
    #                 nomenclature=nomenclature,
    #                 tenant_id=tenant_id,
    #                 floor=t.get("floor", "")
    #             )
    #         )
    #
    #     NomenclatureTenant.objects.bulk_create(objs)

    def _set_tenants(self, nomenclature, tenants_data):
        """Установка арендаторов для номенклатуры"""
        for tenant_data in tenants_data:
            tenant_id = tenant_data.get('id')
            floor = tenant_data.get('floor', '')
            brand = tenant_data.get('brand')  # Здесь brand должен быть объектом Brand или ID

            # Получаем Counterparty (арендатора)
            try:
                counterparty = Counterparty.objects.get(id=tenant_id)
            except Counterparty.DoesNotExist:
                raise Exception(f"Арендатор с id {tenant_id} не найден")

            # Если brand передан как ID, получаем объект Brand
            brand_obj = None
            if brand:
                if isinstance(brand, str):
                    try:
                        brand_obj = Brand.objects.get(id=brand)
                    except Brand.DoesNotExist:
                        raise Exception(f"Бренд с id {brand} не найден")
                else:
                    brand_obj = brand

            # Создаем связь
            NomenclatureTenant.objects.create(
                nomenclature=nomenclature,
                tenant=counterparty,
                floor=floor,
                brand=brand_obj,  # 👈 Убедитесь, что передается объект Brand
            )

    def create(self, validated_data):
        # Извлекаем все поля, которые нужно обработать отдельно
        address_data = None
        address_id = None

        # Вариант 1: через address_data
        if "address_data" in validated_data:
            address_data = validated_data.pop("address_data")

        # Вариант 2: через address_id
        elif "address_id" in validated_data:
            address_id = validated_data.pop("address_id")

        # Вариант 3: через старую структуру address.address
        elif "address" in validated_data:
            address_relation = validated_data.pop("address", {})
            address_data = address_relation.get("address") if address_relation else None

        tenants_id = validated_data.pop("tenants_id", [])

        # Извлекаем поля внешних ключей для отдельной обработки
        brand_id = validated_data.pop("brand_id", None)
        legalEntity_id = validated_data.pop("legalEntity_id", None)
        typeOfPlace_id = validated_data.pop("typeOfPlace_id", None)

        # Получаем данные для проверок
        code1c = validated_data.get("code1c")
        price_per_month = validated_data.get("pricePerMonth")
        name = validated_data.get("name")

        # Проверка code1c на уникальность
        if code1c:
            old_item = Nomenclature.objects.filter(code1c=code1c).first()
            if old_item:
                log_path = "/app/network_logs/nomenclature_conflicts.log"
                try:
                    with open(log_path, "a", encoding="utf-8") as f:
                        f.write(f"{name}: {old_item.id}, {getattr(old_item, 'code1c', '—')}\n")
                except Exception:
                    pass

                raise serializers.ValidationError({
                    "code1c": f"Номенклатура с кодом '{code1c}' уже существует (id={old_item.id})"
                })

        # Проверка pricePerMonth
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

        # СОЗДАЕМ НОМЕНКЛАТУРУ (после всех проверок)
        try:
            nomenclature = Nomenclature.objects.create(**validated_data)
        except Exception as e:
            raise serializers.ValidationError({
                "non_field_errors": f"Ошибка при создании номенклатуры: {str(e)}"
            })

        # Обработка brand_id
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

        # Обработка legalEntity_id
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

        # Обработка typeOfPlace_id
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

        # --- ОБРАБОТКА АДРЕСА ПРИ СОЗДАНИИ ---

        # Если передан ID существующего адреса
        if address_id is not None:
            try:
                address_obj = AddressBook.objects.get(id=address_id)
                NomenclatureAddress.objects.create(
                    nomenclature=nomenclature,
                    address=address_obj
                )
            except AddressBook.DoesNotExist:
                raise serializers.ValidationError(
                    {"address_id": "Адрес с таким ID не найден"}
                )

        # Если переданы данные адреса для создания нового
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
                # Передаем каждому TenantWriteSerializer контекст с арендатором
                self._set_tenants(nomenclature, tenants_id)
            except Exception as e:
                nomenclature.delete()
                raise serializers.ValidationError({
                    "tenants_id": f"Ошибка при добавлении арендаторов: {str(e)}"
                })

        return nomenclature

    # def _set_tenants(self, nomenclature, tenants_data):
    #     """
    #     Установка арендаторов для номенклатуры с проверкой брендов.
    #     """
    #     for tenant_data in tenants_data:
    #         tenant_id = tenant_data.get('id')
    #         floor = tenant_data.get('floor', '')
    #         brand = tenant_data.get('brand')  # или brand_id
    #
    #         # Получаем Counterparty (арендатора)
    #         try:
    #             counterparty = Counterparty.objects.get(id=tenant_id)
    #         except Counterparty.DoesNotExist:
    #             raise Exception(f"Арендатор с id {tenant_id} не найден")

            # Проверяем бренд
            # brand_obj = None
            # if brand:
            #     # Проверяем, что бренд принадлежит этому арендатору
            #     # Важно: brand может быть объектом или ID
            #     if hasattr(brand, 'id'):
            #         # Если brand уже объект
            #         if brand not in counterparty.brands.all():
            #             raise Exception(
            #                 f"Бренд '{brand.name}' не принадлежит арендатору {counterparty}"
            #             )
            #         brand_obj = brand
            #     else:
            #         # Если brand это ID
            #         try:
            #             brand_obj = Brand.objects.get(id=brand.id if hasattr(brand, 'id') else brand)
            #             if brand_obj not in counterparty.brands.all():
            #                 raise Exception(
            #                     f"Бренд '{brand_obj.name}' не принадлежит арендатору {counterparty}"
            #                 )
            #         except Brand.DoesNotExist:
            #             raise Exception(f"Бренд с id {brand} не найден")

            # Создаем связь (проверьте, есть ли поле brand в NomenclatureTenant)
            # NomenclatureTenant.objects.create(
            #     nomenclature=nomenclature,
            #     tenant=counterparty,
            #     floor=floor,
            #     brand=brand_obj  # если поле brand существует
            # )

    def update(self, instance, validated_data):
        # 1️⃣ ИЗВЛЕКАЕМ ВСЕ ПОЛЯ ДЛЯ РУЧНОЙ ОБРАБОТКИ
        tenants_id = validated_data.pop("tenants_id", None)

        # Извлекаем данные для адреса (все варианты)
        address_data = None
        address_id = None

        if "address_data" in validated_data:
            address_data = validated_data.pop("address_data")
        elif "address_id" in validated_data:
            address_id = validated_data.pop("address_id")
        elif "address" in validated_data:
            address_relation = validated_data.pop("address", {})
            if isinstance(address_relation, dict):
                address_data = address_relation.get("address")
            elif isinstance(address_relation, AddressBook):
                address_id = address_relation.id

        # Извлекаем поля для связей
        brand_id = validated_data.pop("brand_id", None) if "brand_id" in validated_data else None
        legalEntity_id = validated_data.pop("legalEntity_id", None) if "legalEntity_id" in validated_data else None

        # Сохраняем code1c и price_per_month для дополнительной валидации
        code1c = validated_data.get("code1c")
        price_per_month = validated_data.get("pricePerMonth") if "pricePerMonth" in validated_data else None

        # 2️⃣ УДАЛЯЕМ ВСЕ ПОЛЯ С ТОЧЕЧНОЙ НОТАЦИЕЙ
        validated_data.pop('type_of_place_display', None)
        validated_data.pop('name_for_front', None)
        validated_data.pop('address', None)
        validated_data.pop('legalEntity', None)
        validated_data.pop('brand', None)
        validated_data.pop('tenants', None)

        # 3️⃣ ВЫЗЫВАЕМ РОДИТЕЛЬСКИЙ update
        instance = super().update(instance, validated_data)

        # 4️⃣ РУЧНАЯ ОБРАБОТКА ПОЛЕЙ

        # Валидация code1c
        if code1c is not None:
            conflict = Nomenclature.objects.filter(code1c=code1c).exclude(id=instance.id).first()
            if conflict:
                raise serializers.ValidationError({
                    "code1c": f"Код '{code1c}' уже используется в другой номенклатуре (id={conflict.id})"
                })
            instance.code1c = code1c

        # Валидация цены
        if price_per_month is not None and price_per_month < 0:
            raise serializers.ValidationError({
                "pricePerMonth": "Стоимость аренды не может быть меньше 0."
            })

        # Обновление юр.лица
        if legalEntity_id is not None:
            if legalEntity_id == "" or legalEntity_id is None:
                instance.legalEntity = None
            else:
                try:
                    instance.legalEntity = Counterparty.objects.get(id=legalEntity_id)
                except Counterparty.DoesNotExist:
                    raise serializers.ValidationError(
                        {"legalEntity_id": "Юр. лицо с таким ID не найдено"}
                    )

        # Обновление бренда
        if brand_id is not None:
            if brand_id == "" or brand_id is None:
                instance.brand = None
            else:
                try:
                    instance.brand = Brand.objects.get(id=brand_id)
                except Brand.DoesNotExist:
                    raise serializers.ValidationError(
                        {"brand_id": "Бренд с таким ID не найден"}
                    )

        # --- ОБРАБОТКА АДРЕСА ---
        if address_id is None and "address_id" in self.initial_data:
            if hasattr(instance, 'address') and instance.address:
                instance.address.delete()
        elif (address_data is None or address_data == {}) and "address_data" in self.initial_data:
            if hasattr(instance, 'address') and instance.address:
                instance.address.delete()
        elif address_id is not None:
            try:
                address_obj = AddressBook.objects.get(id=address_id)
                NomenclatureAddress.objects.update_or_create(
                    nomenclature=instance,
                    defaults={"address": address_obj}
                )
            except AddressBook.DoesNotExist:
                raise serializers.ValidationError(
                    {"address_id": "Адрес с таким ID не найден"}
                )
        elif address_data is not None and address_data != {}:
            if isinstance(address_data, dict):
                address_serializer = AddressCreateSerializer(data=address_data)
                address_serializer.is_valid(raise_exception=True)
                address_obj = address_serializer.save()
                NomenclatureAddress.objects.update_or_create(
                    nomenclature=instance,
                    defaults={"address": address_obj}
                )
            elif isinstance(address_data, AddressBook):
                NomenclatureAddress.objects.update_or_create(
                    nomenclature=instance,
                    defaults={"address": address_data}
                )

        # --- ОБРАБОТКА АРЕНДАТОРОВ (ИСПРАВЛЕНО - НЕ УДАЛЯЕМ НЕПЕРЕДАННЫХ) ---
        if 'tenants_id' in self.initial_data:
            if tenants_id is not None:
                # Получаем существующих арендаторов
                existing_tenants = {
                    str(nt.tenant_id): nt for nt in NomenclatureTenant.objects.filter(
                        nomenclature=instance
                    )
                }

                # Обновляем или создаем только переданных арендаторов
                for tenant_data in tenants_id:
                    tenant_id = str(tenant_data.get('id'))
                    if not tenant_id:
                        continue

                    floor = tenant_data.get('floor', '')
                    brand = tenant_data.get('brand')

                    # Получаем объект бренда
                    brand_obj = None
                    if brand:
                        if isinstance(brand, str):
                            try:
                                brand_obj = Brand.objects.get(id=brand)
                            except Brand.DoesNotExist:
                                raise serializers.ValidationError({
                                    "tenants_id": f"Бренд с id {brand} не найден"
                                })
                        else:
                            brand_obj = brand

                    if tenant_id in existing_tenants:
                        # Обновляем существующего
                        tenant_relation = existing_tenants[tenant_id]
                        tenant_relation.floor = floor
                        tenant_relation.brand = brand_obj
                        tenant_relation.save()
                    else:
                        # Создаем нового
                        try:
                            counterparty = Counterparty.objects.get(id=tenant_id)
                            NomenclatureTenant.objects.create(
                                nomenclature=instance,
                                tenant=counterparty,
                                floor=floor,
                                brand=brand_obj,
                            )
                        except Counterparty.DoesNotExist:
                            raise serializers.ValidationError({
                                "tenants_id": f"Арендатор с id {tenant_id} не найден"
                            })
            else:
                # tenants_id = null - удаляем всех арендаторов
                NomenclatureTenant.objects.filter(nomenclature=instance).delete()

        # 5️⃣ СОХРАНЯЕМ
        instance.save()

        return instance

    # def get_tenants(self, obj):
    #     """
    #     Возвращает список арендаторов с количеством арендуемых номенклатур
    #     """
    #     tenants = obj.tenants.annotate(
    #         places_count=Count("rented_nomenclatures")  # Исправлено!
    #     ).order_by("-places_count")

    #     return TenantsShortSerializer(tenants, many=True, context=self.context).data

    def get_status(self, obj) -> int | None:
        try:
            return obj.availability.status
        except AttributeError:
            return None

    def get_last_answer(self, obj) -> str:
        try:
            return f"{obj.availability.last_answer_date:%Y-%m-%d %H:%M:%S}"
        except AttributeError:
            return "Не выходила в сеть"

    def get_interior(self, obj):
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="interior"), many=True
        ).data

    def get_exterior(self, obj):
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="exterior"), many=True
        ).data

    def _user_id_name(self, user):
        if not user:
            return None

        # Берём ВСЕ basic телефоны
        basic_phones = list(
            user.contacts_cp
            .filter(type="phone", basic=True)
            .values_list("meaning", flat=True)
        )

        # fallback — если basic нет, но есть phone_number в CustomUser
        if not basic_phones and user.phone_number:
            basic_phones = [str(user.phone_number)]

        # гарантируем строки
        phones = [str(p) for p in basic_phones if p]

        return {
            "id": str(user.id),
            "full_name": user.first_name,
            "phone_number": phones,
        }

    def to_representation(self, obj):
        repr_ = super().to_representation(obj)

        # Создаем main_info точно как в оригинале
        repr_["main_info"] = {
            "description": obj.description,
            "owner": obj.owner.full_name,
            "timezone": TIMEZONES[obj.timezone],
            "status": self.get_status(obj),
            "last_answer": self.get_last_answer(obj),
            "version": obj.version,
            "created": f"{obj.created:%Y-%m-%d %H:%M:%S}",
        }

        repr_["responsible"] = {
            "ad": self._user_id_name(obj.responsible_ad),
            "radio": self._user_id_name(obj.responsible_radio),
            "technic": self._user_id_name(obj.responsible_technic),
            "technic_on_address": self._user_id_name(obj.responsible_technic_on_address),
            "placement_marketing": self._user_id_name(obj.responsible_placement_marketing),
        }

        repr_["tenants_length"] = obj.tenants.count()

        # if 'tenants' in repr_ and repr_['tenants']:
        #     transformed_tenants = []
        #     for tenant_item in repr_['tenants']:
        #         # Извлекаем данные из вложенной структуры
        #         tenant_data = tenant_item.get('tenant', {})
        #         floor = tenant_item.get('floor')
        #
        #         # Создаем новую структуру
        #         transformed_tenant = {
        #             'id': tenant_data.get('id'),
        #             'brands_list': tenant_data.get('brands_list'),
        #             'logotypes': tenant_data.get('logotypes', []),
        #             'floor': floor
        #         }
        #         transformed_tenants.append(transformed_tenant)
        #
        #     repr_['tenants'] = transformed_tenants

        # Добавляем broadcast
        repr_["broadcast"] = getattr(obj.legalEntity, "broadcast", None)

        # ✅ FIXED: Create a list of keys to remove instead of modifying while iterating
        fields_to_remove = []
        for field in repr_["main_info"]:
            if field in repr_:
                fields_to_remove.append(field)

        # Remove the fields after iteration
        for field in fields_to_remove:
            repr_.pop(field)

        # Remove responsibility fields
        fields_to_remove = [
            "responsible_ad",
            "responsible_radio",
            "responsible_technic",
            "responsible_technic_on_address",
            "responsible_placement_marketing",
        ]
        for field in fields_to_remove:
            repr_.pop(field, None)

        # Обработка settings (точная копия оригинала)
        if "settings" in repr_ and repr_["settings"]:
            # ✅ FIXED: Create a copy of items or use list() to avoid modification during iteration
            for day, setting in list(repr_["settings"].items()):
                repr_["settings"][day] = {
                    "worktime": setting["worktime"],
                    "default_volume": setting["default_volume"],
                    "custom_volume": (
                        setting["custom_volume"]
                        if "custom_volume" in setting
                        else {}
                    ),
                }

        if "address" in repr_:
            repr_.pop("address")

        # Преобразование contentType (точная копия оригинала)
        if "contentType" in repr_:
            key = repr_["contentType"]
            repr_["contentType"] = AVAILABLE_CONTENT_TYPES.get(key, key)

        return repr_


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализация списка номенклатур."""
    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
    # abbreviation = serializers.SerializerMethodField()
    # status = serializers.SerializerMethodField()
    brand = BrandSerializer()
    legalEntity = CounterpartiesShortSerializer()
    exterior = serializers.SerializerMethodField()
    address = AddressReadSerializer(source="address.address")
    formattedAddress = serializers.SerializerMethodField()
    # contentType = serializers.ChoiceField(
    #     choices=list(AVAILABLE_CONTENT_TYPES.values()),
    #     required=False
    # )

    class Meta:
        fields = (
            "id",
            "name",
            # "timezone",
            # "status",
            "legalEntity",
            "brand",
            "exterior",
            "address",
            "formattedAddress",
            # "contentType",
            "typeOfPlace",
            "pricePerMonth",
            "code1c",
            # "abbreviation",
        )
        read_only_fields = fields
        model = Nomenclature

    def get_exterior(self, obj):
        return InNomenclaturePhotoSerializer(
            obj.images.filter(type="exterior"), many=True
        ).data

    def get_status(self, obj):
        try:
            return obj.availability.status
        except AttributeError:
            return None

    def get_last_answer(self, obj):
        try:
            return f"{obj.availability.last_answer_date:%Y-%m-%d %H:%M:%S}"
        except AttributeError:
            return "Не выходила в сеть"

    def get_formattedAddress(self, obj):
        """Форматирует адрес с проверкой наличия всех частей"""
        try:
            # Пытаемся получить связанный адрес
            nomenclature_address = obj.address
        except ObjectDoesNotExist:
            # Если связи нет, возвращаем пустую строку
            return ""

        # Если связь есть, но нет самого адреса
        if not nomenclature_address or not nomenclature_address.address:
            return ""

        address = nomenclature_address.address

        address_parts = []

        # Проверяем и добавляем город
        if address.city and address.city.name:
            address_parts.append(f"г. {address.city.name}")

        # Проверяем и добавляем улицу
        if address.street and address.street.name:
            address_parts.append(f"ул. {address.street.name}")

        # Проверяем наличие номера дома или строения
        house_number = None
        if address.house and address.house.number:
            house_number = address.house.number
        elif address.building and address.building.number:
            house_number = address.building.number

        if house_number:
            address_parts.append(house_number)

        # Если есть улица, но нет номера, все равно возвращаем "город, улица"
        # Если есть только город, возвращаем только город

        return ', '.join(address_parts)

    def to_representation(self, value):
        repr_ = super().to_representation(value)

        if "address" in repr_:
            repr_.pop("address")

        return repr_



class StatusHistorySerializer(serializers.ModelSerializer):
    """Сериализация истории доступности."""

    class Meta:
        fields = ("change_time", "status")
        read_only_fields = fields
        model = StatusHistory

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_["change_time"] = f"{value.change_time:%Y-%m-%d %H:%M:%S}"
        return repr_
