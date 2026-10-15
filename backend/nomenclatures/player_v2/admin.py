"""Регистрация ключей и команд Player v2 в Django admin."""

from copy import deepcopy
from datetime import time
import re

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponseRedirect
from django.urls import path, reverse

from nomenclatures.models import (
    Nomenclature,
    StationCommandV2,
    StationCredential,
    StationInstallation,
)
from nomenclatures.player_v2.credentials import (
    generate_station_token,
    hash_station_token,
    issue_station_token,
)
from nomenclatures.player_v2.settings import SettingsPatchError, apply_settings_operations, validate_settings_document


DAY_CHOICES = (
    ("mon", "Понедельник"),
    ("tue", "Вторник"),
    ("wed", "Среда"),
    ("thu", "Четверг"),
    ("fri", "Пятница"),
    ("sat", "Суббота"),
    ("sun", "Воскресенье"),
)
SETTING_GROUP_CHOICES = (
    ("volume", "Громкость канала"),
    ("interval_volume", "Громкость по времени"),
    ("background", "Параметр фона"),
    ("worktime", "Рабочее время"),
    ("audio_device", "Аудиовыход Player"),
    ("display", "Экран вывода Player"),
    ("visual_output", "Поворот визуального вывода"),
)
SETTINGS_PATCH_GROUPS = frozenset({"volume", "interval_volume", "background", "worktime"})
DAY_KEYS = frozenset(day for day, _ in DAY_CHOICES)
TIME_VALUE_PATTERN = re.compile(r"^\d{2}:\d{2}(?::\d{2})?$")
BACKGROUND_SETTING_CHOICES = (
    ("video_enabled", "Показывать фоновое видео"),
    ("video_muted", "Выключить звук фонового видео"),
    ("img_enabled", "Показывать фоновые картинки"),
    ("img_duration", "Время показа картинки"),
    ("music_random", "Случайный порядок фоновой музыки"),
    ("video_random", "Случайный порядок фонового видео"),
    ("img_random", "Случайный порядок фоновых картинок"),
)
BACKGROUND_BOOLEAN_VALUES = (("true", "Включено"), ("false", "Выключено"))
BACKGROUND_SWITCHES = tuple((key, label) for key, label in BACKGROUND_SETTING_CHOICES if key != "img_duration")


def _background_switch(label):
    return forms.ChoiceField(label=label, required=False, choices=(("", "Не изменять"),) + BACKGROUND_BOOLEAN_VALUES)


def _latest_saved_revision(nomenclature) -> int:
    """Возвращает последнюю revision, подтверждённую Player, а не admin-формой."""
    if nomenclature.applied_settings_revision is not None:
        return nomenclature.applied_settings_revision

    commands = StationCommandV2.objects.filter(
        nomenclature=nomenclature,
        status=StationCommandV2.Status.APPLIED,
    ).order_by("-updated_at")
    for result in commands.values_list("result", flat=True).iterator(chunk_size=100):
        revision = (result or {}).get("saved_revision")
        if isinstance(revision, int) and not isinstance(revision, bool) and revision >= 0:
            return revision
    return 0


def _station_audio_devices(nomenclature):
    """Return only valid device records published by this Player."""
    capabilities = nomenclature.station_capabilities or {}
    audio = capabilities.get("audio") if isinstance(capabilities, dict) else None
    devices = audio.get("devices") if isinstance(audio, dict) else None
    if not isinstance(devices, list):
        return []
    return [
        device for device in devices
        if isinstance(device, dict) and isinstance(device.get("id"), str) and device["id"]
    ]


def _audio_device_choices(nomenclature=None):
    """Offer published choices; clean() still authorizes against selected station."""
    if nomenclature is None:
        return [("", "Сначала выберите точку вещания")]

    devices = _station_audio_devices(nomenclature)
    if devices:
        return [("", "Выберите аудиоустройство")] + [
            (device["id"], f"{device.get('name', device['id'])} — {nomenclature.name}")
            for device in devices
        ]

    capabilities = nomenclature.station_capabilities
    audio = capabilities.get("audio") if isinstance(capabilities, dict) else None
    if not isinstance(audio, dict) or "devices" not in audio:
        return [("", "Player ещё не передал список аудиоустройств")]
    return [("", "У этой точки нет доступных аудиоустройств")]


