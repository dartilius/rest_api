"""Validation boundary for the isolated Content Player v2 protocol."""

from rest_framework import serializers

from nomenclatures.models import StationCommandV2
from nomenclatures.settings_patch import SettingsPatchError, validate_settings_document


class StationCommandReceiptSerializer(serializers.Serializer):
    """Acknowledge exactly one command delivered to this station."""

    command_id = serializers.UUIDField()
    status = serializers.ChoiceField(
        choices=(
            StationCommandV2.Status.APPLIED,
            StationCommandV2.Status.FAILED,
        )
    )
    result = serializers.JSONField(required=False, default=dict)

    def validate_result(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("result must be an object.")
        return value


class StationV2SyncRequestSerializer(serializers.Serializer):
    """Incoming polling request with a bounded batch of receipts."""

    receipts = StationCommandReceiptSerializer(
        many=True,
        required=False,
        default=list,
        max_length=100,
    )
    applied_settings = serializers.JSONField(required=False)
    applied_settings_revision = serializers.IntegerField(required=False, min_value=0)
    station_capabilities = serializers.JSONField(required=False)
    applied_visual_output = serializers.JSONField(required=False)

    def validate(self, attrs):
        settings = attrs.get("applied_settings")
        revision = attrs.get("applied_settings_revision")
        if (settings is None) != (revision is None):
            raise serializers.ValidationError(
                "Настройки Player и их версия передаются только вместе."
            )
        if settings is not None:
            try:
                validate_settings_document(settings)
            except SettingsPatchError as exc:
                raise serializers.ValidationError({"applied_settings": str(exc)}) from exc
        capabilities = attrs.get("station_capabilities")
        if capabilities is not None:
            _validate_station_capabilities(capabilities)
        visual_output = attrs.get("applied_visual_output")
        if visual_output is not None:
            _validate_visual_output(visual_output)
        return attrs


def _validate_visual_output(value):
    if not isinstance(value, dict) or set(value) != {"rotation"}:
        raise serializers.ValidationError("Некорректные настройки визуального вывода.")
    if isinstance(value["rotation"], bool) or value["rotation"] not in (0, 90, 180, 270):
        raise serializers.ValidationError("Недопустимый поворот визуального вывода.")


def _validate_station_capabilities(value):
    """Принимает только минимальную карту устройств, без характеристик ПК."""
    if not isinstance(value, dict) or set(value) != {
        "inventory_version",
        "system",
        "displays",
        "audio",
    }:
        raise serializers.ValidationError("Некорректная структура доступных устройств.")
    if value["inventory_version"] != 2:
        raise serializers.ValidationError("Неподдерживаемая версия карты устройств.")
    if value["system"] not in ({"os": "Windows"}, {"os": "Linux"}, {"os": "macOS"}):
        raise serializers.ValidationError("Укажите только поддерживаемый тип ОС.")
    if not isinstance(value["displays"], list) or len(value["displays"]) > 16:
        raise serializers.ValidationError("Некорректный список экранов.")
    if not isinstance(value["audio"], dict) or set(value["audio"]) != {
        "devices",
        "selected_device",
    }:
        raise serializers.ValidationError("Некорректный список аудиовыходов.")
    if not isinstance(value["audio"]["devices"], list) or len(value["audio"]["devices"]) > 64:
        raise serializers.ValidationError("Некорректный список аудиовыходов.")
    _validate_capability_items(value["displays"], {"id", "name", "is_primary", "width", "height", "supported_rotations"})
    _validate_capability_items(value["audio"]["devices"], {"id", "name", "is_default"})
    _validate_capability_items([value["audio"]["selected_device"]], {"id", "name", "is_default"})


def _validate_capability_items(items, allowed_fields):
    for item in items:
        if not isinstance(item, dict) or set(item) != allowed_fields:
            raise serializers.ValidationError("Карта устройств содержит неподдерживаемые поля.")


class StationV2BindingRequestSerializer(serializers.Serializer):
    """A requested station plus an optional previously issued installation ID."""

    nomenclature_id = serializers.UUIDField()
    installation_id = serializers.UUIDField(required=False)
