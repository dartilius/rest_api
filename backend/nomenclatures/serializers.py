# backend/nomenclatures/serializers.py
from datetime import time
from rest_framework import serializers
from django.core.cache import cache
from files.serializers import Base64FileField
from nomenclatures.models import (
    Nomenclature,
    StatusHistory,
    TIMEZONES,
    NomenclatureImage,
    Brand,
    NomenclatureAddress,
)


class AddressSerializer(serializers.ModelSerializer):
    """
    Сериализатор для адресов номенклатуры.

    Attributes:
        city (str): Город
        federalDistrict (str): Федеральный округ
        street (str): Улица
        street_house (str): Номер дома
        building (str): Строение (опционально)
    """

    class Meta:
        model = NomenclatureAddress
        fields = (
            "city",
            "federalDistrict",
            "street",
            "street_house",
            "building",
        )


class BrandCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и обновления брендов.
    Поддерживает загрузку логотипа в формате base64.
    Используется для операций записи (create/update).

    Attributes:
        logo (Base64FileField): Поле для загрузки логотипа в base64
        id (UUID): Уникальный идентификатор (только чтение)
    """

    logo = Base64FileField(write_only=True, required=False)
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Brand
        fields = ("id", "name", "logo")
        read_only_fields = ("id",)
        # Отключаем валидаторы уникальности для корректной работы get_or_create
        extra_kwargs = {
            'name': {'validators': []}
        }

    def validate_name(self, value):
        """
        Валидация имени бренда.
        
        Args:
            value (str): Название бренда

        Returns:
            str: Очищенное название бренда

        Raises:
            ValidationError: Если название пустое
        """
        if not value or not value.strip():
            raise serializers.ValidationError("Наименование бренда не может быть пустым")
        return value.strip()


class BrandSerializer(serializers.ModelSerializer):
    """
    Сериализатор для чтения данных бренда.

    Используется для операций чтения (list/retrieve).

    Attributes:
        id (UUID): Уникальный идентификатор бренда
        name (str): Наименование бренда
        logo (File): URL логотипа
        created (datetime): Дата создания бренда
    """

    class Meta:
        model = Brand
        fields = ("id", "name", "logo", "created")
        read_only_fields = ("id", "created")


class PhotoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для фотографий номенклатуры.

    Attributes:
        id (UUID): Уникальный идентификатор фотографии
        source (File): Файл изображения в base64 (только запись)
        type (str): Тип фотографии (interior/exterior)
        created (datetime): Дата создания
        nomenclature (UUID): Ссылка на номенклатуру
    """

    source = Base64FileField(write_only=True)

    class Meta:
        model = NomenclatureImage
        fields = ("id", "source", "type", "created", "nomenclature")
        read_only_fields = ("id", "created", "nomenclature")


class InNomenclaturePhotoSerializer(serializers.ModelSerializer):
    """
    Упрощенный сериализатор для фотографий внутри номенклатуры.

    Attributes:
        source (File): URL исходного файла фотографии
    """

    class Meta:
        model = NomenclatureImage
        fields = ("source",)
        read_only_fields = ("source",)


class NomenclatureBaseSerializer(serializers.ModelSerializer):
    """
    Базовый сериализатор для номенклатур.

    Предоставляет общие методы для получения статуса и времени последнего ответа.

    Attributes:
        status (int): Текущий статус доступности
        last_answer (str): Время последнего ответа
    """

    status = serializers.SerializerMethodField()
    last_answer = serializers.SerializerMethodField()

    def get_status(self, obj) -> int | None:
        """
        Получает текущий статус доступности номенклатуры.

        Args:
            obj: Объект номенклатуры

        Returns:
            int | None: Код статуса (0, 1, 2) или None
        """
        try:
            return obj.availability.status
        except AttributeError:
            return None

    def get_last_answer(self, obj) -> str:
        """
        Получает время последнего ответа номенклатуры.

        Args:
            obj: Объект номенклатуры

        Returns:
            str: Время последнего ответа или "Не выходила в сеть"
        """
        try:
            return f"{obj.availability.last_answer_date:%Y-%m-%d %H:%M:%S}"
        except AttributeError:
            return "Не выходила в сеть"


