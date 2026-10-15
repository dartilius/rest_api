"""Сериализаторы единых заказов фона и рекламы."""

from collections.abc import Mapping

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, extend_schema_serializer

from files.models import Playlist
from nomenclatures.models import Nomenclature
from orders.models import Order
from orders.services.order_audio_images import (
    AUDIO_IMAGES_PARAMETER,
    get_order_audio_images,
    public_order_parameters,
    validate_order_audio_images,
    with_order_audio_images,
)
from orders.services.unified_order_input import (
    normalize_public_order_input,
    validate_unified_order_attributes,
)


AUDIO_IMAGES_SCHEMA = {
    "type": "object",
    "description": (
        "Объект {UUID аудиофайла: [UUID картинки, ...]}. "
        "Ключ — id аудиофайла из выбранного плейлиста; массив — id картинок в порядке показа. "
        "additionalProp1, additionalProp2 — автоматические заглушки документации, "
        "вместо них укажите UUID аудиофайлов."
    ),
    "additionalProperties": {
        "type": "array",
        "items": {"type": "string", "format": "uuid"},
    },
    "example": {
        "00000000-0000-0000-0000-000000000011": [
            "00000000-0000-0000-0000-000000000021",
            "00000000-0000-0000-0000-000000000022",
        ],
        "00000000-0000-0000-0000-000000000012": [
            "00000000-0000-0000-0000-000000000023",
        ],
    },
}


@extend_schema_field(AUDIO_IMAGES_SCHEMA)
class OrderAudioImagesField(serializers.JSONField):
    """JSON-карта привязок с понятным UUID-примером в документации."""


def public_order_errors(detail):
    """Ошибки общей проверки показываем с именами полей публичного запроса."""
    if not isinstance(detail, Mapping):
        return detail
    aliases = {"placement": "type", "nomenclature": "clients", "playback_policy": "broadcast_type"}
    result = {}
    interval = {}
    for field, errors in detail.items():
        if field in {"starts_at", "ends_at"}:
            interval[{"starts_at": "lower", "ends_at": "upper"}[field]] = errors
        else:
            result[aliases.get(field, field)] = errors
    if interval:
        result["broadcast_interval"] = interval
    return result


@extend_schema_field({
    "type": "string",
    "pattern": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$",
    "example": "2026-09-30 13:04:00",
})
class LocalOrderDateTimeField(serializers.DateTimeField):
    """Локальные даты в JSON и OpenAPI имеют один формат."""

    def __init__(self, **kwargs):
        super().__init__(format="%Y-%m-%d %H:%M:%S", input_formats=("%Y-%m-%d %H:%M:%S",), **kwargs)


