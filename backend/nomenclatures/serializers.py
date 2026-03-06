import hashlib
from datetime import time

from rest_framework import serializers
from brands.models import Brand
from brands.serializers import BrandSerializer
from counterparties.models import Counterparty
from counterparties.serializers import CounterpartiesSerializer, CounterpartiesShortSerializer
from files.serializers import Base64FileField
from nomenclatures.models import (
    Nomenclature,
    StatusHistory,
    TIMEZONES,
    NomenclatureImage,
    NomenclatureAddress,
    AVAILABLE_CONTENT_TYPES,
    TypeOfPlace
)
from addresses.models import Address as AddressBook
from addresses.serializers import AddressCreateSerializer, AddressReadSerializer
from api.base_objects import Article


serializers.ModelSerializer.serializer_field_mapping[Article] = serializers.IntegerField



serializers.ModelSerializer.serializer_field_mapping[Article] = serializers.IntegerField

ALLOWED_FORMATS = ("jpg", "jpeg", "png", "webp")

class TypeOfPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TypeOfPlace
        fields = "__all__"
        read_only_fields = ("id",)

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


class NomenclatureSerializer(serializers.ModelSerializer):
    """Сериализация одной номенклатуры."""

    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
    nameForFront = serializers.CharField(source="name_for_front", read_only=True)
    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()
    legalEntity = CounterpartiesShortSerializer(read_only=True)
    tenants = CounterpartiesShortSerializer(read_only=True, many=True)
    legalEntity_id = serializers.PrimaryKeyRelatedField(
        queryset=Counterparty.objects.all(),
        source="legalEntity",
        write_only=True,
        required=False,
        allow_null=True,
    )
    tenants_id = serializers.PrimaryKeyRelatedField(
        queryset=Counterparty.objects.all(),
        source="tenants",
        write_only=True,
        required=False,
        allow_null=True,
        many=True
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
            "nameForFront"
        )
        model = Nomenclature

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

    def create(self, validated_data):
        # Извлекаем данные адреса из разных источников
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

        # --- Оригинальная обработка brand ---
        brand = validated_data.pop("brand_id", None)

        tenants = validated_data.pop("tenants", None)
        name = validated_data.get("name")
        code1c = validated_data.get("code1c")
        price_of_month = validated_data.get("pricePerMonth")

        # --- Проверка уникальности code1c ---
        if code1c:
            old_item = Nomenclature.objects.filter(code1c=code1c).first()
            if old_item:
                log_path = "/app/network_logs/nomenclature_conflicts.log"
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(f"{name}: {old_item.id}, {getattr(old_item, 'code1c', '—')}\n")

                raise serializers.ValidationError({
                    "code1c": f"Номенклатура с кодом '{code1c}' уже существует (id={old_item.id})"
                })

        # --- Проверка цены ---
        if price_of_month is not None:
            if price_of_month < 0:
                raise serializers.ValidationError({
                    "pricePerMonth": "Стоимость аренды не может быть меньше 0."
                })

        # --- Обработка brand ---
        if brand:
            try:
                validated_data["brand"] = Brand.objects.get(id=brand)
            except Brand.DoesNotExist:
                raise serializers.ValidationError(
                    {"brand_id": "Бренд с таким ID не найден"}
                )

        # --- Создание номенклатуры ---
        try:
            nomenclature = Nomenclature.objects.create(**validated_data)
        except Exception as e:
            raise serializers.ValidationError({
                "non_field_errors": f"Ошибка при создании номенклатуры: {str(e)}"
            })

        # --- Обработка арендаторов ---
        if tenants is not None:
            nomenclature.tenants.set(tenants)

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

        return nomenclature

    def update(self, instance, validated_data):
        # Инициализация переменных для адреса
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
            if isinstance(address_relation, dict):
                address_data = address_relation.get("address")
            elif isinstance(address_relation, AddressBook):
                address_id = address_relation.id

        # Извлекаем другие данные
        brand_id = validated_data.pop("brand_id", None) if "brand_id" in validated_data else None
        legalEntity_id = validated_data.pop("legalEntity_id", None) if "legalEntity_id" in validated_data else None
        code1c = validated_data.get("code1c")
        price_per_month = validated_data.get("pricePerMonth") if "pricePerMonth" in validated_data else None
        tenants = validated_data.pop("tenants", None)

        # Валидация code1c
        if code1c is not None:
            conflict = Nomenclature.objects.filter(code1c=code1c).exclude(id=instance.id).first()
            if conflict:
                raise serializers.ValidationError({
                    "code1c": f"Код '{code1c}' уже используется в другой номенклатуре (id={conflict.id})\n"
                })
            instance.code1c = code1c

        # Валидация цены
        if price_per_month is not None:
            if price_per_month < 0:
                raise serializers.ValidationError({
                    "pricePerMonth": "Стоимость аренды не может быть меньше 0."
                })
            instance.pricePerMonth = price_per_month

        # Обновление юр.лица
        if legalEntity_id is not None:
            if legalEntity_id == "" or legalEntity_id is None:
                instance.legalEntity = None
            else:
                try:
                    instance.legalEntity = Counterparty.objects.get(id=legalEntity_id)
                except Counterparty.DoesNotExist:
                    raise serializers.ValidationError(
                        {
                            "legalEntity_id": "Юр. лицо с таким ID не найдено"
                        }
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

        # --- КЛЮЧЕВАЯ ЛОГИКА ОБРАБОТКИ АДРЕСА ---

        # Проверяем, нужно ли удалить адрес
        # Случай 1: явно передано address_id: null
        if address_id is None and "address_id" in self.initial_data:
            # Удаляем связь, если она существует
            if hasattr(instance, 'address') and instance.address:
                instance.address.delete()

        # Случай 2: явно передано address_data: null или {}
        elif (address_data is None or address_data == {}) and "address_data" in self.initial_data:
            if hasattr(instance, 'address') and instance.address:
                instance.address.delete()

        # Случай 3: передан ID существующего адреса
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

        # Случай 4: переданы данные адреса
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

        # Обработка арендаторов
        if tenants is not None:
            instance.tenants.set(tenants)

        # Обновляем остальные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        return instance

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
            "full_name": user.full_name,
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


        # Добавляем broadcast
        repr_["broadcast"] = getattr(obj.legalEntity, "broadcast", None)

        # Удаляем дублирующиеся поля из repr_
        # Важно: удаляем только те поля, которые есть в main_info
        for field in repr_["main_info"]:
            if field in repr_:
                repr_.pop(field)

        for field in (
            "responsible_ad",
            "responsible_radio",
            "responsible_technic",
            "responsible_technic_on_address",
            "responsible_placement_marketing",
        ):
            repr_.pop(field, None)

        # Обработка settings (точная копия оригинала)
        if "settings" in repr_ and repr_["settings"]:
            for day, setting in repr_["settings"].items():
                repr_["settings"][day] = {
                    "worktime": setting["worktime"],
                    "default_volume": setting["default_volume"],
                    "custom_volume": (
                        setting["custom_volume"]
                        if "custom_volume" in setting
                        else {}
                    ),
                }

        # Преобразование contentType (точная копия оригинала)
        if "contentType" in repr_:
            key = repr_["contentType"]
            repr_["contentType"] = AVAILABLE_CONTENT_TYPES.get(key, key)

        return repr_


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализация списка номенклатур."""
    typeOfPlace = serializers.CharField(source="type_of_place_display", read_only=True)
    abbreviation = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    brand = BrandSerializer()
    legalEntity = CounterpartiesShortSerializer()
    exterior = serializers.SerializerMethodField()
    address = AddressReadSerializer(source="address.address")
    contentType = serializers.ChoiceField(
        choices=list(AVAILABLE_CONTENT_TYPES.values()),
        required=False
    )

    class Meta:
        fields = (
            "id",
            "name",
            "timezone",
            "status",
            "legalEntity",
            "brand",
            "exterior",
            "address",
            "contentType",
            "typeOfPlace",
            "pricePerMonth",
            "code1c",
            "abbreviation",
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

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_["timezone"] = TIMEZONES[value.timezone]
        repr_["broadcast"] = getattr(value.legalEntity, "broadcast", None)
        if "contentType" in repr_:
            key = repr_["contentType"]
            repr_["contentType"] = AVAILABLE_CONTENT_TYPES.get(key, key)
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
