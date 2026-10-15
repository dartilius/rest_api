"""Typed Django-admin form for unified Player orders.

The transport keeps ``Order.parameters`` as JSON for the API and Player, but
managers configure its supported values through ordinary form controls.
"""

from __future__ import annotations

from datetime import time, timedelta
import logging
from uuid import UUID

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework.exceptions import ValidationError as RestValidationError

from files.models import File, Playlist
from files.playlist_content import is_audio_file
from nomenclatures.models import Nomenclature
from orders.models import Order
from orders.services.order_audio_images import (
    get_order_audio_images,
    validate_order_audio_images,
    with_order_audio_images,
)
from orders.services.unified_order_input import validate_unified_order_attributes
from orders.services.unified_order_delivery import validate_order_delivery


logger = logging.getLogger(__name__)


class ClockInput(forms.TimeInput):
    input_type = "time"

_SCHEDULE_KEYS = {
    "times_in_hour", "timedelta", "start_time", "end_time", "schedule_mode",
}
_POLICY_FIELDS = {
    "open_offset": ("timedelta",),
    "close_offset": ("timedelta",),
    "fixed_time": ("start_time", "end_time"),
    "open_to_fixed": ("end_time",),
    "fixed_to_close": ("start_time",),
    "start_to_close": ("start_time",),
}
_WEEKDAY_CHOICES = (
    ("0", "Понедельник"),
    ("1", "Вторник"),
    ("2", "Среда"),
    ("3", "Четверг"),
    ("4", "Пятница"),
    ("5", "Суббота"),
    ("6", "Воскресенье"),
)
_ALL_WEEKDAYS = tuple(value for value, _label in _WEEKDAY_CHOICES)


def _playlist_primary_files(playlist: Playlist) -> list[File]:
    items = list(
        playlist.items.select_related("file").order_by("position", "pk")
    )
    if items:
        return [item.file for item in items]
    return list(playlist.files.all().order_by("name", "pk"))


def order_audio_image_options(
    playlist: Playlist, *, selected_image_ids=()
) -> dict[str, list[dict[str, str]]]:
    """Передаём названия в форму; проверку привязок выполняет сервис."""

    valid_selected_ids = []
    for value in selected_image_ids:
        try:
            valid_selected_ids.append(UUID(str(value)))
        except (AttributeError, TypeError, ValueError):
            continue

    audios = [
        {"id": str(file.pk), "name": file.name}
        for file in _playlist_primary_files(playlist)
        if is_audio_file(file)
    ]
    images = []
    if audios:
        images = [
            {"id": str(file.pk), "name": file.name}
            for file in (
                File.objects.filter(type=2)
                .filter(Q(is_active=True) | Q(pk__in=valid_selected_ids))
                .order_by("name", "pk")
            )
        ]
    return {"audios": audios, "images": images}


class OrderAudioImagesWidget(forms.Widget):
    """Выбор картинок по названиям аудиофайлов с сохранением порядка показа."""

    template_name = "admin/orders/widgets/audio_images.html"

    class Media:
        js = (
            "admin/js/core.js",
            "admin/js/SelectBox.js",
            "admin/js/SelectFilter2.js",
        )

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.audios: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []

    def configure(self, options):
        self.audios = options["audios"]
        self.images = options["images"]

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        mapping = value if isinstance(value, dict) else {}
        groups = []
        for audio in self.audios:
            selected_ids = list(mapping.get(audio["id"], ()))
            selected = set(selected_ids)
            images_by_id = {image["id"]: image for image in self.images}
            groups.append(
                {
                    **audio,
                    "choices": [
                        image
                        for image in self.images
                        if image["id"] not in selected
                    ],
                    "selected_images": [
                        images_by_id[image_id]
                        for image_id in selected_ids
                        if image_id in images_by_id
                    ],
                }
            )
        context["widget"]["groups"] = groups
        return context

    def value_from_datadict(self, data, files, name):
        marker = f"{name}__present"
        if marker not in data:
            return None
        prefix = f"{name}__"
        mapping = {}
        for key in data:
            if not key.startswith(prefix) or key == marker:
                continue
            parent_id = key.removeprefix(prefix)
            values = (
                data.getlist(key)
                if hasattr(data, "getlist")
                else data.get(key, ())
            )
            if isinstance(values, str):
                values = [values]
            mapping[parent_id] = [str(value) for value in values if value]
        return mapping

    def value_omitted_from_data(self, data, files, name):
        return f"{name}__present" not in data


