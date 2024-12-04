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
            'first_name',
            'last_name',
            'middle_name'
        )
        read_only_fields = (
            'id',
            'created'
        )
        model = CustomUser

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        return repr_


class CustomUserListSerializer(serializers.ModelSerializer):
    """Сериализация списка пользователей."""

    class Meta:
        fields = (
            'id',
            'role',
            'created'
        )
        read_only_fields = fields
        model = CustomUser

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        return repr_
