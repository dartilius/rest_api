"""Validation boundary for the isolated Content Player v2 protocol."""

from rest_framework import serializers

from nomenclatures.models import StationCommandV2
from nomenclatures.player_v2.playback.serializers import PlaybackEventSerializer
from nomenclatures.player_v2.runtime.serializers import RuntimeSnapshotSerializer, StrictIntegerField
from nomenclatures.player_v2.settings import SettingsPatchError, validate_settings_document


class OrderProgressSerializer(serializers.Serializer):
    """A transient observation, never a readiness or playback receipt."""

    command_id = serializers.UUIDField()
    revision = StrictIntegerField(min_value=1)
    phase = serializers.ChoiceField(choices=("downloading", "verifying", "applying"))
    files_verified = StrictIntegerField(min_value=0, max_value=100000)
    files_total = StrictIntegerField(min_value=1, max_value=100000)

    def validate(self, attrs):
        if attrs["files_verified"] > attrs["files_total"]:
            raise serializers.ValidationError("Verified count exceeds the manifest size.")
        if attrs["phase"] == "downloading" and attrs["files_verified"] != 0:
            raise serializers.ValidationError("Downloading is not integrity verification.")
        if attrs["phase"] == "applying" and attrs["files_verified"] != attrs["files_total"]:
            raise serializers.ValidationError("Applying requires all files to be verified.")
        return attrs


class StationCommandReceiptSerializer(serializers.Serializer):
    """Acknowledge exactly one command delivered to this station."""

    command_id = serializers.UUIDField()
    status = serializers.ChoiceField(
        choices=(
            StationCommandV2.Status.SUPERSEDED,
            StationCommandV2.Status.APPLIED,
            StationCommandV2.Status.FAILED,
        )
    )
    result = serializers.JSONField(required=False, default=dict)

    def validate_result(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("result must be an object.")
        return value


class PlaybackEventErrorSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    code = serializers.ChoiceField(choices=("event_conflict", "station_mismatch", "order_mismatch", "sequence_conflict"))


class StationV2SyncResponseSerializer(serializers.Serializer):
    commands = serializers.ListField(child=serializers.JSONField())
    playback_events_stored = serializers.ListField(child=serializers.UUIDField(), required=False)
    playback_event_errors = PlaybackEventErrorSerializer(many=True, required=False)
    playback_event_storage = serializers.ChoiceField(choices=("postgresql",), required=False)
    runtime_snapshot_received = serializers.JSONField(required=False)


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
    station_protocol = serializers.DictField(required=False)
    playback_events = PlaybackEventSerializer(many=True, required=False, default=list, max_length=100)
    runtime_snapshot = RuntimeSnapshotSerializer(required=False)
    order_progress = OrderProgressSerializer(many=True, required=False, default=list, max_length=100)

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
        protocol = attrs.get("station_protocol")
        if protocol is not None and (
            "unified_orders_version" not in protocol
            or not set(protocol) <= {"unified_orders_version", "advertising_options_version", "background_visual_queue_version", "continuous_advertising_version", "playback_events_version", "order_schedule_version"}
            or type(protocol["unified_orders_version"]) is not int
            or protocol["unified_orders_version"] != 1
            or ("advertising_options_version" in protocol and (
                type(protocol["advertising_options_version"]) is not int
                or protocol["advertising_options_version"] != 1
            ))
            or ("background_visual_queue_version" in protocol and (
                type(protocol["background_visual_queue_version"]) is not int
                or protocol["background_visual_queue_version"] != 1
            ))
            or ("continuous_advertising_version" in protocol and (
                type(protocol["continuous_advertising_version"]) is not int
                or protocol["continuous_advertising_version"] != 1
            ))
            or ("playback_events_version" in protocol and (
                type(protocol["playback_events_version"]) is not int
                or protocol["playback_events_version"] != 1
            ))
            or ("order_schedule_version" in protocol and (
                type(protocol["order_schedule_version"]) is not int
                or protocol["order_schedule_version"] != 1
            ))
        ):
            raise serializers.ValidationError({"station_protocol": "Неподдерживаемая версия команд заказов."})
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
    # Audio enumeration is asynchronous in the desktop player.  Its first
    # polling request can therefore report an honest, as-yet-undiscovered
    # selected output as JSON null.  It is not a device item and must not be
    # validated as one.
    selected_device = value["audio"]["selected_device"]
    if selected_device is not None:
        _validate_capability_items([selected_device], {"id", "name", "is_default"})


def _validate_capability_items(items, allowed_fields):
    for item in items:
        if not isinstance(item, dict) or set(item) != allowed_fields:
            raise serializers.ValidationError("Карта устройств содержит неподдерживаемые поля.")


class StationV2BindingRequestSerializer(serializers.Serializer):
    """A requested station plus an optional previously issued installation ID."""

    nomenclature_id = serializers.UUIDField()
    installation_id = serializers.UUIDField(required=False)
    replace_revoked = serializers.BooleanField(
        required=False, default=False,
        help_text="Повторная привязка отозванной установки только после явного действия пользователя.",
    )
