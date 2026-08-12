"""
Сериализаторы для приложения counterparties.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Добавлена поддержка предзагруженных брендов через _prefetched_brands
2. Оптимизированы метод-поля для избежания N+1 запросов
3. Добавлена ленивая загрузка связанных объектов
"""

from typing import List

from rest_framework import serializers

from addresses.models import Address
from brands.models import Brand
from brands.serializers import BrandShortSerializer, BrandListSerializer
from counterparties.models import (
    Counterparty,
    TYPE_FL,
    TYPE_ORG,
    CounterpartyContactInfo,
    CounterpartyCategory,
)
from users.models import CustomUser
from users.serializers import CustomUserShortSerializer


class CounterpartyContactInfoSerializer(serializers.ModelSerializer):
    """
    Сериализатор для контактной информации контрагента.

    ОПТИМИЗАЦИЯ:
    - Использует предзагруженный counterparty через _prefetched_counterparty
    """
    counterparty_name = serializers.SerializerMethodField()

    class Meta:
        model = CounterpartyContactInfo
        fields = "__all__"

    def get_counterparty_name(self, obj):
        """
        Возвращает имя контрагента без лишних запросов.

        Использует предзагруженный counterparty, если он есть.
        """
        if hasattr(obj, '_prefetched_counterparty'):
            return obj._prefetched_counterparty.name
        return obj.counterparty.name


class CreateCounterpartySerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания контрагента.
    """
    name = serializers.SerializerMethodField(read_only=True)
    contacts = CounterpartyContactInfoSerializer(many=True, required=False)
    brands = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Brand.objects.all(),
        required=False,
        write_only=True,
    )
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CounterpartyCategory.objects.filter(is_active=True),
        required=False,
    )
    address = serializers.PrimaryKeyRelatedField(
        queryset=Address.objects.all(),
        required=False,
        allow_null=True,
    )
    contact_persons = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CustomUser.objects.all(),
        write_only=True,
        required=False
    )

    def get_name(self, obj):
        return obj.name

    class Meta:
        model = Counterparty
        fields = "__all__"

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop('contacts', None)
        brands_data = validated_data.pop('brands', None)
        categories_data = validated_data.pop('categories', None)
        contact_persons_data = validated_data.pop('contact_persons', None)

        # Обновляем простые поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Добавляем новые контакты, старые остаются
        if contacts_data:
            for contact in contacts_data:
                exists = instance.contacts.filter(
                    type=contact.get("type"),
                    meaning=contact.get("meaning")
                ).exists()
                if not exists:
                    CounterpartyContactInfo.objects.create(
                        counterparty=instance,
                        **contact
                    )

        # Обновляем ManyToMany связи
        if brands_data is not None:
            instance.brands.set(brands_data)
        if categories_data is not None:
            instance.categories.set(categories_data)
        if contact_persons_data is not None:
            instance.contact_persons.set(contact_persons_data)

        return instance

    def validate(self, data):
        opf = data.get('opf')

        if opf in TYPE_FL:
            required = ["first_name", "last_name"]
            missing = [f for f in required if not data.get(f)]
            if missing:
                raise serializers.ValidationError({
                    f: "Обязательное поле" for f in missing
                })

        elif opf in TYPE_ORG:
            required = ["keyword"]
            missing = [f for f in required if not data.get(f)]
            if missing:
                raise serializers.ValidationError({
                    f: "Обязательное поле" for f in missing
                })

        return data

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['opf'] = value.get_opf_display()
        return repr_


class CounterpartiesSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для контрагента.
    """
    name = serializers.SerializerMethodField(read_only=True)

    def get_name(self, obj):
        return obj.name

    class Meta:
        model = Counterparty
        fields = "__all__"
        read_only_fields = ('id', 'code1c', 'created', 'name')


class CounterpartiesShortSerializer(serializers.ModelSerializer):
    """
    Короткий сериализатор — только id и name.

    ОПТИМИЗАЦИЯ:
    - Использует предзагруженные бренды через _prefetched_brands
    """
    brands = serializers.SerializerMethodField()

    class Meta:
        model = Counterparty
        fields = ("id", "brands", "name", "opf")

    def get_brands(self, obj):
        """
        Возвращает сериализованные бренды без лишних запросов.

        Использует предзагруженные бренды, если они есть.
        """
        if hasattr(obj, '_prefetched_brands'):
            brands = obj._prefetched_brands
        else:
            brands = obj.brands.all()
        return BrandShortSerializer(brands, many=True).data