@extend_schema_serializer(exclude_fields=("placement", "nomenclature", "playback_policy", "starts_at", "ends_at", "slides"))
class UnifiedOrderSerializer(serializers.ModelSerializer):
    """Публичный запрос заказа с единым массивом целевых номенклатур."""

    type = serializers.ChoiceField(
        choices=(("bg", "Фоновый контент"), ("ad", "Реклама")),
        required=False,
        write_only=True,
        help_text="Вид заказа: bg — фон, ad — реклама.",
    )
    clients = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        write_only=True,
        min_length=1,
        help_text="UUID номенклатур: массив из одной или нескольких активных точек.",
    )
    broadcast_interval = serializers.JSONField(
        required=False,
        write_only=True,
        help_text="Период заказа: объект {lower, upper} с локальными датами начала и окончания.",
    )
    broadcast_type = serializers.IntegerField(
        required=False,
        write_only=True,
        help_text="Тип рекламного расписания от 0 до 7; значение 7 означает непрерывную рекламу.",
    )

    # Поля модели заполняет преобразование публичного запроса.
    placement = serializers.ChoiceField(
        choices=("background", "advertising"), required=False, write_only=True,
    )
    playback_policy = serializers.CharField(required=False, write_only=True)
    nomenclature = serializers.PrimaryKeyRelatedField(
        queryset=Nomenclature.active.all(), required=False, write_only=True,
    )
    playlist = serializers.PrimaryKeyRelatedField(
        queryset=Playlist.objects.all(),
        help_text="UUID плейлиста с роликами и их порядком воспроизведения.",
    )
    created = LocalOrderDateTimeField(read_only=True)
    starts_at = LocalOrderDateTimeField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Локальные дата и время без часового пояса: YYYY-MM-DD HH:MM:SS, например 2026-09-25 09:00:00. Для рекламы обязательно. У фона пусто — начать после доставки заказа Player.",
    )
    ends_at = LocalOrderDateTimeField(
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Локальные дата и время без часового пояса: YYYY-MM-DD HH:MM:SS. Для рекламы обязательно. Для бессрочного фона можно не передавать или передать null. При переводе в бессрочный фон прежнее окончание очищается, если поле не передано.",
    )
    is_permanent = serializers.BooleanField(
        required=False,
        help_text="true — бессрочный резервный фон: type=bg, broadcast_interval.upper=null.",
    )
    suppress_background_audio = serializers.BooleanField(
        required=False,
        help_text="Для рекламы: true — отключить фоновую музыку. При broadcast_type=7 определяется по audio_muted.",
    )
    suppress_background_visual = serializers.BooleanField(
        required=False,
        help_text="Для рекламы: true — скрыть визуальный фон. При broadcast_type=7 всегда true.",
    )
    parameters = serializers.JSONField(
        required=False,
        help_text=(
            "Расписание рекламы. При broadcast_type=7 times_in_hour не нужен; "
            "для остальных типов times_in_hour — число выходов за час от 1 до 60. "
            "Типы 1 и 2 требуют timedelta, тип 3 — start_time и end_time, "
            "тип 4 — end_time, тип 5 — start_time. Формат времени: HH:MM:SS."
            " audio_muted: true отключает звук рекламного ролика; по умолчанию false. weight — целое число 0–100."
            " Для визуального фона image_duration_seconds — время показа каждой картинки, целое число 1–86400;"
            " без него используется настройка Player. weekdays — выбранные дни недели: JSON-массив уникальных"
            " целых чисел от 0 (понедельник) до 6 (воскресенье). Если ключ не передан, заказ работает каждый день."
        ),
    )
    audio_images = OrderAudioImagesField(
        required=False,
        write_only=True,
        help_text=AUDIO_IMAGES_SCHEMA["description"],
    )
    slides = serializers.JSONField(
        required=False,
        write_only=True,
        help_text="Совместимый входной alias поля audio_images. В ответах не возвращается.",
    )

    class Meta:
        model = Order
        fields = (
            "id", "name", "description", "type", "clients",
            "broadcast_interval", "broadcast_type", "placement", "playback_policy",
            "nomenclature", "playlist", "starts_at", "ends_at", "is_permanent",
            "suppress_background_audio", "suppress_background_visual", "parameters",
            "audio_images", "slides",
            "status", "owner", "created",
        )
        read_only_fields = ("id", "owner", "created", "status")
        extra_kwargs = {
            "parameters": {
                "help_text": "Параметры расписания. Для рекламы, кроме broadcast_type=7, требуется times_in_hour от 1 до 60.",
            },
            "status": {
                "help_text": "0 — ожидает эфира, 1 — в эфире, 2 — завершён, 3 — отменён, 4 — ошибка.",
            },
        }

    def to_internal_value(self, data):
        normalized = normalize_public_order_input(
            data,
            creating=self.instance is None,
            current_placement=getattr(self.instance, "placement", None),
        )
        return super().to_internal_value(normalized)

    def run_validation(self, data=serializers.empty):
        try:
            return super().run_validation(data)
        except serializers.ValidationError as exc:
            raise serializers.ValidationError(public_order_errors(exc.detail)) from exc

    def validate_clients(self, clients):
        if len(set(clients)) != len(clients):
            raise serializers.ValidationError("Одна и та же точка указана несколько раз.")
        active = Nomenclature.active.in_bulk(clients)
        missing = [str(identifier) for identifier in clients if identifier not in active]
        if missing:
            raise serializers.ValidationError(
                f"Не найдены активные точки: {', '.join(missing)}."
            )
        return [active[identifier] for identifier in clients]

    def validate(self, attrs):
        if self.instance is not None and "clients" in attrs:
            raise serializers.ValidationError({
                "clients": "Точки существующего заказа нельзя менять; создайте новый заказ."
            })
        has_audio_images = "audio_images" in attrs
        has_slides = "slides" in attrs
        if has_audio_images and has_slides:
            raise serializers.ValidationError({
                "audio_images": "Передайте audio_images или совместимое поле slides, но не оба сразу."
            })
        raw_parameters = None
        initial_data = getattr(self, "initial_data", None)
        if isinstance(initial_data, Mapping):
            raw_parameters = initial_data.get("parameters")
        if isinstance(raw_parameters, Mapping) and AUDIO_IMAGES_PARAMETER in raw_parameters:
            raise serializers.ValidationError({
                "parameters": "audio_images передаётся отдельным полем верхнего уровня."
            })

        supplied_mapping = attrs.pop("audio_images", attrs.pop("slides", None))
        attrs = validate_unified_order_attributes(attrs, instance=self.instance)
        playlist = attrs.get("playlist", getattr(self.instance, "playlist", None))
        placement = attrs.get("placement", getattr(self.instance, "placement", None))

        if has_audio_images or has_slides:
            try:
                mapping = validate_order_audio_images(
                    supplied_mapping,
                    playlist=playlist,
                    placement=placement,
                )
            except DjangoValidationError as exc:
                detail = exc.message_dict if hasattr(exc, "message_dict") else {"audio_images": exc.messages}
                raise serializers.ValidationError(detail) from exc
        elif self.instance is None:
            mapping = {}
        else:
            mapping = get_order_audio_images(self.instance)
            if "playlist" in attrs and mapping:
                try:
                    mapping = validate_order_audio_images(
                        mapping,
                        playlist=playlist,
                        placement=placement,
                        allow_inactive_images=True,
                    )
                except DjangoValidationError as exc:
                    detail = exc.message_dict if hasattr(exc, "message_dict") else {"audio_images": exc.messages}
                    raise serializers.ValidationError(detail) from exc

        parameters = attrs.get(
            "parameters",
            getattr(self.instance, "parameters", {}) or {},
        )
        attrs["parameters"] = with_order_audio_images(parameters, mapping)
        return attrs

    def to_representation(self, instance):
        return UnifiedOrderResponseSerializer(instance, context=self.context).data


