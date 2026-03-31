from typing import List

from rest_framework import serializers

from addresses.models import Address
from brands.models import Brand
from brands.serializers import BrandShortSerializer, BrandSerializer
from counterparties.models import Counterparty, TYPE_FL, TYPE_ORG, CounterpartyContactInfo
from users.models import CustomUser
from users.serializers import CustomUserShortSerializer


class CounterpartyContactInfoSerializer(serializers.ModelSerializer):
    counterparty_name = serializers.SerializerMethodField()
    class Meta:
        model = CounterpartyContactInfo
        fields = "__all__"

    def get_counterparty_name(self, obj):
        return obj.counterparty.name

class CreateCounterpartySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField(read_only=True)
    contacts = CounterpartyContactInfoSerializer(many=True, required=False)
    brands = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Brand.objects.all(),
        required=False,
        write_only=True,
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
        contact_persons_data = validated_data.pop('contact_persons', None)

        # обновляем простые поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # добавляем новые контакты, старые остаются
        if contacts_data:
            for contact in contacts_data:
                # проверка на дублирование по type + meaning (можно настроить)
                exists = instance.contacts.filter(
                    type=contact.get("type"),
                    meaning=contact.get("meaning")
                ).exists()
                if not exists:
                    CounterpartyContactInfo.objects.create(
                        counterparty=instance,
                        **contact
                    )

        # обновляем ManyToMany связи
        if brands_data is not None:
            instance.brands.set(brands_data)
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

            # ---------- ЮрЛицо ----------
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

    name = serializers.SerializerMethodField(read_only=True)

    def get_name(self, obj):
        return obj.name
    class Meta:
        model = Counterparty
        fields = (
            'id', 'name', 'code1c', 'brands', 'contact_persons', 'broadcast',
            'opf', 'inn', 'address'
        )
        read_only_fields = ('id', 'code1c', 'created', 'name')


class CounterpartiesShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор — только id и name."""

    brands = BrandShortSerializer(read_only=True, many=True)

    class Meta:
        model = Counterparty
        fields = ("id", "brands", "name", "opf")


class TenantsShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор — только id и кастомное поле с брендами."""

    brands_list = serializers.SerializerMethodField()
    logotypes = serializers.SerializerMethodField()

    class Meta:
        model = Counterparty
        fields = ("id", "brands_list", "logotypes")

    def get_brands_list(self, obj) -> str:
        """Возвращает строку с названиями брендов через запятую."""
        brands = [brand.name for brand in obj.brands.all()]
        return ", ".join(brands)

    def get_logotypes(self, obj) -> list:
        """Возвращает массив строк с URL логотипов брендов."""
        return [
            brand.logotype.url
            for brand in obj.brands.all()
            if brand.logotype
        ]

class CounterpartiesListSerializer(serializers.ModelSerializer):
    """Короткий сериализатор"""
    # contact_persons = serializers.PrimaryKeyRelatedField(
    #     read_only=True,
    #     many=True,
    # )

    class Meta:
        model = Counterparty
        fields = ("id", "name", 'contact_persons', 'brands', 'inn')

class FullTenantsSerializer(serializers.ModelSerializer):
    brands = BrandSerializer(many=True, read_only=True)
    contact_persons = CustomUserShortSerializer(many=True, read_only=True)

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