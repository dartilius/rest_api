from rest_framework import serializers

from users.models import CustomUser, ROLES


class CustomUserSerializer(serializers.ModelSerializer):
    """Сериализация одного пользователя."""
    class Meta:
        model = CustomUser
        fields = "__all__"
        read_only_fields = (
            'id',
            'created',
            'role'
        )


    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['role'] = value.get_role_display()
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        repr_['full_name'] = {
            'first_name': value.first_name,
            'last_name': value.last_name,
            'middle_name': value.middle_name,
        }
        repr_['contact_info'] = {
            'basic': value.basic,
            'type': value.type,
            'vidtel': value.vidtel,
            'vidmail': value.vidmail,
            'meaning': value.meaning,
            'ext': value.ext,
            'comment': value.comment,
        }
        for field in repr_['full_name']:
            repr_.pop(field)
        for field in repr_['contact_info']:
            repr_.pop(field)
        return repr_


class CustomUserListSerializer(serializers.ModelSerializer):
    """Сериализация списка пользователей."""

    class Meta:
        model = CustomUser

        fields = (
            'id',
            'last_name',
            'first_name',
            'middle_name',
            'email',
            'phone_number',
            'role'
        )
        read_only_fields = (
            'id',
            'created',
            'role'
        )

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        repr_['role'] = value.get_role_display()
        repr_['full_name'] = {
            'first_name': value.first_name,
            'last_name': value.last_name,
            'middle_name': value.middle_name,
        }
        for field in repr_['full_name']:
            repr_.pop(field)
        return repr_

class CustomUserShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'middle_name'
        )
        read_only_fields = 'id'

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['full_name'] = {
            'first_name': value.first_name,
            'last_name': value.last_name,
            'middle_name': value.middle_name,
        }
        for field in repr_['full_name']:
            repr_.pop(field)

        return repr_