def _station_displays(nomenclature):
    capabilities = nomenclature.station_capabilities or {}
    displays = capabilities.get("displays") if isinstance(capabilities, dict) else None
    if not isinstance(displays, list):
        return []
    return [
        display for display in displays
        if isinstance(display, dict) and isinstance(display.get("id"), str) and display["id"]
    ]


def _display_choices(nomenclature=None):
    if nomenclature is None:
        return [("", "Сначала выберите точку вещания")]

    displays = _station_displays(nomenclature)
    if displays:
        return [("", "Выберите монитор")] + [
            (display["id"], f"{display.get('name', display['id'])} — {nomenclature.name}")
            for display in displays
        ]

    capabilities = nomenclature.station_capabilities
    if not isinstance(capabilities, dict) or "displays" not in capabilities:
        return [("", "Player ещё не передал список мониторов")]
    return [("", "У этой точки нет доступных мониторов")]


def _station_default_volumes(nomenclature):
    """Читаем подтверждённую громкость четырёх каналов для каждого дня."""

    settings = nomenclature.settings if isinstance(nomenclature.settings, dict) else {}
    result = {}
    for day, _ in DAY_CHOICES:
        day_settings = settings.get(day)
        values = day_settings.get("default_volume") if isinstance(day_settings, dict) else None
        if (
            not isinstance(values, list)
            or len(values) != 4
            or any(type(value) is not int or not 0 <= value <= 100 for value in values)
        ):
            continue
        result[day] = {
            "background_left": values[0],
            "advertisement_left": values[1],
            "background_right": values[2],
            "advertisement_right": values[3],
        }
    return result


def _station_custom_volumes(nomenclature):
    """Читаем подтверждённые интервальные профили в форме, удобной для admin."""

    settings = nomenclature.settings if isinstance(nomenclature.settings, dict) else {}
    result = {}
    for day, _ in DAY_CHOICES:
        day_settings = settings.get(day)
        custom_volume = day_settings.get("custom_volume") if isinstance(day_settings, dict) else None
        if not isinstance(custom_volume, dict):
            continue

        intervals = {}
        for interval, values in custom_volume.items():
            if (
                not isinstance(interval, str)
                or not isinstance(values, list)
                or len(values) != 4
                or any(type(value) is not int or not 0 <= value <= 100 for value in values)
            ):
                continue
            intervals[interval] = {
                "background_left": values[0],
                "advertisement_left": values[1],
                "background_right": values[2],
                "advertisement_right": values[3],
            }
        if intervals:
            result[day] = intervals
    return result


class StationIntervalScheduleWidget(forms.HiddenInput):
    """Скрыто передаёт JSON; оператор редактирует таблицу в отдельном виджете."""

    # Сам input скрыт шаблоном, но составной редактор видим. Иначе Django
    # admin добавляет всей строке класс hidden, скрывая также кнопку и поля.
    is_hidden = False
    template_name = "nomenclatures/widgets/station_intervals.html"


