"""Per-file daily plan and confirmed completion facts for advertising orders."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Any
from uuid import UUID

from django.conf import settings
from django.db.models import Count, OuterRef, Subquery
from django.utils import timezone

from nomenclatures.models import StationCommandV2
from nomenclatures.player_v2.playback.models import PlaybackEvent
from nomenclatures.player_v2.playback.service import completed_playbacks
from orders.models import OrderStationState


_DAY_KEYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_UNPLANNED_BROADCAST_TYPES = {6, 7}
_WORKTIME_BROADCAST_TYPES = {0, 1, 2, 4, 5}


def report_for_order(order, day: date, *, now: datetime | None = None) -> dict[str, Any]:
    """Build the daily plan from an immutable manifest and actual completions.

    Player has no historical copy of a station's worktime profile. The plan
    therefore uses the current profile; actual completion events remain tied
    to the immutable revision that Player received.
    """
    manifest = _manifest_for_report(order)
    if manifest is None:
        return _unavailable_report(order, day, "Для этой редакции нет неизменяемого манифеста Player.")

    body, revision, cancelled_revision = manifest
    parameters = body["task"]["parameters"]
    try:
        files = _manifest_files(body, parameters["playlist"]["files"])
    except ValueError as exc:
        return _unavailable_report(order, day, str(exc), revision=revision)
    completed = _completed_counts(order, revision, day, [item["file_id"] for item in files])
    broadcast_type = parameters.get("broadcast_type")

    if order.placement != "advertising" or type(broadcast_type) is not int:
        return _unavailable_report(
            order, day, "Дневной план доступен только для рекламного заказа.", files, completed, revision
        )
    if broadcast_type in _UNPLANNED_BROADCAST_TYPES:
        reason = (
            "Непрерывная реклама не имеет заданной частоты выходов."
            if broadcast_type == 7
            else "Реклама по событию не имеет заданного расписания."
        )
        return _unplanned_report(order, day, files, completed, reason, revision)

    try:
        occurrences, uses_current_worktime = _occurrences(parameters, order.nomenclature, day)
    except ValueError as exc:
        return _unavailable_report(order, day, str(exc), files, completed, revision)

    planned_by_file = Counter()
    due_by_file = Counter()
    local_now = _local_naive(now or datetime.now())
    for occurrence, index in occurrences:
        file_id = files[index % len(files)]["file_id"]
        planned_by_file[file_id] += 1
        if occurrence <= local_now:
            due_by_file[file_id] += 1

    rows = []
    for item in files:
        file_id = item["file_id"]
        planned = planned_by_file[file_id]
        due = due_by_file[file_id]
        completed_count = completed[file_id]
        rows.append({
            **item,
            "planned": planned,
            "due": due,
            "completed": completed_count,
            "missing": max(due - completed_count, 0),
            "future": planned - due,
            "extra": max(completed_count - planned, 0),
        })

    notes = [
        "Факт — только подтверждённые полные завершения с началом воспроизведения в выбранный день.",
        "«Не подтверждено» не доказывает пропуск: событие могло ещё не прийти с Player.",
    ]
    if uses_current_worktime:
        notes.append(
            "Исторического снимка рабочего времени нет: план реконструирован по текущим настройкам точки."
        )
    if cancelled_revision:
        notes.append(
            "Для отмены показано последнее отправленное расписание. Время фактической остановки в этом плане не учтено."
        )
    return {
        "day": day.isoformat(),
        "order_id": str(order.pk),
        "revision": revision,
        "plan_supported": True,
        "plan_source": "immutable_current_revision_manifest",
        "rows": rows,
        "summary": _summary(rows, planned=True),
        "notes": notes,
    }


def _manifest_for_report(order) -> tuple[dict[str, Any], int, bool] | None:
    """Select the exact revision whose media could have reached Player."""
    commands = StationCommandV2.objects.filter(
        nomenclature_id=order.nomenclature_id,
        kind="apply_order_manifest",
        body__order_id=str(order.pk),
    )
    cancelled = order.status == 3
    command = commands.filter(body__revision=order.revision).order_by("-created_at").only("body").first()
    if command is None:
        if not cancelled:
            try:
                cancelled = order.station_state.desired_action == "cancel"
            except OrderStationState.DoesNotExist:
                pass
        if cancelled:
            command = commands.filter(body__revision__lte=order.revision).order_by("-created_at").only("body").first()
    body = command.body if command is not None and isinstance(command.body, dict) else None
    task = body.get("task") if isinstance(body, dict) else None
    parameters = task.get("parameters") if isinstance(task, dict) else None
    playlist = parameters.get("playlist") if isinstance(parameters, dict) else None
    files = playlist.get("files") if isinstance(playlist, dict) else None
    revision = body.get("revision") if isinstance(body, dict) else None
    if (
        not isinstance(parameters, dict)
        or not isinstance(files, list)
        or not files
        or not isinstance(parameters.get("order_parameters"), dict)
        or type(revision) is not int
    ):
        return None
    return body, revision, cancelled


def _manifest_files(manifest: dict[str, Any], playlist_files: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Use the delivered file names and Player's immutable playlist order."""
    media = manifest.get("files")
    if not isinstance(media, list):
        raise ValueError("Манифест не содержит корректного списка медиафайлов.")
    names = {
        str(item.get("id")): item.get("name")
        for item in media
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in playlist_files:
        file_id = str(item.get("id")) if isinstance(item, dict) and item.get("id") else ""
        try:
            UUID(file_id)
        except ValueError as exc:
            raise ValueError("Манифест содержит неверный идентификатор файла.") from exc
        if not file_id or file_id in seen:
            continue
        seen.add(file_id)
        rows.append({"file_id": file_id, "file_name": names.get(file_id) or file_id})
    if not rows:
        raise ValueError("Манифест не содержит файлов рекламного плейлиста.")
    return rows


def _occurrences(
    parameters: dict[str, Any], nomenclature, day: date
) -> tuple[list[tuple[datetime, int]], bool]:
    broadcast_type = parameters.get("broadcast_type")
    options = parameters["order_parameters"]
    times = options.get("times_in_hour")
    if type(times) is not int or not 1 <= times <= 60:
        raise ValueError("В неизменяемом манифесте нет корректного числа выходов в час.")
    order_start = _parse_datetime(parameters.get("broadcast_start"), "начала заказа")
    order_end = _parse_datetime(parameters.get("broadcast_end"), "окончания заказа")
    if order_start >= order_end:
        raise ValueError("В неизменяемом манифесте указан некорректный период заказа.")

    windows = _windows_for_day(
        broadcast_type, options, nomenclature, day, order_start, order_end
    )
    interval_seconds = 3600 / times
    occurrences: list[tuple[datetime, int]] = []
    for window_start, window_end in windows:
        index = 0
        occurrence = window_start
        while occurrence < window_end:
            if occurrence.date() == day:
                occurrences.append((occurrence, index))
            index += 1
            # Indexed construction matches Player's fractional-slot clock.
            occurrence = window_start + timedelta(seconds=index * interval_seconds)
    return occurrences, broadcast_type in _WORKTIME_BROADCAST_TYPES


def _windows_for_day(
    broadcast_type: int,
    options: dict[str, Any],
    nomenclature,
    day: date,
    order_start: datetime,
    order_end: datetime,
) -> list[tuple[datetime, datetime]]:
    if broadcast_type not in {0, 1, 2, 3, 4, 5}:
        raise ValueError("Правило вещания не поддерживает дневной план.")
    if broadcast_type == 3:
        start = _combine(day, _clock(options.get("start_time"), "start_time"))
        end = _combine(day, _clock(options.get("end_time"), "end_time"))
        return _clip_windows([(start, end)], order_start, order_end)

    work_start, work_end = _worktime(nomenclature, day)
    result = []
    for shift_start, shift_end in _worktime_windows(day, work_start, work_end):
        start, end = shift_start, shift_end
        if broadcast_type == 1:
            start += timedelta(seconds=_offset(options))
        elif broadcast_type == 2:
            end -= timedelta(seconds=_offset(options))
        elif broadcast_type == 4:
            end = _clock_in_shift(options.get("end_time"), shift_start, shift_end)
        elif broadcast_type == 5:
            start = _clock_in_shift(options.get("start_time"), shift_start, shift_end)
        result.append((start, end))
    return _clip_windows(result, order_start, order_end)


def _worktime(nomenclature, day: date) -> tuple[time, time]:
    settings_document = nomenclature.settings if isinstance(nomenclature.settings, dict) else {}
    day_settings = settings_document.get(_DAY_KEYS[day.weekday()])
    worktime = day_settings.get("worktime") if isinstance(day_settings, dict) else None
    if not isinstance(worktime, str) or "-" not in worktime:
        raise ValueError("У точки нет подтверждённого рабочего времени для выбранного дня.")
    start, end = worktime.split("-", 1)
    return _clock(start, "worktime"), _clock(end, "worktime")


def _worktime_windows(day: date, work_start: time, work_end: time) -> list[tuple[datetime, datetime]]:
    start = _combine(day, work_start)
    end = _combine(day, work_end)
    if end > start:
        return [(start, end)]
    # Player uses the selected calendar day's profile in both halves of an
    # overnight shift.
    return [(start - timedelta(days=1), end), (start, end + timedelta(days=1))]


def _clock_in_shift(value: Any, shift_start: datetime, shift_end: datetime) -> datetime:
    candidate = _combine(shift_start.date(), _clock(value, "время правила"))
    if shift_end.date() != shift_start.date() and candidate < shift_start:
        candidate += timedelta(days=1)
    return candidate


def _clip_windows(
    windows: list[tuple[datetime, datetime]], order_start: datetime, order_end: datetime
) -> list[tuple[datetime, datetime]]:
    clipped = []
    for start, end in windows:
        start, end = max(start, order_start), min(end, order_end)
        if start < end:
            clipped.append((start, end))
    return clipped


def _offset(options: dict[str, Any]) -> int:
    """Decode current HH:MM:SS and legacy numeric minutes."""
    value = options.get("timedelta")
    if isinstance(value, str):
        try:
            hours, minutes, seconds = (int(part) for part in value.split(":"))
        except (TypeError, ValueError) as exc:
            raise ValueError("В неизменяемом манифесте нет корректного смещения времени.") from exc
        if hours < 0 or not 0 <= minutes < 60 or not 0 <= seconds < 60:
            raise ValueError("В неизменяемом манифесте нет корректного смещения времени.")
        return hours * 3600 + minutes * 60 + seconds
    if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
        return int(value * 60)
    raise ValueError("В неизменяемом манифесте нет корректного смещения времени.")


def _clock(value: Any, field: str) -> time:
    try:
        return time.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"В неизменяемом манифесте нет корректного {field}.") from exc


