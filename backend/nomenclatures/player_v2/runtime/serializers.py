"""Bounded runtime frames shared by WebSocket and the polling reserve."""

import math

from rest_framework import serializers


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if type(data) is not int:
            self.fail("invalid")
        return super().to_internal_value(data)


class RuntimeItemSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=512)
    type = serializers.JSONField(required=False)
    status = serializers.CharField(max_length=64, required=False)
    duration_ms = serializers.FloatField(min_value=0, max_value=9_007_199_254_740_991, required=False)
    position_ms = serializers.FloatField(min_value=0, max_value=9_007_199_254_740_991, required=False)
    order_id = serializers.CharField(max_length=64, required=False, allow_blank=True, allow_null=True)
    order_revision = StrictIntegerField(min_value=1, required=False)

    def to_internal_value(self, data):
        if isinstance(data, dict) and any(type(data.get(key)) is bool for key in ("duration_ms", "position_ms")):
            raise serializers.ValidationError("Time must be numeric, not boolean.")
        return super().to_internal_value(data)

    def validate_type(self, value):
        if type(value) is int and value in range(4):
            return value
        if isinstance(value, str) and len(value) <= 64:
            return value
        raise serializers.ValidationError("Unsupported content type.")

    def validate(self, attrs):
        for name in ("duration_ms", "position_ms"):
            if name in attrs and not math.isfinite(attrs[name]):
                raise serializers.ValidationError("Invalid duration.")
        return attrs


class RuntimeStateSerializer(serializers.Serializer):
    mode = serializers.CharField(max_length=64)
    maintenance_mode = serializers.BooleanField()
    current_ad = RuntimeItemSerializer(required=False, allow_null=True)
    background = RuntimeItemSerializer(many=True, max_length=16, required=False, default=list)
    last_error = serializers.CharField(max_length=1024, required=False, allow_null=True, allow_blank=True)

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - set(self.fields):
            raise serializers.ValidationError("Only playback state is allowed here.")
        if type(data.get("maintenance_mode")) is not bool:
            raise serializers.ValidationError("maintenance_mode must be boolean.")
        return super().to_internal_value(data)


class RuntimeSnapshotSerializer(serializers.Serializer):
    stream_id = serializers.UUIDField()
    sequence = StrictIntegerField(min_value=1, max_value=9_223_372_036_854_775_807)
    state = RuntimeStateSerializer()