class UnifiedOrderResponseSerializer(serializers.ModelSerializer):
    """Ответ с привычными именами полей и UUID плейлиста."""

    type = serializers.SerializerMethodField()
    clients = serializers.SerializerMethodField()
    owner = serializers.SerializerMethodField()
    broadcast_interval = serializers.SerializerMethodField()
    broadcast_type = serializers.SerializerMethodField()
    order_type = serializers.SerializerMethodField()
    parameters = serializers.SerializerMethodField()
    audio_images = serializers.SerializerMethodField()
    created = LocalOrderDateTimeField(read_only=True)

    class Meta:
        model = Order
        fields = (
            "id", "name", "description", "type", "clients", "playlist",
            "broadcast_interval", "broadcast_type", "order_type", "is_permanent",
            "suppress_background_audio", "suppress_background_visual", "parameters",
            "audio_images",
            "status", "owner", "created",
        )
        read_only_fields = fields

    @extend_schema_field({"type": "string", "enum": ["ad", "bg"]})
    def get_type(self, obj):
        return {"advertising": "ad", "background": "bg"}[obj.placement]

    @extend_schema_field({"type": "array", "items": {
        "type": "object",
        "properties": {"id": {"type": "string", "format": "uuid"}, "name": {"type": "string"}},
    }})
    def get_clients(self, obj):
        return [{"id": obj.nomenclature.id, "name": obj.nomenclature.name}]

    @extend_schema_field({"type": "object", "nullable": True, "properties": {
        "id": {"type": "string", "format": "uuid"}, "full_name": {"type": "string"},
    }})
    def get_owner(self, obj):
        if obj.owner is None:
            return None
        return {"id": obj.owner.id, "full_name": obj.owner.full_name}

    @extend_schema_field({
        "type": "object",
        "properties": {
            "lower": {"type": "string", "nullable": True, "pattern": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", "example": "2026-09-30 13:04:00"},
            "upper": {"type": "string", "nullable": True, "pattern": r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", "example": "2026-10-09 13:04:00"},
        },
    })
    def get_broadcast_interval(self, obj):
        field = LocalOrderDateTimeField()
        return {
            "lower": field.to_representation(obj.starts_at) if obj.starts_at else None,
            "upper": field.to_representation(obj.ends_at) if obj.ends_at else None,
        }

    @extend_schema_field({"type": "integer", "nullable": True, "minimum": 0, "maximum": 7})
    def get_broadcast_type(self, obj):
        if obj.placement != "advertising":
            return None
        return {
            "workday": 0,
            "hourly_slots": 0,
            "open_offset": 1,
            "close_offset": 2,
            "fixed_time": 3,
            "open_to_fixed": 4,
            "fixed_to_close": 5,
            "start_to_close": 5,
            "event": 6,
            "continuous": 7,
        }[obj.playback_policy]

    @extend_schema_field({"type": "integer", "nullable": True, "minimum": 0, "maximum": 3})
    def get_order_type(self, obj):
        if obj.placement != "background":
            return None
        items = list(obj.playlist.items.all())
        media_types = {item.file.type for item in items}
        if not media_types:
            media_types = {file.type for file in obj.playlist.files.all()}
        if media_types == {1, 2}:
            return 1
        if len(media_types) == 1:
            media_type = next(iter(media_types))
            return media_type if media_type in {0, 1, 2, 3} else None
        return None

    @extend_schema_field({"type": "object"})
    def get_parameters(self, obj):
        parameters = public_order_parameters(obj.parameters)
        parameters.pop("schedule_mode", None)
        return parameters

    @extend_schema_field(AUDIO_IMAGES_SCHEMA)
    def get_audio_images(self, obj):
        return get_order_audio_images(obj)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.placement == "background":
            representation.pop("broadcast_type", None)
        else:
            representation.pop("order_type", None)
        return representation


class UnifiedOrderResendSerializer(serializers.Serializer):
    """Список существующих заказов для повторной отправки Player."""

    order_ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100,
        help_text="От одного до 100 UUID заказов со статусом «ожидает» или «в эфире».",
    )

    def validate_order_ids(self, order_ids):
        if len(set(order_ids)) != len(order_ids):
            raise serializers.ValidationError("Один и тот же заказ указан несколько раз.")
        return order_ids