class StationVolumeCommandForm(forms.ModelForm):
    """Операторская форма, которая собирает независимые изменения в одну отправку."""

    setting_groups = forms.MultipleChoiceField(
        label="Что изменить",
        choices=SETTING_GROUP_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    # Старые POST из уже открытой admin-страницы остаются понятны форме, но в
    # новом интерфейсе эти два поля не выводятся.
    setting_group = forms.ChoiceField(choices=SETTING_GROUP_CHOICES, required=False, widget=forms.HiddenInput)
    day = forms.ChoiceField(choices=DAY_CHOICES, required=False, widget=forms.HiddenInput)
    settings_revision = forms.IntegerField(min_value=0, required=False, widget=forms.HiddenInput)

    volume_day = forms.ChoiceField(label="День", choices=DAY_CHOICES, required=False)
    background_left_volume = forms.IntegerField(
        label="Фон — левый канал, %", min_value=0, max_value=100, required=False
    )
    background_right_volume = forms.IntegerField(
        label="Фон — правый канал, %", min_value=0, max_value=100, required=False
    )
    advertisement_left_volume = forms.IntegerField(
        label="Реклама — левый канал, %", min_value=0, max_value=100, required=False
    )
    advertisement_right_volume = forms.IntegerField(
        label="Реклама — правый канал, %", min_value=0, max_value=100, required=False
    )
    volume_all_days = forms.BooleanField(label="Применить громкость ко всем дням", required=False)

    interval_volume_rows = forms.JSONField(
        label="Интервалы громкости",
        required=False,
        widget=StationIntervalScheduleWidget,
        help_text="В интервале эти значения имеют приоритет над обычной громкостью.",
    )

    background_day = forms.ChoiceField(label="День", choices=DAY_CHOICES, required=False)
    background_video_enabled = _background_switch("Показывать фоновое видео")
    background_video_muted = _background_switch("Выключить звук фонового видео")
    background_img_enabled = _background_switch("Показывать фоновые картинки")
    background_music_random = _background_switch("Случайный порядок фоновой музыки")
    background_video_random = _background_switch("Случайный порядок фонового видео")
    background_img_random = _background_switch("Случайный порядок фоновых картинок")
    background_setting = forms.ChoiceField(
        label="Параметр фона",
        choices=BACKGROUND_SETTING_CHOICES,
        required=False,
        widget=forms.HiddenInput,
        help_text="Для времени показа используйте поле ниже; для остальных — «Значение». ",
    )
    background_enabled = forms.ChoiceField(
        label="Значение",
        choices=BACKGROUND_BOOLEAN_VALUES,
        required=False,
        widget=forms.HiddenInput,
    )
    background_all_days = forms.BooleanField(label="Применить настройку фона ко всем дням", required=False)
    image_duration = forms.IntegerField(
        label="Время показа картинки, сек.",
        min_value=1,
        max_value=60,
        required=False,
    )

    worktime_day = forms.ChoiceField(label="День", choices=DAY_CHOICES, required=False)
    full_day = forms.BooleanField(label="Круглосуточно", required=False)
    worktime_start = forms.TimeField(
        label="Начало вещания",
        input_formats=("%H:%M", "%H:%M:%S"),
        required=False,
    )
    worktime_end = forms.TimeField(
        label="Конец вещания",
        input_formats=("%H:%M", "%H:%M:%S"),
        required=False,
    )
    worktime_all_days = forms.BooleanField(label="Применить рабочее время ко всем дням", required=False)

    audio_device_id = forms.ChoiceField(label="Аудиовыход", choices=(), required=False)
    display_id = forms.ChoiceField(label="Экран вывода", choices=(), required=False)
    visual_output_rotation = forms.ChoiceField(
        label="Поворот контента",
        choices=(("0", "Без поворота"), ("90", "90°"), ("180", "180°"), ("270", "270°")),
        required=False,
    )

    class Meta:
        model = StationCommandV2
        fields = ("nomenclature",)
        labels = {"nomenclature": "Точка вещания"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prepared_commands = []
        self.fields["interval_volume_rows"].widget.attrs["data-bound"] = "true" if self.is_bound else "false"
        station_id = (
            self.data.get(self.add_prefix("nomenclature"))
            if self.is_bound else self.initial.get("nomenclature")
        )
        station = None
        if station_id:
            try:
                station = Nomenclature.objects.only("name", "station_capabilities").filter(
                    pk=getattr(station_id, "pk", station_id)
                ).first()
            except (ValidationError, ValueError, TypeError):
                pass  # ModelChoiceField сообщит об ошибочном идентификаторе точки.
        self.fields["audio_device_id"].choices = _audio_device_choices(station)
        self.fields["display_id"].choices = _display_choices(station)

    class Media:
        # django.jQuery инициализируется этим файлом, а не самой библиотекой jQuery.
        css = {"all": ("nomenclatures/station_commands.css",)}
        js = (
            "admin/js/jquery.init.js",
            "nomenclatures/station_intervals.js",
            "nomenclatures/station_devices.js",
        )

    def clean(self):
        cleaned_data = super().clean()
        nomenclature = cleaned_data.get("nomenclature")
        groups = tuple(cleaned_data.get("setting_groups") or ())
        if not groups and cleaned_data.get("setting_group"):
            groups = (cleaned_data["setting_group"],)
        if not groups:
            self.add_error("setting_groups", "Выберите хотя бы один блок настроек.")
        cleaned_data["selected_setting_groups"] = groups
        if nomenclature is None or not groups:
            return cleaned_data
        revision = cleaned_data.get("settings_revision")
        if revision is not None and revision != _latest_saved_revision(nomenclature):
            raise forms.ValidationError("Настройки Player изменились. Обновите страницу точки перед отправкой.")

        self._validate_selected_groups(cleaned_data, groups, nomenclature)
        if self.errors:
            return cleaned_data

        operations = []
        if any(group in SETTINGS_PATCH_GROUPS for group in groups):
            try:
                validate_settings_document(nomenclature.settings)
            except SettingsPatchError as exc:
                raise forms.ValidationError(
                    "Невозможно подготовить изменение: сохранённые настройки точки некорректны."
                ) from exc
            try:
                operations = self._settings_operations(cleaned_data)
                if operations:
                    apply_settings_operations(nomenclature.settings, operations)
            except (SettingsPatchError, KeyError, TypeError) as exc:
                raise forms.ValidationError(
                    f"Не удалось подготовить настройки: {exc}"
                ) from exc

        prepared_commands = []
        if operations:
            prepared_commands.append({
                "kind": "apply_settings_patch",
                "body": {
                    "base_revision": _latest_saved_revision(nomenclature),
                    "operations": operations,
                },
            })
        if "audio_device" in groups:
            prepared_commands.append({
                "kind": "select_audio_device",
                "body": {"device_id": cleaned_data["audio_device_id"]},
            })
        if "display" in groups:
            prepared_commands.append({
                "kind": "select_display",
                "body": {"display_id": cleaned_data["display_id"]},
            })
        if "visual_output" in groups:
            prepared_commands.append({
                "kind": "set_visual_output",
                "body": {"rotation": int(cleaned_data["visual_output_rotation"])},
            })
        if not prepared_commands:
            raise forms.ValidationError(
                "Нет новых значений для отправки: выбранные настройки уже подтверждены Player. Команда не создана."
            )

        pending_kinds = {command["kind"] for command in prepared_commands}
        if StationCommandV2.objects.filter(
            nomenclature=nomenclature,
            status=StationCommandV2.Status.PENDING,
            kind__in=pending_kinds,
        ).exists():
            raise forms.ValidationError(
                "У этой точки уже есть ожидающее изменение одного из выбранных блоков. "
                "Дождитесь результата Player перед созданием следующего."
            )
        self._prepared_commands = prepared_commands
        return cleaned_data

    def _validate_selected_groups(self, data, groups, nomenclature):
        if "volume" in groups:
            volume_fields = (
                "background_left_volume",
                "background_right_volume",
                "advertisement_left_volume",
                "advertisement_right_volume",
            )
            if len(groups) == 1 and not any(data.get(field) is not None for field in volume_fields):
                self.add_error(None, "Укажите хотя бы один канал громкости для изменения.")
            self._require_target_day(data, "volume")
        if "interval_volume" in groups:
            self._validate_interval_rows(data)
        if "background" in groups:
            background_setting = data.get("background_setting")
            if not background_setting:
                if data.get("image_duration") is None and not any(data.get(f"background_{key}") for key, _ in BACKGROUND_SWITCHES):
                    self.add_error(None, "Измените хотя бы один параметр фонового контента.")
            elif background_setting == "img_duration":
                if data.get("image_duration") is None:
                    self.add_error("image_duration", "Укажите время показа картинки.")
            elif not data.get("background_enabled"):
                self.add_error("background_enabled", "Выберите, включить или выключить параметр.")
            self._require_target_day(data, "background")
        if "worktime" in groups:
            if not data.get("full_day"):
                start = data.get("worktime_start")
                end = data.get("worktime_end")
                if start is None:
                    self.add_error("worktime_start", "Укажите начало вещания.")
                if end is None:
                    self.add_error("worktime_end", "Укажите конец вещания.")
                if start is not None and end is not None and start >= end:
                    self.add_error("worktime_end", "Конец должен быть позже начала в пределах одного дня.")
            self._require_target_day(data, "worktime")
        if "audio_device" in groups:
            device_id = data.get("audio_device_id")
            available_ids = {device["id"] for device in _station_audio_devices(nomenclature)}
            if not device_id:
                self.add_error("audio_device_id", "Выберите аудиовыход Player.")
            elif device_id not in available_ids:
                self.add_error("audio_device_id", "Этот аудиовыход не принадлежит выбранной точке.")
        if "display" in groups:
            display_id = data.get("display_id")
            available_ids = {display["id"] for display in _station_displays(nomenclature)}
            if not display_id:
                self.add_error("display_id", "Выберите экран вывода Player.")
            elif display_id not in available_ids:
                self.add_error("display_id", "Этот экран не принадлежит выбранной точке.")
        if "visual_output" in groups and not data.get("visual_output_rotation"):
            self.add_error("visual_output_rotation", "Выберите поворот визуального контента.")

    def _require_target_day(self, data, group):
        if data.get(f"{group}_all_days"):
            return
        if data.get(f"{group}_day") or data.get("day"):
            return
        self.add_error(f"{group}_day", "Выберите день или отметьте применение ко всем дням.")

    def _validate_interval_rows(self, data):
        rows = data.get("interval_volume_rows")
        if not isinstance(rows, list):
            self.add_error("interval_volume_rows", "Добавьте хотя бы один интервал громкости.")
            return
        try:
            self._parsed_interval_rows(rows)
        except forms.ValidationError as exc:
            self.add_error("interval_volume_rows", exc)

    @staticmethod
    def _normalise_time(value, field_name):
        if not isinstance(value, str) or not TIME_VALUE_PATTERN.fullmatch(value):
            raise forms.ValidationError(f"{field_name}: используйте время в формате ЧЧ:ММ или ЧЧ:ММ:СС.")
        try:
            return time.fromisoformat(value).strftime("%H:%M:%S")
        except ValueError as exc:
            raise forms.ValidationError(f"{field_name}: указано недопустимое время.") from exc

    @classmethod
    def _normalise_interval(cls, start, end):
        start_value = cls._normalise_time(start, "Начало")
        end_value = cls._normalise_time(end, "Конец")
        if time.fromisoformat(start_value) >= time.fromisoformat(end_value):
            raise forms.ValidationError("Конец интервала должен быть позже начала в пределах одного дня.")
        return f"{start_value}-{end_value}"

    @classmethod
    def _parsed_interval_rows(cls, rows):
        if len(rows) > 128:
            raise forms.ValidationError("Можно редактировать не более 128 строк за одну отправку.")
        parsed_rows = []
        seen_origins = set()
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                raise forms.ValidationError(f"Строка {index}: ожидается объект интервала.")
            deleted = row.get("deleted", False)
            if type(deleted) is not bool:
                raise forms.ValidationError(f"Строка {index}: признак удаления некорректен.")
            original_day = row.get("original_day")
            original_interval = row.get("original_interval")
            has_original = original_day is not None or original_interval is not None
            if has_original:
                if not isinstance(original_day, str) or original_day not in DAY_KEYS or not isinstance(original_interval, str):
                    raise forms.ValidationError(f"Строка {index}: исходный интервал некорректен.")
                original_start, separator, original_end = original_interval.partition("-")
                if not separator:
                    raise forms.ValidationError(f"Строка {index}: исходный интервал некорректен.")
                original_interval = cls._normalise_interval(original_start, original_end)
                origin = (original_day, original_interval)
                if origin in seen_origins:
                    raise forms.ValidationError(f"Строка {index}: один интервал указан несколько раз.")
                seen_origins.add(origin)
            elif deleted:
                raise forms.ValidationError(f"Строка {index}: можно удалить только сохранённый интервал.")

            if deleted:
                parsed_rows.append({"deleted": True, "origin": (original_day, original_interval)})
                continue

            day = row.get("day")
            if not isinstance(day, str) or (day != "all" and day not in DAY_KEYS):
                raise forms.ValidationError(f"Строка {index}: выберите день или «Все дни».")
            interval = cls._normalise_interval(row.get("start"), row.get("end"))
            values = {}
            for key in (
                "background_left",
                "background_right",
                "advertisement_left",
                "advertisement_right",
            ):
                value = row.get(key)
                if type(value) is not int or not 0 <= value <= 100:
                    raise forms.ValidationError(f"Строка {index}: {key} должен быть целым числом от 0 до 100.")
                values[key] = value
            parsed_rows.append({
                "deleted": False,
                "origin": (original_day, original_interval) if has_original else None,
                "days": tuple(day_key for day_key, _ in DAY_CHOICES) if day == "all" else (day,),
                "interval": interval,
                "value": [
                    values["background_left"],
                    values["advertisement_left"],
                    values["background_right"],
                    values["advertisement_right"],
                ],
            })
        return parsed_rows

    @staticmethod
    def _target_days(data, group):
        all_days_field = {
            "volume": "volume_all_days",
            "background": "background_all_days",
            "worktime": "worktime_all_days",
        }[group]
        if data.get(all_days_field):
            return tuple(key for key, _ in DAY_CHOICES)
        return (data.get(f"{group}_day") or data.get("day"),)

    @classmethod
    def _interval_operations(cls, data):
        settings = data["nomenclature"].settings
        current_by_day = {
            day: deepcopy(settings[day].get("custom_volume", {}))
            for day, _ in DAY_CHOICES
        }
        desired_by_day = deepcopy(current_by_day)
        parsed_rows = cls._parsed_interval_rows(data.get("interval_volume_rows") or [])

        for row in parsed_rows:
            origin = row["origin"]
            if origin is None:
                continue
            origin_day, origin_interval = origin
            if origin_interval not in desired_by_day[origin_day]:
                raise SettingsPatchError("исходный интервал уже изменён Player; обновите страницу точки")
            del desired_by_day[origin_day][origin_interval]

        assigned = {}
        for row in parsed_rows:
            if row["deleted"]:
                continue
            for day in row["days"]:
                interval = row["interval"]
                key = (day, interval)
                if key in assigned and assigned[key] != row["value"]:
                    raise forms.ValidationError("В строках заданы разные уровни для одного дня и интервала.")
                assigned[key] = row["value"]
                desired_by_day[day][interval] = row["value"]

        for day, label in DAY_CHOICES:
            intervals = sorted(desired_by_day[day])
            for previous, following in zip(intervals, intervals[1:]):
                if previous.split("-")[1] > following.split("-")[0]:
                    raise forms.ValidationError(f"{label}: интервалы громкости пересекаются. Исправьте время.")

        operations = []
        for day, _ in DAY_CHOICES:
            current = current_by_day[day]
            desired = desired_by_day[day]
            for interval in current:
                if interval not in desired:
                    operations.append({"op": "remove", "path": f"/days/{day}/custom_volume/{interval}"})
            for interval, value in desired.items():
                if current.get(interval) != value:
                    operations.append({
                        "op": "set",
                        "path": f"/days/{day}/custom_volume/{interval}",
                        "value": {
                            "background": {"left": value[0], "right": value[2]},
                            "advertisement": {"left": value[1], "right": value[3]},
                        },
                    })
        return operations

    @classmethod
    def _settings_operations(cls, data):
        nomenclature = data["nomenclature"]
        groups = data["selected_setting_groups"]
        candidates = []
        if "volume" in groups:
            channels = (
                ("background", "left", data["background_left_volume"]),
                ("background", "right", data["background_right_volume"]),
                ("advertisement", "left", data["advertisement_left_volume"]),
                ("advertisement", "right", data["advertisement_right_volume"]),
            )
            for day in cls._target_days(data, "volume"):
                for source, channel, value in channels:
                    if value is None:
                        continue
                    operation = {
                        "op": "set",
                        "path": f"/days/{day}/default_volume/{source}/{channel}",
                        "value": value,
                    }
                    if apply_settings_operations(nomenclature.settings, [operation]) != nomenclature.settings:
                        candidates.append(operation)
        if "interval_volume" in groups:
            candidates.extend(cls._interval_operations(data))
        if "background" in groups:
            values = {
                key: data[f"background_{key}"] == "true"
                for key, _ in BACKGROUND_SWITCHES if data.get(f"background_{key}")
            }
            if data.get("image_duration") is not None:
                values["img_duration"] = data["image_duration"]
            if data.get("background_setting"):
                setting = data["background_setting"]
                values[setting] = data["image_duration"] if setting == "img_duration" else data["background_enabled"] == "true"
            for day in cls._target_days(data, "background"):
                for setting, value in values.items():
                    operation = {"op": "set", "path": f"/days/{day}/background/{setting}", "value": value}
                    if apply_settings_operations(nomenclature.settings, [operation]) != nomenclature.settings:
                        candidates.append(operation)
        if "worktime" in groups:
            value = "00:00:00-23:59:59" if data["full_day"] else (
                f"{data['worktime_start'].strftime('%H:%M:%S')}-"
                f"{data['worktime_end'].strftime('%H:%M:%S')}"
            )
            for day in cls._target_days(data, "worktime"):
                operation = {"op": "set", "path": f"/days/{day}/worktime", "value": value}
                if apply_settings_operations(nomenclature.settings, [operation]) != nomenclature.settings:
                    candidates.append(operation)
        return candidates

    def save(self, commit=True):
        command = super().save(commit=False)
        first = self._prepared_commands[0]
        command.kind = first["kind"]
        command.body = first["body"]
        if commit:
            self.save_commands(command)
        return command

    def save_commands(self, command):
        """Сохраняет весь пакет вместе и перепроверяет состояние под блокировкой."""
        with transaction.atomic():
            station = Nomenclature.objects.select_for_update().get(pk=command.nomenclature_id)
            kinds = [prepared["kind"] for prepared in self._prepared_commands]
            if StationCommandV2.objects.filter(
                nomenclature=station, status=StationCommandV2.Status.PENDING, kind__in=kinds,
            ).exists():
                raise ValidationError("У точки уже есть ожидающая команда. Обновите страницу.")
            for prepared in self._prepared_commands:
                if prepared["kind"] == "apply_settings_patch":
                    if prepared["body"]["base_revision"] != _latest_saved_revision(station):
                        raise ValidationError("Настройки Player изменились. Обновите страницу перед отправкой.")
                    apply_settings_operations(station.settings, prepared["body"]["operations"])
            command.save()
            for prepared in self._prepared_commands[1:]:
                StationCommandV2.objects.create(
                    nomenclature=station, kind=prepared["kind"], body=prepared["body"],
                )


@admin.register(StationCredential)
class StationCredentialAdmin(admin.ModelAdmin):
    list_select_related = ("nomenclature",)
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    list_per_page = 50
    list_display = ("nomenclature", "is_active", "rotated_at")
    list_filter = ("is_active",)
    search_fields = ("nomenclature__name", "nomenclature__code1c")
    autocomplete_fields = ("nomenclature",)
    readonly_fields = ("token_hash", "created_at", "rotated_at")
    fields = ("nomenclature", "is_active", "token_hash", "created_at", "rotated_at")
    actions = ("rotate_tokens",)

    @admin.action(description="Rotate station tokens")
    def rotate_tokens(self, request, queryset):
        credentials = list(queryset[:2])
        if len(credentials) != 1:
            self.message_user(
                request, "Выберите одну станцию, чтобы получить её новый токен.",
                level=messages.ERROR,
            )
            return
        token = issue_station_token(credentials[0])
        self.message_user(
            request,
            f"New station token (copy now; it will not be shown again): {token}",
            level=messages.WARNING,
        )

    def save_model(self, request, obj, form, change):
        if change:
            super().save_model(request, obj, form, change)
            return

        token = generate_station_token()
        obj.token_hash = hash_station_token(token)
        super().save_model(request, obj, form, change)
        self.message_user(
            request,
            f"Station token (copy now; it will not be shown again): {token}",
            level=messages.WARNING,
        )


@admin.register(StationInstallation)
class StationInstallationAdmin(admin.ModelAdmin):
    """Показывает привязки, созданные автоматически после входа Player."""
    list_select_related = ("nomenclature", "created_by")
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    list_per_page = 50

    list_display = (
        "installation_id",
        "nomenclature",
        "created_by",
        "is_active",
        "created_at",
        "rotated_at",
    )
    list_filter = ("is_active",)
    search_fields = ("id", "nomenclature__name", "nomenclature__code1c", "created_by__email")
    autocomplete_fields = ("nomenclature", "created_by")
    readonly_fields = (
        "id",
        "nomenclature",
        "created_by",
        "is_active",
        "token_hash",
        "created_at",
        "rotated_at",
    )
    fields = ("id", "nomenclature", "created_by", "is_active", "token_hash", "created_at", "rotated_at")
    actions = ("revoke_installations",)

    @admin.display(description="ID установки", ordering="id")
    def installation_id(self, obj):
        return str(obj.pk)

    def has_add_permission(self, request):
        """Установки создаёт только защищённый endpoint привязки Player."""
        return False

    def has_delete_permission(self, request, obj=None):
        """История привязок нужна для аудита и не удаляется из admin."""
        return False

    @admin.action(description="Отозвать выбранные установки Player")
    def revoke_installations(self, request, queryset):
        revoked = queryset.filter(is_active=True).update(is_active=False)
        if revoked:
            self.message_user(request, f"Отозвано установок: {revoked}.", level=messages.SUCCESS)
            return
        self.message_user(request, "Среди выбранных установок нет активных.", level=messages.WARNING)


@admin.register(StationCommandV2)
class StationCommandV2Admin(admin.ModelAdmin):
    """Ставит выбранные настройки в очередь одной отправкой формы."""
    list_select_related = ("nomenclature",)
    show_full_result_count = False
    show_facets = admin.ShowFacets.NEVER
    list_per_page = 50

    form = StationVolumeCommandForm
    list_display = ("nomenclature", "kind", "delivery_state", "created_at", "updated_at")
    list_filter = ("status", "kind")
    search_fields = ("nomenclature__name", "nomenclature__code1c", "command_id")
    autocomplete_fields = ("nomenclature",)
    readonly_fields = (
        "command_id",
        "kind",
        "body",
        "result",
        "delivered_at",
        "created_at",
        "updated_at",
    )

    def get_urls(self):
        return [
            path("station-devices/", self.admin_site.admin_view(self.station_devices_view),
                 name="nomenclatures_stationcommandv2_devices"),
        ] + super().get_urls()

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "nomenclature" in form.base_fields:
            form.base_fields["nomenclature"].widget.attrs["data-station-devices-url"] = reverse(
                "admin:nomenclatures_stationcommandv2_devices"
            )
        return form

    def station_devices_view(self, request):
        if request.method != "GET":
            return HttpResponseNotAllowed(["GET"])
        if not self.has_add_permission(request):
            raise PermissionDenied
        try:
            station = Nomenclature.objects.only("name", "station_capabilities", "settings").filter(
                pk=request.GET.get("station")
            ).first()
        except (ValidationError, ValueError, TypeError):
            station = None
        if station is None:
            return JsonResponse({"error": "Точка не найдена."}, status=404)
        station_admin = self.admin_site.get_model_admin(Nomenclature)
        if not station_admin.has_view_or_change_permission(request, station):
            raise PermissionDenied
        return JsonResponse({
            "audio": _audio_device_choices(station),
            "displays": _display_choices(station),
            "default_volumes": _station_default_volumes(station),
            "custom_volumes": _station_custom_volumes(station),
            "settings_revision": _latest_saved_revision(station),
        })

    @admin.display(description="Состояние доставки", ordering="delivered_at")
    def delivery_state(self, obj):
        if obj.status == StationCommandV2.Status.APPLIED:
            return "Применена"
        if obj.status == StationCommandV2.Status.FAILED:
            return "Ошибка применения"
        if obj.delivered_at is not None:
            return "Доставлена, ждёт подтверждения"
        return "Ожидает отправки"

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return (
                (
                    "Область изменения",
                    {"fields": ("nomenclature", "setting_groups", "settings_revision"), "classes": ("station-command-choices",)},
                ),
                (
                    "Громкость канала",
                    {
                        "fields": (
                            "volume_day",
                            "background_left_volume",
                            "background_right_volume",
                            "advertisement_left_volume",
                            "advertisement_right_volume",
                            "volume_all_days",
                        ),
                        "classes": ("station-command-volume",),
                    },
                ),
                (
                    "Громкость по времени",
                    {"fields": ("interval_volume_rows",), "classes": ("station-command-interval_volume",)},
                ),
                (
                    "Фоновый контент",
                    {
                        "fields": (
                            "background_day",
                            *(f"background_{key}" for key, _ in BACKGROUND_SWITCHES),
                            "image_duration",
                            "background_all_days",
                        ),
                        "classes": ("station-command-background",),
                    },
                ),
                (
                    "Рабочее время",
                    {
                        "fields": ("worktime_day", "full_day", "worktime_start", "worktime_end", "worktime_all_days"),
                        "classes": ("station-command-worktime",),
                    },
                ),
                (
                    "Аудиовыход Player",
                    {"fields": ("audio_device_id",), "classes": ("station-command-audio_device",)},
                ),
                (
                    "Экран вывода Player",
                    {"fields": ("display_id",), "classes": ("station-command-display",)},
                ),
                (
                    "Поворот визуального вывода",
                    {"fields": ("visual_output_rotation",), "classes": ("station-command-visual_output",)},
                ),
            )
        return (("Команда", {"fields": ("nomenclature",) + self.readonly_fields}),)

    def has_change_permission(self, request, obj=None):
        return False

    def add_view(self, request, form_url="", extra_context=None):
        try:
            return super().add_view(request, form_url, extra_context)
        except (ValidationError, SettingsPatchError) as exc:
            # Между проверкой формы и сохранением Player мог подтвердить
            # другую команду. Транзакция уже откатила весь пакет.
            self.message_user(request, f"Настройки не отправлены: {exc}", level=messages.ERROR)
            return HttpResponseRedirect(request.path)

    def save_model(self, request, obj, form, change):
        form.save_commands(obj)
