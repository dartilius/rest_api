from rest_framework import serializers

from users.models import CustomUser


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализация одного пользователя."""

    class Meta:
        fields = (
            'id',
            'role',
            'email',
            'phone_number',
            'created'
        )
        read_only_fields = (
            'id',
            'created'
        )
        model = CustomUser

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['full_name'] = {
            'Фамилия': value.last_name,
            'Имя': value.first_name,
            'Отчество': value.middle_name
        } if value.middle_name is not None else {
            'Фамилия': value.last_name,
            'Имя': value.first_name,
        }
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation


class CustomUserListSerializer(serializers.ModelSerializer):
    """Сериализация списка пользователей."""

    class Meta:
        fields = (
            'id',
            'created'
        )
        read_only_fields = (
            'id',
            'created'
        )
        model = CustomUser

    def to_representation(self, value):
        representation = super().to_representation(value)
        representation['full_name'] = (
            f'{value.last_name} '
            f'{value.first_name} '
            f'{value.middle_name}'
        ) if value.middle_name is not None else (
            f'{value.last_name} '
            f'{value.first_name}'
        )
        representation['created'] = value.created.strftime('%Y-%m-%d %H:%M:%S')
        return representation
