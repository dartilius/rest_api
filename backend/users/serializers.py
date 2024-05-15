from rest_framework import serializers

from users.models import User


class UserSerializer(serializers.ModelSerializer):
    """Сериализация пользователей."""

    class Meta:
        fields = (
            'id',
            'username',
            'last_name',
            'first_name',
            'middle_name',
            'role',
            'email',
            'phone_number',
        )
        read_only_fields = ('id',)
        model = User
        ref_name = 'UserCustom'