class TenantsShortSerializer(serializers.ModelSerializer):
    """
    Короткий сериализатор для арендаторов.

    ОПТИМИЗАЦИЯ:
    - Использует предзагруженные бренды через _prefetched_brands
    """
    brands_list = serializers.SerializerMethodField()
    logotypes = serializers.SerializerMethodField()

    class Meta:
        model = Counterparty
        fields = ("id", "brands_list", "logotypes")

    def get_brands_list(self, obj) -> str:
        """
        Возвращает строку с названиями брендов через запятую.

        Использует предзагруженные бренды, если они есть.
        """
        if hasattr(obj, '_prefetched_brands'):
            brands = obj._prefetched_brands
        else:
            brands = obj.brands.all()
        return ", ".join(brand.name for brand in brands)

    def get_logotypes(self, obj) -> list:
        """
        Возвращает массив строк с URL логотипов брендов.

        Использует предзагруженные бренды, если они есть.
        """
        if hasattr(obj, '_prefetched_brands'):
            brands = obj._prefetched_brands
        else:
            brands = obj.brands.all()
        return [
            brand.logotype.url
            for brand in brands
            if brand.logotype
        ]


class CounterpartiesListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для списка контрагентов.
    """
    class Meta:
        model = Counterparty
        fields = ("id", "name", 'contact_persons', 'brands', 'inn')


class FullTenantsSerializer(serializers.ModelSerializer):
    """
    Полный сериализатор для арендаторов.

    ОПТИМИЗАЦИЯ:
    - Использует предзагруженные бренды и контактные лица
    """
    brands = serializers.SerializerMethodField()
    contact_persons = serializers.SerializerMethodField()

    class Meta:
        model = Counterparty
        fields = (
            'id',
            'code1c',
            'opf',
            'inn',
            'first_name',
            'middle_name',
            'last_name',
            'description',
            'keyword',
            'additional_name',
            'broadcast',
            'contact_persons',
            'brands',
            'is_active',
            'created',
        )

    def get_brands(self, obj):
        """Возвращает сериализованные бренды без лишних запросов."""
        if hasattr(obj, '_prefetched_brands'):
            brands = obj._prefetched_brands
        else:
            brands = obj.brands.all()
        return BrandListSerializer(brands, many=True, read_only=True).data

    def get_contact_persons(self, obj):
        """Возвращает сериализованные контактные лица без лишних запросов."""
        if hasattr(obj, '_prefetched_contact_persons'):
            persons = obj._prefetched_contact_persons
        else:
            persons = obj.contact_persons.all()
        return CustomUserShortSerializer(persons, many=True, read_only=True).data


# from typing import List

# from rest_framework import serializers

# from addresses.models import Address
# from brands.models import Brand
# from brands.serializers import BrandShortSerializer, BrandListSerializer
# from counterparties.models import Counterparty, TYPE_FL, TYPE_ORG, CounterpartyContactInfo
# from users.models import CustomUser
# from users.serializers import CustomUserShortSerializer


# class CounterpartyContactInfoSerializer(serializers.ModelSerializer):
#     counterparty_name = serializers.SerializerMethodField()
#     class Meta:
#         model = CounterpartyContactInfo
#         fields = "__all__"

#     def get_counterparty_name(self, obj):
#         return obj.counterparty.name

# class CreateCounterpartySerializer(serializers.ModelSerializer):
#     name = serializers.SerializerMethodField(read_only=True)
#     contacts = CounterpartyContactInfoSerializer(many=True, required=False)
#     brands = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=Brand.objects.all(),
#         required=False,
#         write_only=True,
#     )
#     address = serializers.PrimaryKeyRelatedField(
#         queryset=Address.objects.all(),
#         required=False,
#         allow_null=True,
#     )
#     contact_persons = serializers.PrimaryKeyRelatedField(
#         many=True,
#         queryset=CustomUser.objects.all(),
#         write_only=True,
#         required=False
#     )

#     def get_name(self, obj):
#         return obj.name

#     class Meta:
#         model = Counterparty
#         fields = "__all__"

#     def update(self, instance, validated_data):
#         contacts_data = validated_data.pop('contacts', None)
#         brands_data = validated_data.pop('brands', None)
#         contact_persons_data = validated_data.pop('contact_persons', None)

#         # обновляем простые поля
#         for attr, value in validated_data.items():
#             setattr(instance, attr, value)
#         instance.save()

#         # добавляем новые контакты, старые остаются
#         if contacts_data:
#             for contact in contacts_data:
#                 # проверка на дублирование по type + meaning (можно настроить)
#                 exists = instance.contacts.filter(
#                     type=contact.get("type"),
#                     meaning=contact.get("meaning")
#                 ).exists()
#                 if not exists:
#                     CounterpartyContactInfo.objects.create(
#                         counterparty=instance,
#                         **contact
#                     )

#         # обновляем ManyToMany связи
#         if brands_data is not None:
#             instance.brands.set(brands_data)
#         if contact_persons_data is not None:
#             instance.contact_persons.set(contact_persons_data)

#         return instance

#     def validate(self, data):
#         opf = data.get('opf')

#         if opf in TYPE_FL:
#             required = ["first_name", "last_name"]
#             missing = [f for f in required if not data.get(f)]
#             if missing:
#                 raise serializers.ValidationError({
#                     f: "Обязательное поле" for f in missing
#                 })

#             # ---------- ЮрЛицо ----------
#         elif opf in TYPE_ORG:
#             required = ["keyword"]
#             missing = [f for f in required if not data.get(f)]
#             if missing:
#                 raise serializers.ValidationError({
#                     f: "Обязательное поле" for f in missing
#                 })

#         return data

#     def to_representation(self, value):
#         repr_ = super().to_representation(value)
#         repr_['opf'] = value.get_opf_display()
#         return repr_


# class CounterpartiesSerializer(serializers.ModelSerializer):

#     name = serializers.SerializerMethodField(read_only=True)

#     def get_name(self, obj):
#         return obj.name
#     class Meta:
#         model = Counterparty
#         fields = "__all__"
#         read_only_fields = ('id', 'code1c', 'created', 'name')


# class CounterpartiesShortSerializer(serializers.ModelSerializer):
#     """Короткий сериализатор — только id и name."""

#     brands = BrandShortSerializer(read_only=True, many=True)

#     class Meta:
#         model = Counterparty
#         fields = ("id", "brands", "name", "opf")


# class TenantsShortSerializer(serializers.ModelSerializer):
#     """Короткий сериализатор — только id и кастомное поле с брендами."""

#     brands_list = serializers.SerializerMethodField()
#     logotypes = serializers.SerializerMethodField()

#     class Meta:
#         model = Counterparty
#         fields = ("id", "brands_list", "logotypes")

#     def get_brands_list(self, obj) -> str:
#         """Возвращает строку с названиями брендов через запятую."""
#         brands = [brand.name for brand in obj.brands.all()]
#         return ", ".join(brands)

#     def get_logotypes(self, obj) -> list:
#         """Возвращает массив строк с URL логотипов брендов."""
#         return [
#             brand.logotype.url
#             for brand in obj.brands.all()
#             if brand.logotype
#         ]

# class CounterpartiesListSerializer(serializers.ModelSerializer):
#     """Короткий сериализатор"""
#     # contact_persons = serializers.PrimaryKeyRelatedField(
#     #     read_only=True,
#     #     many=True,
#     # )

#     class Meta:
#         model = Counterparty
#         fields = ("id", "name", 'contact_persons', 'brands', 'inn')

# class FullTenantsSerializer(serializers.ModelSerializer):
#     brands = BrandListSerializer(many=True, read_only=True)
#     contact_persons = CustomUserShortSerializer(many=True, read_only=True)

#     class Meta:
#         model = Counterparty
#         fields = (
#             'id',
#             'code1c',
#             'opf',
#             'inn',
#             'first_name',
#             'middle_name',
#             'last_name',
#             'description',
#             'keyword',
#             'additional_name',
#             'broadcast',
#             'contact_persons',
#             'brands',
#             'is_active',
#             'created',
#         )