def _combine(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock)


def _parse_datetime(value: Any, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"В неизменяемом манифесте нет корректного {field}.") from exc
    return _local_naive(parsed)


def _local_naive(value: datetime) -> datetime:
    if timezone.is_aware(value):
        return timezone.localtime(value).replace(tzinfo=None)
    return value


def _completed_counts(order, revision: int, day: date, file_ids: list[str]) -> Counter:
    lower, upper = _query_bounds(day)
    starts = PlaybackEvent.objects.filter(
        nomenclature_id=OuterRef("nomenclature_id"),
        playback_id=OuterRef("playback_id"),
        event_type="started",
        event_sequence=1,
        order_id=OuterRef("order_id"),
        order_revision=OuterRef("order_revision"),
        file_id=OuterRef("file_id"),
    ).order_by("event_sequence")
    rows = (
        completed_playbacks()
        .filter(
            nomenclature_id=order.nomenclature_id,
            order_id=order.pk,
            order_revision=revision,
            media_type="ad",
            file_id__in=file_ids,
        )
        .annotate(started_at=Subquery(starts.values("occurred_at")[:1]))
        .filter(started_at__gte=lower, started_at__lt=upper)
        .values("file_id")
        .annotate(total=Count("event_id"))
    )
    return Counter({str(row["file_id"]): row["total"] for row in rows})


