from rest_framework import serializers

from users.models import CustomUser, ROLES


class CustomUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,        # <-- важно!!!
        allow_blank=False
    )

    email = serializers.CharField(
        write_only=True,
        required=False,  # <-- важно!!!
        allow_blank=False
    )

    class Meta:
        model = CustomUser
        fields = "__all__"
        read_only_fields = (
            'id',
            'created',
            'role',
        )

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        email = validated_data.pop("email", None)
        user = super().create(validated_data)
        if email:
            user.email = email
            user.save(update_fields=["email"])
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user

    def to_representation(self, value):
        repr_ = super().to_representation(value)

        # чтобы не попадало в ответ апишки
        excluded_fields = (
            "is_active",
            "last_login",
            "is_superuser",
            "is_staff",
            "created",
            "groups",
            "user_permissions",
        )

        for field in excluded_fields:
            repr_.pop(field, None)

        repr_['role'] = value.get_role_display()
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        repr_['full_name'] = {
            'first_name': value.first_name,
            'last_name': value.last_name,
            'middle_name': value.middle_name,
        }

        # удаляем старые плоские поля
        for field in repr_['full_name']:
            repr_.pop(field, None)

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
        read_only_fields = ('id',)

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

class RegisterUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
