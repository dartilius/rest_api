from rest_framework import serializers
import re
from users.models import CustomUser, ROLES, ContactInfo
from django.db import transaction
from files.serializers import Base64FileField

class UserContactInfoSerializer(serializers.ModelSerializer):
    """Сериализация и валидация контактной информации."""
    user_name = serializers.SerializerMethodField()
    class Meta:
        model = ContactInfo
        fields = "__all__"
    def get_user_name(self, obj):
        return obj.user.full_name

    def validate(self, attrs):
        type_ = attrs.get("type")
        meaning = attrs.get("meaning")
        vidtel = attrs.get("vidtel")
        vidmail = attrs.get("vidmail")

        if not type_:
            raise serializers.ValidationError({"type": "Поле type обязательно."})

        if type_ == "phone":
            if not meaning or not re.match(r"^\+?[0-9\-\(\) ]+$", meaning):
                raise serializers.ValidationError({"meaning": "Значение должно быть корректным номером телефона."})
            if not vidtel:
                raise serializers.ValidationError({"vidtel": "Для типа 'Телефон' нужно указать вид телефона."})
            attrs["vidmail"] = None  # очищаем vidmail

        elif type_ == "mail":
            if not meaning or not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", meaning):
                raise serializers.ValidationError({"meaning": "Значение должно быть корректным адресом электронной почты."})
            if not vidmail:
                raise serializers.ValidationError({"vidmail": "Для типа 'Почта' нужно указать вид почты."})
            attrs["vidtel"] = None  # очищаем vidtel

        else:
            # Для остальных типов очищаем поля телефона/почты
            attrs["vidtel"] = None
            attrs["vidmail"] = None

        return attrs

class CustomUserSerializer(serializers.ModelSerializer):
    """Полная сериализация пользователя."""

    password = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False
    )
    email = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=False
    )

    contacts_cp = UserContactInfoSerializer(many=True, required=False)

    avatar = Base64FileField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = CustomUser
        fields = (
            "id",
            "email",
            "phone_number",
            "first_name",
            "last_name",
            "middle_name",
            "avatar",
            "role",
            "created",
            "code1c",
            "password",
            "contacts_cp",   # ← ВАЖНО
        )
        read_only_fields = ('id', 'created', 'role')

    def create(self, validated_data):
        contacts_data = validated_data.pop("contacts_cp", [])
        password = validated_data.pop("password", None)
        email = validated_data.pop("email", None)
        user = super().create(validated_data)
        if email:
            user.email = email
            user.save(update_fields=["email"])
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])

        for contact in contacts_data:
            ContactInfo.objects.create(user=user, **contact)
        return user

    def update(self, instance, validated_data):
        contacts_data = validated_data.pop("contacts_cp", None)

        # обычные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # ⬇️ ДОБАВЛЯЕМ, А НЕ УДАЛЯЕМ
        if contacts_data:
            with transaction.atomic():
                for contact in contacts_data:
                    # защита от дублей
                    exists = instance.contacts_cp.filter(
                        type=contact["type"],
                        meaning=contact["meaning"]
                    ).exists()

                    if exists:
                        continue

                    # если basic=true — сбрасываем предыдущий
                    if contact.get("basic"):
                        instance.contacts_cp.filter(
                            type=contact["type"],
                            basic=True
                        ).update(basic=False)

                    ContactInfo.objects.create(
                        user=instance,
                        **contact
                    )

        return instance

    def to_representation(self, value):
        repr_ = super().to_representation(value)

        # Убираем лишние поля
        excluded_fields = (
            "is_active",
            "last_login",
            "is_superuser",
            "is_staff",
            "created",
            "groups",
            "user_permissions",
            "avatar"
        )
        for field in excluded_fields:
            repr_.pop(field, None)

        # Добавляем role и дату
        repr_['role'] = value.get_role_display()
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'

        # Собираем full_name как словарь
        main_info = {
            'first_name': value.first_name,
            'last_name': value.last_name,
            'middle_name': value.middle_name,
            'avatar': value.avatar.url if value.avatar else None,
        }
        repr_['full_name'] = main_info

        # Удаляем старые плоские поля
        for field in main_info.keys():
            repr_.pop(field, None)

        return repr_

class CustomUserListSerializer(serializers.ModelSerializer):
    """Список пользователей (короткая форма)."""

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'last_name',
            'first_name',
            'middle_name',
            'email',
            'phone_number',
            'role',
        )
        read_only_fields = ('id', 'created', 'role')

    def to_representation(self, value):
        repr_ = super().to_representation(value)
        repr_['created'] = f'{value.created:%Y-%m-%d %H:%M:%S}'
        repr_['role'] = value.get_role_display()

        full_name_dict = {
            'first_name': value.first_name,
            'last_name': value.last_name,
            'middle_name': value.middle_name,
        }
        repr_['full_name'] = full_name_dict

        # Удаляем старые плоские поля
        for field in full_name_dict.keys():
            repr_.pop(field, None)

        return repr_


class CustomUserShortSerializer(serializers.ModelSerializer):
    """Минимальная форма пользователя для списка."""

    class Meta:
        model = CustomUser
        fields = ('id', 'last_name', 'first_name', 'middle_name')
        read_only_fields = ('id',)

    def to_representation(self, value):
        repr_ = super().to_representation(value)

        full_name_dict = {
            'first_name': value.first_name,
            'last_name': value.last_name,
            'middle_name': value.middle_name,
        }
        repr_['full_name'] = full_name_dict

        # Удаляем плоские поля
        for field in full_name_dict.keys():
            repr_.pop(field, None)

        return repr_
class RegisterUserSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

class ManagerSerializer(serializers.ModelSerializer):
    """Сериализатор для менеджера — только id и ФИО."""

    class Meta:
        model = CustomUser
        fields = ('id', 'first_name',)

    def to_representation(self, value):
        repr_ = super().to_representation(value)

        full_name_dict = {
            'name': value.first_name,
        }
        repr_['full_name'] = full_name_dict

        # Удаляем плоские поля
        for field in full_name_dict.keys():
            repr_.pop(field, None)

        return repr_

class PasswordResetByEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    new_password_confirm = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError(
                {"new_password_confirm": "Пароли не совпадают."}
            )
        return attrs