class NomenclatureSerializer(NomenclatureBaseSerializer):
    """
    Сериализатор для детального отображения и создания/обновления номенклатуры.
    
    Поддерживает создание/обновление с вложенными полями:
    - brand_data: данные для создания/обновления бренда
    - address: данные адреса номенклатуры
    
    Валидация вложенных полей выполняется отдельно в методах create/update.
    """

    article = serializers.CharField(required=False, allow_blank=True)
    brand = BrandSerializer(read_only=True)  # Только для чтения при выводе
    brand_data = BrandCreateSerializer(write_only=True, required=False)  # Для записи при создании/обновлении
    exterior = serializers.SerializerMethodField()
    interior = serializers.SerializerMethodField()
    address = AddressSerializer()  # Вложенное поле адреса

    class Meta:
        model = Nomenclature
        fields = (
            "id", "owner", "name", "article", "timezone", "status",
            "last_answer", "version", "description", "settings", "hw_info",
            "created", "brand", "brand_data", "interior", "exterior", "address",
            "legalEntity", "contentType", "typeOfPlace", "pricePerMonth",
        )
        read_only_fields = (
            "id", "owner", "hw_info", "version", "created", "status",
            "last_answer", "brand", "interior", "exterior",
        )

    def validate(self, data):
        """
        Валидация данных номенклатуры.
        
        ВАЖНО: Валидация вложенных полей (brand_data, address) 
        выполняется в методах create/update, а не здесь.
        
        Args:
            data (dict): Данные для валидации

        Returns:
            dict: Валидированные данные

        Raises:
            ValidationError: При ошибках валидации основных полей
        """
        # Вызываем родительскую валидацию для основных полей
        validated_data = super().validate(data)
        
        # НЕ валидируем здесь вложенные поля - это сделаем в create/update
        return validated_data

    def create(self, validated_data):
        """
        Создает номенклатуру с обработкой вложенных полей.
        
        Обрабатывает:
        - brand_data: создание/привязка бренда
        - address: создание адреса
        
        Args:
            validated_data (dict): Валидированные данные номенклатуры

        Returns:
            Nomenclature: Созданная номенклатура

        Raises:
            ValidationError: При ошибках валидации вложенных данных
        """
        # Извлекаем вложенные данные из validated_data
        brand_data = validated_data.pop('brand_data', None)
        address_data = validated_data.pop('address', None)
        
        # Создаем основную номенклатуру
        nomenclature = Nomenclature.objects.create(**validated_data)
        
        # Обрабатываем бренд (если передан)
        if brand_data:
            self._process_brand_data(nomenclature, brand_data)
        
        # Обрабатываем адрес (если передан)
        if address_data:
            self._process_address_data(nomenclature, address_data)

        nomenclature.save()
        return nomenclature

    def update(self, instance, validated_data):
        """
        Обновляет номенклатуру с обработкой вложенных полей.
        
        Обрабатывает:
        - brand_data: обновление/привязка бренда
        - address: обновление/создание адреса
        
        Args:
            instance (Nomenclature): Обновляемая номенклатура
            validated_data (dict): Валидированные данные

        Returns:
            Nomenclature: Обновленная номенклатура

        Raises:
            ValidationError: При ошибках валидации вложенных данных
        """
        # Извлекаем вложенные данные из validated_data
        brand_data = validated_data.pop('brand_data', None)
        address_data = validated_data.pop('address', None)
        
        # Обновляем основные поля номенклатуры
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Обрабатываем бренд (если передан)
        if brand_data is not None:  # Важно: проверяем именно на None, а не на bool
            self._process_brand_data(instance, brand_data)
        
        # Обрабатываем адрес (если передан)
        if address_data is not None:  # Важно: проверяем именно на None
            self._process_address_data(instance, address_data)

        instance.save()
        return instance

    def _process_brand_data(self, nomenclature, brand_data):
        """
        Обрабатывает данные бренда для номенклатуры.
        
        Использует get_or_create для поиска существующего бренда
        или создания нового.
        
        Args:
            nomenclature (Nomenclature): Номенклатура для привязки бренда
            brand_data (dict): Данные бренда

        Raises:
            ValidationError: При ошибках валидации данных бренда
        """
        # Валидируем данные бренда
        brand_serializer = BrandCreateSerializer(data=brand_data)
        brand_serializer.is_valid(raise_exception=True)
        
        brand_name = brand_serializer.validated_data['name']
        logo = brand_serializer.validated_data.get('logo')

        # Используем get_or_create для избежания дубликатов
        brand, created = Brand.objects.get_or_create(
            name=brand_name,
            defaults={'logo': logo} if logo else {}
        )

        # Если бренд уже существовал и передан новый логотип - обновляем
        if not created and logo:
            brand.logo = logo
            brand.save()

        nomenclature.brand = brand

    def _process_address_data(self, nomenclature, address_data):
        """
        Обрабатывает данные адреса для номенклатуры.
        
        Создает или обновляет адрес номенклатуры.
        
        Args:
            nomenclature (Nomenclature): Номенклатура для привязки адреса
            address_data (dict): Данные адреса

        Raises:
            ValidationError: При ошибках валидации данных адреса
        """
        # Валидируем данные адреса
        address_serializer = AddressSerializer(data=address_data)
        address_serializer.is_valid(raise_exception=True)
        
        # Проверяем, есть ли уже адрес у номенклатуры
        if hasattr(nomenclature, 'address'):
            # Обновляем существующий адрес
            for attr, value in address_serializer.validated_data.items():
                setattr(nomenclature.address, attr, value)
            nomenclature.address.save()
        else:
            # Создаем новый адрес
            NomenclatureAddress.objects.create(
                nomenclature=nomenclature,
                **address_serializer.validated_data
            )

    def get_interior(self, obj) -> list:
        """
        Получает фотографии интерьера номенклатуры.

        Args:
            obj: Объект номенклатуры

        Returns:
            list: Список сериализованных фотографий интерьера
        """
        interior_images = getattr(obj, 'interior_images', [])
        return InNomenclaturePhotoSerializer(interior_images, many=True).data

    def get_exterior(self, obj) -> list:
        """
        Получает фотографии экстерьера номенклатуры.

        Args:
            obj: Объект номенклатуры

        Returns:
            list: Список сериализованных фотографий экстерьера
        """
        exterior_images = getattr(obj, 'exterior_images', [])
        return InNomenclaturePhotoSerializer(exterior_images, many=True).data

    def to_representation(self, obj):
        """
        Преобразует объект номенклатуры в словарь для сериализации.

        Args:
            obj: Объект номенклатуры

        Returns:
            dict: Сериализованные данные номенклатуры
        """
        repr_ = super().to_representation(obj)

        # Основная информация
        repr_["main_info"] = {
            "name": obj.name,
            "description": obj.description,
            "owner": obj.owner.full_name,
            "timezone": TIMEZONES[obj.timezone],
            "status": self.get_status(obj),
            "last_answer": self.get_last_answer(obj),
            "version": obj.version,
            "created": f"{obj.created:%Y-%m-%d %H:%M:%S}",
        }

        # Удаляем дублирующиеся поля
        for field in repr_["main_info"]:
            if field in repr_:
                repr_.pop(field)

        # Форматирование настроек
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

        return repr_