class UnifiedOrderAdminForm(forms.ModelForm):
    """Показываем параметры заказа обычными полями, без ручного JSON."""

    target_nomenclatures = forms.ModelMultipleChoiceField(
        queryset=Nomenclature.objects.none(),
        required=False,
        label="Точки вещания",
        help_text="Для каждой выбранной точки будет создан отдельный заказ и команда Player.",
        widget=FilteredSelectMultiple("Точки вещания", is_stacked=False),
    )
    audio_images = forms.Field(
        required=False,
        label="Картинки для рекламного аудио",
        help_text=(
            "Для каждого аудиоролика можно выбрать одну или несколько картинок. "
            "Одна картинка показывается всё время ролика; несколько делят его "
            "длительность поровну. Настройка относится только к этому заказу."
        ),
        widget=OrderAudioImagesWidget(),
    )
    times_in_hour = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=60,
        initial=1,
        label="Выходов в час",
        help_text="От 1 до 60 выходов заказа за час. Например, 4 — один выход примерно каждые 15 минут. Ролики выбираются по очереди.",
        widget=forms.NumberInput(attrs={"class": "js-ad-schedule"}),
    )
    start_time = forms.TimeField(
        required=False,
        input_formats=("%H:%M:%S", "%H:%M"),
        label="Начинать показы с",
        help_text="Для фиксированного времени, «с указанного времени до закрытия» и других режимов, где нужно начало.",
        widget=ClockInput(format="%H:%M:%S", attrs={"step": "1", "class": "js-ad-schedule"}),
    )
    end_time = forms.TimeField(
        required=False,
        input_formats=("%H:%M:%S", "%H:%M"),
        label="Заканчивать показы в",
        help_text="Для фиксированного времени и режима «от открытия до указанного времени».",
        widget=ClockInput(format="%H:%M:%S", attrs={"step": "1", "class": "js-ad-schedule"}),
    )
    offset_minutes = forms.IntegerField(required=False, min_value=0, max_value=5999, initial=0,
        label="Отступ, минут", help_text="Например, 30 — начать через полчаса после открытия или закончить за полчаса до закрытия.")
    offset_seconds = forms.IntegerField(required=False, min_value=0, max_value=59, initial=0,
        label="Дополнительно секунд", help_text="Обычно 0. Например, 5 минут и 30 секунд задаются двумя числами: 5 и 30.")
    order_weight = forms.IntegerField(
        required=False,
        min_value=0,
        max_value=100,
        initial=50,
        label="Приоритет заказа",
        help_text="Для рекламы, фоновых видео и картинок: большее число ставит заказ раньше в очереди, а не чаще. Обычно оставляют 50.",
        widget=forms.NumberInput(attrs={"class": "js-order-priority"}),
    )
    image_duration_seconds = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=86400,
        label="Показ картинки, секунд",
        help_text="Если в плейлисте есть картинки, задайте время их показа. Пусто — используется настройка плеера. Видео всегда играется полностью.",
        widget=forms.NumberInput(attrs={"class": "js-order-image-duration"}),
    )
    advertising_audio = forms.ChoiceField(
        choices=(("sound", "Со звуком"), ("muted", "Без звука")),
        initial="sound",
        required=False,
        label="Звук рекламы",
        help_text="У непрерывной рекламы без звука фоновая музыка продолжает играть.",
        widget=forms.Select(attrs={"class": "js-ad-option"}),
    )
    weekdays = forms.MultipleChoiceField(
        choices=_WEEKDAY_CHOICES,
        initial=_ALL_WEEKDAYS,
        required=False,
        label="Дни недели",
        help_text=(
            "По умолчанию выбраны все дни — заказ работает каждый день в пределах периода. "
            "Если снять дни, в эти даты срочный заказ не выходит, а фоновый резерв остаётся доступен."
        ),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "js-order-weekdays"}),
    )
    all_days = forms.BooleanField(
        initial=True,
        required=False,
        label="Каждый день",
        help_text="Оставьте включённым для вещания во все дни недели.",
        widget=forms.CheckboxInput(attrs={"class": "js-order-all-days"}),
    )
    weekdays_control_present = forms.CharField(
        initial="1",
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Order
        exclude = ("parameters",)
        labels = {
            "placement": "Что отправляем", "playback_policy": "Как показывать рекламу",
            "playlist": "Плейлист с контентом", "starts_at": "Начало периода", "ends_at": "Конец периода",
            "is_permanent": "Фон без даты окончания",
            "suppress_background_audio": "Останавливать фоновую музыку на время рекламы",
            "suppress_background_visual": "Приостанавливать фоновые видео и картинки на время рекламы",
        }
        help_texts = {
            "name": "Понятное название, чтобы потом найти заказ. Например: «Осенняя акция».",
            "playlist": "Начните вводить название и выберите плейлист из списка. Его ролики будут воспроизводиться по очереди.",
            "starts_at": "Дата начала действия заказа. Для рекламы также нужно время; для фона пустое поле означает запуск после загрузки.",
            "ends_at": "После этого времени заказ больше не воспроизводится.",
            "is_permanent": "Только для фона. Он не заканчивается по дате и используется, когда нет активного срочного фона этого типа.",
            "suppress_background_audio": "Снимите галочку, если музыка должна продолжать играть под рекламой без звука.",
            "suppress_background_visual": "Обычно эту галочку оставляют: на экране будет реклама вместо фонового видео или картинки.",
        }
        widgets = {
            "placement": forms.Select(attrs={"class": "js-order-placement"}),
            "playback_policy": forms.Select(attrs={"class": "js-order-policy"}),
            "suppress_background_audio": forms.CheckboxInput(attrs={"class": "js-ad-option"}),
            "suppress_background_visual": forms.CheckboxInput(attrs={"class": "js-ad-option"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "playback_policy" not in self.fields:
            return  # В режиме просмотра форма может не содержать полей ввода.
        parameters = self.instance.parameters if isinstance(self.instance.parameters, dict) else {}
        adding = self.instance._state.adding

        initial_audio_images = {} if adding else get_order_audio_images(self.instance)
        selected_playlist = self._selected_playlist()
        options = (
            order_audio_image_options(
                selected_playlist,
                selected_image_ids={
                    image_id
                    for images in initial_audio_images.values()
                    for image_id in images
                },
            )
            if selected_playlist is not None
            else {"audios": [], "images": []}
        )
        self.fields["audio_images"].widget.configure(options)
        self.fields["audio_images"].initial = initial_audio_images
        self.initial["audio_images"] = initial_audio_images

        if adding:
            if "nomenclature" in self.fields:
                self.fields["nomenclature"].required = False
                self.fields["nomenclature"].widget = forms.HiddenInput()
            self.fields["target_nomenclatures"].queryset = Nomenclature.active.order_by("name")
            self.fields["suppress_background_audio"].initial = True
            self.fields["suppress_background_visual"].initial = True
            self.initial["suppress_background_audio"] = True
            self.initial["suppress_background_visual"] = True
            self.initial["placement"] = self.initial.get("placement") or "advertising"
        else:
            self.fields["target_nomenclatures"].widget = forms.HiddenInput()
            self.fields["target_nomenclatures"].disabled = True

        self.fields["times_in_hour"].initial = parameters.get("times_in_hour", 1)
        self.fields["order_weight"].initial = parameters.get("weight", 50)
        self.fields["image_duration_seconds"].initial = parameters.get("image_duration_seconds")
        self.fields["advertising_audio"].initial = "muted" if parameters.get("audio_muted") else "sound"
        stored_weekdays = parameters.get("weekdays")
        if (
            isinstance(stored_weekdays, list)
            and stored_weekdays
            and all(type(day) is int and 0 <= day <= 6 for day in stored_weekdays)
            and len(set(stored_weekdays)) == len(stored_weekdays)
        ):
            self.fields["weekdays"].initial = [str(day) for day in stored_weekdays]
            self.fields["all_days"].initial = set(stored_weekdays) == set(range(7))
        else:
            self.fields["weekdays"].initial = _ALL_WEEKDAYS
            self.fields["all_days"].initial = True
        offset = _parse_offset(parameters.get("timedelta"))
        seconds = int(offset.total_seconds()) if offset is not None else 0
        self.fields["offset_minutes"].initial, self.fields["offset_seconds"].initial = divmod(seconds, 60)
        for field in ("start_time", "end_time"):
            raw_value = parameters.get(field)
            if raw_value:
                try:
                    self.fields[field].initial = time.fromisoformat(raw_value)
                except (TypeError, ValueError):
                    logger.warning("Order %s has invalid %s: %r", self.instance.pk, field, raw_value)

        choices = list(self.fields["playback_policy"].choices)
        self.fields["playback_policy"].required = False
        if adding or self.instance.playback_policy != "event":
            choices = [choice for choice in choices if choice[0] != "event"]
        if adding or self.instance.playback_policy != "hourly_slots":
            choices = [choice for choice in choices if choice[0] != "hourly_slots"]
        if not adding and self.instance.playback_policy == "event":
            self.fields["playback_policy"].disabled = True
            self.fields["playback_policy"].help_text = (
                "Реклама по событию пока не настраивается в админке. Существующие параметры сохранены без изменений."
            )
            self.fields["playback_policy"].widget.attrs["class"] += " js-unsupported-event"
        self.fields["playback_policy"].choices = choices
        selected_placement = self.data.get(self.add_prefix("placement"), self.instance.placement)
        permanent = self.fields["is_permanent"].widget.value_from_datadict(self.data, self.files, self.add_prefix("is_permanent"))
        if self.is_bound and selected_placement == "background" and permanent:
            self.fields["ends_at"].disabled = True
            self.initial["ends_at"] = None

    def clean(self):
        cleaned_data = super().clean()
        placement = cleaned_data.get("placement", self.instance.placement)
        policy = cleaned_data.get("playback_policy") or self.instance.playback_policy
        cleaned_data["placement"] = placement
        cleaned_data["playback_policy"] = policy
        stored = self.instance.parameters or {}
        if not isinstance(stored, dict):
            self.instance.parameters = {}
            self.add_error(None, "Сохранённые настройки заказа повреждены. Обратитесь к администратору.")
            return cleaned_data
        parameters = dict(stored)
        targets = list(cleaned_data.get("target_nomenclatures") or ())
        playlist = cleaned_data.get("playlist")

        if self.instance._state.adding:
            if not targets:
                self.add_error("target_nomenclatures", "Выберите хотя бы одну точку вещания.")
            else:
                cleaned_data["nomenclature"] = targets[0]
                self.instance.nomenclature = targets[0]

        if placement == "background":
            cleaned_data["playback_policy"] = "workday"
            policy = "workday"
            cleaned_data["ends_at"] = None if cleaned_data.get("is_permanent") else cleaned_data.get("ends_at")
            if not cleaned_data.get("is_permanent") and cleaned_data.get("ends_at") is None:
                self.add_error("ends_at", "Укажите конец периода или включите «Фон без даты окончания».")
            parameters.pop("audio_muted", None)
            parameters.pop("event", None)
            parameters.pop("active_ad", None)
            for key in _SCHEDULE_KEYS:
                parameters.pop(key, None)
            self._collect_weekdays(
                cleaned_data,
                parameters,
                enabled=not cleaned_data.get("is_permanent"),
            )
            parameters = with_order_audio_images(parameters, {})
        elif placement == "advertising" and policy != "event":
            for key in _SCHEDULE_KEYS:
                parameters.pop(key, None)
            self._collect_weekdays(
                cleaned_data,
                parameters,
                enabled=True,
            )
            self._collect_advertising_parameters(cleaned_data, parameters, policy, targets)
            parameters = self._collect_audio_images(
                cleaned_data,
                parameters,
                playlist=playlist,
                placement=placement,
            )
        elif placement == "advertising" and policy == "event":
            cleaned_data["suppress_background_audio"] = self.instance.suppress_background_audio
            cleaned_data["suppress_background_visual"] = self.instance.suppress_background_visual
            parameters = self._collect_audio_images(
                cleaned_data,
                parameters,
                playlist=playlist,
                placement=placement,
            )

        self._collect_visual_parameters(cleaned_data, parameters)
        cleaned_data["parameters"] = parameters
        self.instance.parameters = parameters
        return cleaned_data

    def _selected_playlist(self):
        raw_id = self.data.get(self.add_prefix("playlist")) if self.is_bound else None
        if raw_id:
            try:
                return Playlist.objects.get(pk=raw_id)
            except (Playlist.DoesNotExist, ValidationError, ValueError):
                return None
        if self.instance.playlist_id:
            return self.instance.playlist
        return None

    def _collect_audio_images(self, cleaned_data, parameters, *, playlist, placement):
        if playlist is None:
            return with_order_audio_images(parameters, {})
        mapping = cleaned_data.get("audio_images")
        if mapping is None:
            mapping = {} if self.instance._state.adding else get_order_audio_images(self.instance)
        existing = {} if self.instance._state.adding else get_order_audio_images(self.instance)
        mapping = {
            str(parent): list(images)
            for parent, images in mapping.items()
            if images or str(parent) in existing
        }
        if mapping == existing:
            return with_order_audio_images(parameters, existing)

        retained_historic = {
            parent: list(images)
            for parent, images in mapping.items()
            if existing.get(parent) == images
        }
        changed = {
            parent: images
            for parent, images in mapping.items()
            if retained_historic.get(parent) != images
        }
        try:
            validated = validate_order_audio_images(
                changed,
                playlist=playlist,
                placement=placement,
            )
        except ValidationError as exc:
            messages = getattr(exc, "message_dict", {}).get(
                "audio_images", exc.messages
            )
            self.add_error("audio_images", messages)
            return parameters
        return with_order_audio_images(parameters, {**retained_historic, **validated})

    def _collect_weekdays(self, cleaned_data, parameters, *, enabled):
        if not enabled:
            parameters.pop("weekdays", None)
            return
        raw_weekdays = cleaned_data.get("weekdays") or []
        if cleaned_data.get("all_days"):
            parameters.pop("weekdays", None)
            return
        if not cleaned_data.get("weekdays_control_present") and not raw_weekdays:
            # Совместимость с формами, созданными до выбора дней недели.
            parameters.pop("weekdays", None)
            return
        weekdays = [int(day) for day in raw_weekdays]
        if not weekdays:
            self.add_error("weekdays", "Выберите хотя бы один день недели.")
            parameters.pop("weekdays", None)
        elif len(set(weekdays)) != len(weekdays):
            self.add_error("weekdays", "Один и тот же день недели выбран несколько раз.")
            parameters.pop("weekdays", None)
        elif set(weekdays) == set(range(7)):
            parameters.pop("weekdays", None)
        else:
            parameters["weekdays"] = weekdays

    def _collect_advertising_parameters(self, cleaned_data, parameters, policy, targets):
        if policy == "continuous":
            cleaned_data["suppress_background_audio"] = cleaned_data.get("advertising_audio") != "muted"
            cleaned_data["suppress_background_visual"] = True
            return

        times = cleaned_data.get("times_in_hour")
        if times is None:
            self.add_error("times_in_hour", "Укажите количество выходов в час.")
        else:
            parameters["times_in_hour"] = times

        required = _POLICY_FIELDS.get(policy, ())
        if "timedelta" in required:
            minutes = cleaned_data.get("offset_minutes")
            if minutes is None:
                self.add_error("offset_minutes", "Укажите отступ в минутах; 0 означает без отступа.")
            else:
                parameters["timedelta"] = _format_offset(timedelta(minutes=minutes, seconds=cleaned_data.get("offset_seconds") or 0))

        for field in ("start_time", "end_time"):
            value = cleaned_data.get(field)
            if field in required and value is None:
                self.add_error(field, "Укажите время.")
            elif field in required:
                parameters[field] = value.strftime("%H:%M:%S")

        if policy == "fixed_time":
            start, end = cleaned_data.get("start_time"), cleaned_data.get("end_time")
            if start is not None and end is not None and start >= end:
                self.add_error("end_time", "Время окончания должно быть позже времени начала.")
        if policy == "start_to_close" and cleaned_data.get("start_time") is not None:
            for nomenclature in targets or [cleaned_data.get("nomenclature") or self.instance.nomenclature]:
                if nomenclature is not None:
                    self._validate_start_time_in_workday(cleaned_data["start_time"], nomenclature)

    def _collect_visual_parameters(self, cleaned_data, parameters):
        weight = cleaned_data.get("order_weight")
        if weight is not None:
            parameters["weight"] = weight
        else:
            parameters.pop("weight", None)
        duration = cleaned_data.get("image_duration_seconds")
        if duration is None:
            parameters.pop("image_duration_seconds", None)
        else:
            parameters["image_duration_seconds"] = duration
        if cleaned_data.get("placement") == "advertising" and cleaned_data.get("playback_policy") != "event":
            parameters["audio_muted"] = cleaned_data.get("advertising_audio") == "muted"

    def _post_clean(self):
        super()._post_clean()
        if self.errors:
            return
        try:
            # Привязки уже проверены полями формы. Общие правила заказа
            # проверяем отдельно, без повторного разбора карты картинок.
            validated = validate_unified_order_attributes(
                dict(self.cleaned_data),
                instance=None if self.instance._state.adding else self.instance,
            )
        except RestValidationError as exc:
            self._add_serializer_errors(exc.detail)
            return

        self.instance.parameters = validated.get("parameters", self.instance.parameters)
        for field in ("suppress_background_audio", "suppress_background_visual"):
            if field in validated:
                self.cleaned_data[field] = validated[field]
                setattr(self.instance, field, validated[field])
        targets = (
            self.cleaned_data.get("target_nomenclatures")
            if self.instance._state.adding
            else [self.instance.nomenclature]
        )
        original = self.instance.nomenclature
        try:
            for target in targets:
                self.instance.nomenclature = target
                validate_order_delivery(self.instance)
        except ValidationError as exc:
            self.add_error(None, exc)
        finally:
            self.instance.nomenclature = original

    def _add_serializer_errors(self, details):
        for field, messages in details.items():
            target = field
            if field == "parameters":
                policy = self.cleaned_data.get("playback_policy")
                target = {
                    "open_offset": "offset_minutes",
                    "close_offset": "offset_minutes",
                    "fixed_time": "start_time",
                    "open_to_fixed": "end_time",
                    "fixed_to_close": "start_time",
                    "start_to_close": "start_time",
                }.get(policy, "times_in_hour")
            self.add_error(target if target in self.fields else None, messages)

    def _validate_start_time_in_workday(self, start_time, nomenclature) -> None:
        worktime_start = getattr(nomenclature, "worktime_start", None)
        worktime_end = getattr(nomenclature, "worktime_end", None)
        if worktime_start is None or worktime_end is None:
            return
        in_workday = (
            worktime_start <= start_time < worktime_end
            if worktime_start < worktime_end
            else start_time >= worktime_start or start_time < worktime_end
        )
        if not in_workday:
            self.add_error("start_time", "Первый выход должен быть в рабочее время точки.")


def _parse_offset(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return timedelta(minutes=value)
    if isinstance(value, str):
        try:
            hours, minutes, seconds = (int(part) for part in value.split(":"))
        except (TypeError, ValueError):
            return None
        if hours >= 0 and 0 <= minutes < 60 and 0 <= seconds < 60:
            return timedelta(hours=hours, minutes=minutes, seconds=seconds)
    return None


def _format_offset(value: timedelta) -> str:
    seconds = int(value.total_seconds())
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
