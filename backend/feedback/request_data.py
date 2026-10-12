from collections.abc import Mapping

from rest_framework import serializers

from corporate_broadcast.constants import BUSINESS_TYPES, BroadcastFormat, FORMAT_CONTENT


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown = data.keys() - self.fields.keys()
            if unknown:
                raise serializers.ValidationError({key: ["Неизвестное поле."] for key in sorted(unknown)})
        return super().to_internal_value(data)


class StrictBooleanField(serializers.BooleanField):
    def to_internal_value(self, data):
        if not isinstance(data, bool):
            self.fail("invalid", input=data)
        return data


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, int):
            self.fail("invalid")
        return super().to_internal_value(data)


class ContentSerializer(StrictSerializer):
    music = StrictBooleanField(required=False)
    announcements = StrictBooleanField(required=False)
    ads = StrictBooleanField(required=False)
    jingles = StrictBooleanField(required=False)
    slides = StrictBooleanField(required=False)
    video_content = StrictBooleanField(required=False)
    information = StrictBooleanField(required=False)
    menu = StrictBooleanField(required=False)
    seasonal = StrictBooleanField(required=False)
    promotions = StrictBooleanField(required=False)


class StrictFloatField(serializers.FloatField):
    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, (int, float)):
            self.fail("invalid")
        return super().to_internal_value(data)


class BroadcastRequestDataSerializer(StrictSerializer):
    business_type = serializers.ChoiceField(choices=BUSINESS_TYPES, required=False)
    object_count = StrictIntegerField(min_value=1, max_value=100000, required=False)
    area_per_object = StrictFloatField(min_value=0.01, max_value=10000000, required=False)
    format = serializers.ChoiceField(choices=BroadcastFormat.choices, required=False)
    screens = serializers.ChoiceField(choices=("existing", "needed"), required=False)
    video_content = serializers.ChoiceField(choices=("own", "production", "consultation"), required=False)
    content = ContentSerializer(required=False)

    def validate_area_per_object(self, value):
        import math
        if not math.isfinite(value):
            raise serializers.ValidationError("Укажите конечное положительное число.")
        return value

    def validate(self, attrs):
        selected = attrs.get("format")
        dependent = {"content", "screens", "video_content"} & attrs.keys()
        if dependent and not selected:
            raise serializers.ValidationError({"format": "Укажите формат для параметров контента и экранов."})
        if selected == "audio" and ({"screens", "video_content"} & attrs.keys()):
            raise serializers.ValidationError({key: "Недоступно для аудиовещания." for key in ("screens", "video_content") if key in attrs})
        if selected:
            invalid = {key for key, enabled in attrs.get("content", {}).items() if enabled and key not in FORMAT_CONTENT[selected]}
            if invalid:
                raise serializers.ValidationError({"content": {key: "Недоступно для выбранного формата." for key in sorted(invalid)}})
        return attrs
