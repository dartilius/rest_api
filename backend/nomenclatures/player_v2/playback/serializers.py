"""Strict immutable wire contract for lifecycle events."""

from datetime import datetime

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field

from nomenclatures.player_v2.playback.models import PlaybackEvent


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if type(data) is not int:
            self.fail("invalid")
        return super().to_internal_value(data)


@extend_schema_field({"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", "example": "2026-10-05 09:00:00"})
class LocalPlaybackTimeField(serializers.Field):
    def to_internal_value(self, data):
        try:
            if not isinstance(data, str):
                raise ValueError
            value = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
            if value.strftime("%Y-%m-%d %H:%M:%S") != data:
                raise ValueError
            return value
        except ValueError as exc:
            raise serializers.ValidationError("Ожидается YYYY-MM-DD HH:MM:SS без часового пояса.") from exc


class PlaybackEventSerializer(serializers.Serializer):
    event_id = serializers.UUIDField()
    station_id = serializers.UUIDField()
    playback_id = serializers.UUIDField()
    event_sequence = StrictIntegerField(min_value=1, max_value=2_147_483_647)
    event_type = serializers.ChoiceField(choices=PlaybackEvent.Type.choices)
    occurred_at = LocalPlaybackTimeField()
    media_type = serializers.ChoiceField(choices=PlaybackEvent.Media.choices)
    file_id = serializers.UUIDField()
    order_id = serializers.UUIDField(allow_null=True)
    order_revision = StrictIntegerField(allow_null=True, min_value=1, max_value=2_147_483_647)
    position_ms = StrictIntegerField(min_value=0, max_value=9_007_199_254_740_991)
    duration_ms = StrictIntegerField(min_value=0, max_value=9_007_199_254_740_991)
    reason = serializers.CharField(allow_null=True, allow_blank=True, max_length=512, trim_whitespace=False)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) != set(self.fields):
            raise serializers.ValidationError("Некорректные поля события эфира.")
        return super().to_internal_value(data)

    def validate(self, attrs):
        if (attrs["order_id"] is None) != (attrs["order_revision"] is None):
            raise serializers.ValidationError("Заказ и его редакция передаются вместе.")
        if attrs["event_type"] == "started" and attrs["event_sequence"] != 1:
            raise serializers.ValidationError("Начало должно иметь номер 1.")
        if attrs["event_sequence"] == 1 and attrs["event_type"] not in ("started", "error"):
            raise serializers.ValidationError("Первое событие — начало или ошибка запуска.")
        return attrs