def _query_bounds(day: date) -> tuple[datetime, datetime]:
    lower = datetime.combine(day, time.min)
    upper = lower + timedelta(days=1)
    if settings.USE_TZ:
        return timezone.make_aware(lower), timezone.make_aware(upper)
    return lower, upper


def _unavailable_report(
    order,
    day: date,
    note: str,
    files: list[dict[str, str]] | None = None,
    completed: Counter | None = None,
    revision: int | None = None,
) -> dict[str, Any]:
    files = files or []
    completed = completed or Counter()
    rows = [
        {
            **item,
            "planned": None,
            "due": None,
            "completed": completed[item["file_id"]],
            "missing": None,
            "future": None,
            "extra": None,
        }
        for item in files
    ]
    return {
        "day": day.isoformat(),
        "order_id": str(order.pk),
        "revision": revision if revision is not None else order.revision,
        "plan_supported": False,
        "plan_source": "unavailable",
        "rows": rows,
        "summary": _summary(rows, planned=False),
        "notes": [note],
    }


def _unplanned_report(order, day, files, completed, note, revision):
    return _unavailable_report(order, day, note, files, completed, revision)


def _summary(rows: list[dict[str, Any]], *, planned: bool) -> dict[str, int | None]:
    total_completed = sum(row["completed"] for row in rows)
    if not planned:
        return {
            "planned": None,
            "due": None,
            "completed": total_completed,
            "missing": None,
            "future": None,
            "extra": None,
        }
    return {
        key: sum(row[key] for row in rows)
        for key in ("planned", "due", "completed", "missing", "future", "extra")
    }
