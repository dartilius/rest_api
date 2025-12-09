from rest_framework import serializers

from addresses.models import Address
from brands.models import Brand
from counterparties.models import Counterparty, TYPE_FL, TYPE_ORG
from users.models import CustomUser


class CreateCounterpartySerializer(serializers.ModelSerializer):

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
    )

    class Meta:
        model = Counterparty
        fields = [
            'id', 'code1c', 'opf', "first_name",
            'description', 'keyword', "last_name", "middle_name",
            'contact_persons', 'brands', 'address', 'name', 'inn'
        ]
        # extra_kwargs = {
        #     "first_name": {"required": False},
        #     "last_name": {"required": False},
        #     "middle_name": {"required": False},
        #     "keyword": {"required": False},
        # }

    # def to_internal_value(self, data):
    #     """
    #     кастомные поля для создания имени КА (для фронта)
    #     - ФЛ: fullName {first_name, middle_name, last_name}
    #     - ЮрЛица: без изменений
    #     """
    #     opf = data.get('opf')
    #     data = data.copy()
    #     data['contact_persons'] = data.get('contactPersons')
    #     # FL — fullName → поля модели
    #     if opf in TYPE_FL:
    #         data["first_name"] = data.get("firstName")
    #         data["middle_name"] = data.get("middleName")
    #         data["last_name"] = data.get("lastName")
    #
    #         # keyword создаём автоматически
    #         data["keyword"] = " ".join(filter(None, [
    #             data.get("first_name"),
    #             data.get("middle_name"),
    #             data.get("last_name"),
    #         ]))
    #
    #     return super().to_internal_value(data)

    def validate(self, data):
        opf = data.get('opf')

        if not opf:
            raise serializers.ValidationError({
                "opf": "ОПФ обязательно"
            })

        if opf in TYPE_FL:
            required = ["first_name", "last_name", "contact_persons"]
            missing = [f for f in required if not data.get(f)]
            if missing:
                raise serializers.ValidationError({
                    f: "Обязательное поле" for f in missing
                })

            # ---------- ЮрЛицо ----------
        elif opf in TYPE_ORG:
            required = ["keyword", "contact_persons"]
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
