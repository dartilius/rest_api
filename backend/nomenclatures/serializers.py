from rest_framework import serializers

from nomenclatures.models import (
    Nomenclature,
    HardWareInfo,
    Settings,
    NomenclatureGroup
)
from users.serializers import UserSerializer

TIMEZONES = {
    "Etc/GMT+11": "UTC -11",
    "Etc/GMT+10": "UTC -10",
    "Etc/GMT+9": "UTC -9",
    "Etc/GMT+8": "UTC -8",
    "Etc/GMT+7": "UTC -7",
    "Etc/GMT+6": "UTC -6",
    "Etc/GMT+5": "UTC -5",
    "Etc/GMT+4": "UTC -4",
    "Etc/GMT+3": "UTC -3",
    "Etc/GMT+2": "UTC -2",
    "Etc/GMT+1": "UTC -1",
    "Etc/GMT+0": "UTC",
    "Etc/GMT-1": "UTC +1",
    "Etc/GMT-2": "UTC +2",
    "Etc/GMT-3": "UTC +3",
    "Etc/GMT-4": "UTC +4",
    "Etc/GMT-5": "UTC +5",
    "Etc/GMT-6": "UTC +6",
    "Etc/GMT-7": "UTC +7",
    "Etc/GMT-8": "UTC +8",
    "Etc/GMT-9": "UTC +9",
    "Etc/GMT-10": "UTC +10",
    "Etc/GMT-11": "UTC +11",
    "Etc/GMT-12": "UTC +12"
}


class HardWareInfoSerializer(serializers.ModelSerializer):
    """Сериализация инфы о железе разбы."""

    class Meta:
        model = HardWareInfo
        fields = (
            'city',
            'model',
            'internet_service_provider',
            'external_ip',
            'network_config',
            'audio_device'
        )


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
    timezone = serializers.SerializerMethodField() # сделать to representation вместо этого
    # hw_info = serializers.SlugRelatedField(
    #     slug_field='client',
    #     queryset=HardWareInfo.objects.filter(client__id=id),
    #     read_only=True
    # )

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
            # 'hw_info',
            'created'
        )
        read_only_fields = (
            'id',
            'owner',
            'is_active',
            # 'hw_info',
            'settings',
            'created'
        )
        model = Nomenclature

    def get_timezone(self, obj):
        """Читаемый часовой пояс."""
        return TIMEZONES[obj.timezone]

    # def get_hw_info(self, obj):
    #     """Получаем информацию о железе."""
    #     return obj.nomenclature_hwinfo.first()


class NomenclatureListSerializer(serializers.ModelSerializer):
    """Сериализация всех номенклатур."""

    timezone = serializers.SerializerMethodField()

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

    def get_timezone(self, obj):
        """Читаемый часовой пояс."""
        return TIMEZONES[obj.timezone]


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
