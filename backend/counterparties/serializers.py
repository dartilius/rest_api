from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from contact_persons.models import Contact
from contact_persons.serializers import ContactSerializer
from counterparties.models import Counterparties


class CounterpartiesCreateSerializer(serializers.ModelSerializer):
    contact_persons = ContactSerializer(read_only=True, many=True)
    contact_persons_id = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        source='contact_person',
        allow_null=True,
        queryset=Contact.active.all()
    )
    class Meta:
        model = Counterparties
        fields = '__all__'
        read_only_fields = ('id', 'code1c', 'created', 'contact_persons')

    def validate(self, attrs):
        code1c = attrs.get("code1c")
        name = attrs.get("name")
        if code1c:
            old_counterparties = Counterparties.active().filter(code1c=code1c)
            if old_counterparties:
                # Логируем попытку
                with open('/app/network_logs/counterparties_conflicts.log', 'a', encoding='utf-8') as f:
                    f.write(f'{name}: {old_counterparties.id}, {getattr(old_counterparties, "code1c", "—")}\n')

                # Ошибка валидации
                raise ValidationError({
                    "error": "Brand with this code1c already exists",
                    "existing_brand_id": old_counterparties.id,
                    "existing_brand_name": old_counterparties.name,
                    "existing_brand_code1c": old_counterparties.code1c,
                    "message": f"Бренд с кодом '{code1c}' уже существует (id={old_counterparties.id}, name='{old_counterparties.name}')",
                })
        return attrs

class CounterpartiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Counterparties
        fields = '__all__'
        read_only_fields = ('id', 'code1c', 'created')

class CounterpartiesShortSerializer(serializers.ModelSerializer):
    """Короткий сериализатор — только id и name."""

    class Meta:
        model = Counterparties
        fields = ("id", "name", "code1c")