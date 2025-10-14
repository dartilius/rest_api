from rest_framework import serializers
from .models import Contact, ContactInformation


class ContactInformationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactInformation
        fields = (
            "id",
            "basic",
            "type",
            "vidtel",
            "vidmail",
            "meaning",
            "ext",
            "comment",
        )
        read_only_fields = ("id",)


class ContactSerializer(serializers.ModelSerializer):
    contact_info = ContactInformationSerializer(many=True)

    class Meta:
        model = Contact
        fields = (
            "id",
            "vid",
            "last_name",
            "first_name",
            "surname",
            "role",
            "job_title",
            "gender",
            "date_of_birth",
            "other",
            "nomenclatures",
            "active",
            "created",
            "updated",
            "contact_info",
        )
        read_only_fields = ("id", "active", "created", "updated")

    def create(self, validated_data):
        contact_info_data = validated_data.pop("contact_info", [])
        existing = Contact.objects.filter(
            last_name=validated_data.get("last_name"),
            first_name=validated_data.get("first_name"),
            active=True
        ).first()
        if existing:
            # Возвращаем существующий контакт
            raise serializers.ValidationError({
                "detail": "Контакт уже существует",
                "contact": ContactSerializer(existing).data
            })

        contact = Contact.objects.create(**validated_data)
        for info_data in contact_info_data:
            ContactInformation.objects.create(contact=contact, **info_data)
        return contact

    def update(self, instance, validated_data):
        contact_info_data = validated_data.pop("contact_info", [])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Обновляем контактную информацию
        for info_data in contact_info_data:
            info_id = info_data.get("id", None)
            if info_id:
                info_instance = ContactInformation.objects.get(id=info_id, contact=instance)
                for key, value in info_data.items():
                    setattr(info_instance, key, value)
                info_instance.save()
            else:
                ContactInformation.objects.create(contact=instance, **info_data)

        return instance
