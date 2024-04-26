from rest_framework import serializers

from nomenclatures.models import (
    Nomenclature,
    HardWareInfo,
    Settings,
    NomenclatureGroup
)
from users.serializers import UserSerializer


class SettingsSerializer(serializers.ModelSerializer):
    """Сериализация настроек номенклатуры."""

    class Meta:
        fields = (
            'days',
            'start_time',
            'end_time',
            'volumes',
            'default_volume'
        )
        model = Settings

    def validate_default_volume(self, value):
        if len(value) != 4:
            raise serializers.ValidationError(
                "Значение громкости по умолчанию должно содержать 4 значения"
            )
        return value


class NomenclatureSerializer(serializers.ModelSerializer):
    """Сериализация одной номенклатуры."""

    owner = UserSerializer(read_only=True)
    settings = SettingsSerializer(many=True, required=False)

    class Meta:
        fields = (
            'id',
            'owner',
            'name',
            'timezone',
            'is_active',
            'status',
            'version',
            'description',
            'settings',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'is_active',
            'status',
            'version',
            'settings',
            'created'
        )
        model = Nomenclature


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализация всех номенклатур."""

    class Meta:
        fields = (
            'id',
            'name',
            'timezone',
            'status',
            'version'
        )
        read_only_fields = fields
        model = Nomenclature


class HardWareInfoSerializer(serializers.ModelSerializer):
    """Сериализация инфы о железе разбы."""

    client = NomenclatureSerializer(read_only=True)

    class Meta:
        model = HardWareInfo
        fields = (
            'client',
            'city',
            'model',
            'internet_service_provider',
            'external_ip',
            'network_config',
            'audio_device'
        )
        read_only_fields = ('client',)


class NomenclatureGroupSerializer(serializers.ModelSerializer):
    """Сериализация групп номенклатуры."""

    clients = NomenclatureSerializer(read_only=True, many=True)
    owner = UserSerializer(read_only=True)

    class Meta:
        fields = (
            'clients',
            'owner',
            'name',
            'description',
            'created'
        )
        read_only_fields = (
            'clients',
            'owner',
            'created'
        )
        model = NomenclatureGroup