class NomenclatureListSerializer(NomenclatureBaseSerializer):
    """
    Сериализатор для списка номенклатур.

    Используется для отображения краткой информации.
    Только для чтения.

    Attributes:
        article (str): Артикул номенклатуры (может быть пустым)
        brand (BrandSerializer): Данные бренда
        exterior (list): Список фотографий экстерьера
        address (AddressSerializer): Данные адреса
    """

    article = serializers.CharField(required=False, allow_blank=True)
    brand = BrandSerializer(read_only=True)
    exterior = serializers.SerializerMethodField()
    address = AddressSerializer()

    class Meta:
        model = Nomenclature
        fields = (
            "id", "article", "name", "timezone", "status", "last_answer",
            "version", "brand", "exterior", "address", "legalEntity",
            "contentType", "typeOfPlace", "pricePerMonth",
        )
        read_only_fields = fields

    def get_exterior(self, obj) -> list:
        """
        Получает фотографии экстерьера для списка номенклатур.

        Args:
            obj: Объект номенклатуры

        Returns:
            list: Список сериализованных фотографий экстерьера
        """
        exterior_images = getattr(obj, 'exterior_images', [])
        return InNomenclaturePhotoSerializer(exterior_images, many=True).data

    def to_representation(self, value):
        """
        Преобразует объект номенклатуры для списка.

        Args:
            value: Объект номенклатуры

        Returns:
            dict: Сериализованные данные для списка
        """
        repr_ = super().to_representation(value)
        repr_["timezone"] = TIMEZONES[value.timezone]
        return repr_


class StatusHistorySerializer(serializers.ModelSerializer):
    """
    Сериализатор для истории изменений статуса доступности.

    Attributes:
        change_time (str): Время изменения статуса
        status (int): Код статуса (0, 1, 2)
    """

    class Meta:
        model = StatusHistory
        fields = ("change_time", "status")
        read_only_fields = fields

    def to_representation(self, value):
        """
        Преобразует время изменения в читаемый формат.

        Args:
            value: Объект истории статуса

        Returns:
            dict: Сериализованные данные истории
        """
        repr_ = super().to_representation(value)
        repr_["change_time"] = f"{value.change_time:%Y-%m-%d %H:%M:%S}"
        return repr_
