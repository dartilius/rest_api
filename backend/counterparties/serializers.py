from rest_framework import serializers

from addresses.models import Address
from brands.models import Brand
from counterparties.models import Counterparty, TYPE_FL, TYPE_ORG, CounterpartyContactInfo
from users.models import CustomUser


class CounterpartyContactInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CounterpartyContactInfo
        fields = "__all__"

class CreateCounterpartySerializer(serializers.ModelSerializer):
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

        if not opf:
            raise serializers.ValidationError({
                "opf": "ОПФ обязательно"
            })

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

        else:
            raise serializers.ValidationError("Неверный ОПФ")

        return data

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['opf'] = value.get_opf_display()
        return repr_


class CounterpartiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counterparty
        fields = '__all__'
        read_only_fields = ('id', 'code1c', 'created')


class CounterpartiesShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор — только id и name."""

    class Meta:
        model = Counterparty
        fields = ("id", "name")


class CounterpartiesListSerializer(serializers.ModelSerializer):
    """Короткий сериализатор"""
    # contact_persons = serializers.PrimaryKeyRelatedField(
    #     read_only=True,
    #     many=True,
    # )

    class Meta:
        model = Counterparty
        fields = ("id", "name", 'contact_persons', 'brands', 'inn')
