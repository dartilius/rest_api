"""Human-readable station playback snapshots; no settings or transport metadata."""

MODES = {
    "starting": "Запуск Player", "idle": "Ожидание контента",
    "music": "Фоновый контент", "background": "Фоновый контент",
    "ad": "Реклама", "maintenance": "Сервисный режим",
    "paused": "Воспроизведение на паузе", "stopped": "Воспроизведение остановлено",
    "error": "Ошибка воспроизведения",
}
MEDIA_TYPES = {0: "Музыка", 1: "Видео", 2: "Изображение", 3: "Бегущая строка"}
AD_TYPES = {
    "AUDIO_ONLY": "Аудиореклама", "audio": "Аудиореклама",
    "VIDEO": "Видеореклама", "video": "Видеореклама",
    "IMAGE_AUDIO": "Аудиореклама с изображениями", "image_audio": "Аудиореклама с изображениями",
}
STATUSES = {
    "играет": "Воспроизводится", "playing": "Воспроизводится",
    "пауза": "На паузе", "paused": "На паузе",
    "остановлен": "Остановлено", "stopped": "Остановлено",
    "completed": "Завершено", "ended": "Завершено",
    "buffering": "Подготовка к воспроизведению", "error": "Ошибка воспроизведения",
}


def human_duration(value, *, milliseconds=True, unknown_zero=False):
    if type(value) not in (int, float) or not 0 <= value <= 9_007_199_254_740_991:
        return "Не определена"
    if value == 0 and unknown_zero:
        return "Не определена"
    seconds = int(value / (1000 if milliseconds else 1))
    if value > 0 and seconds == 0:
        return "Менее секунды"
    hours, remaining = divmod(seconds, 3600)
    minutes, seconds = divmod(remaining, 60)
    parts = []
    if hours:
        parts.append(f"{hours} ч")
    if minutes:
        parts.append(f"{minutes} мин")
    if seconds or not parts:
        parts.append(f"{seconds} сек")
    return " ".join(parts)


def _time(item, field, *, duration=False):
    if f"{field}_ms" in item:
        return human_duration(item[f"{field}_ms"], unknown_zero=duration)
    if f"{field}_seconds" in item:
        return human_duration(item[f"{field}_seconds"], milliseconds=False, unknown_zero=duration)
    return human_duration(item.get(field), unknown_zero=duration)


def _label(value, labels, fallback):
    return labels.get(value, fallback) if isinstance(value, str) else fallback


def _content(item, *, advertisement=False, mode=None):
    media_type = item.get("type")
    if advertisement:
        label = _label(media_type, AD_TYPES, "Реклама")
    else:
        label = MEDIA_TYPES.get(media_type, "Контент") if type(media_type) is int else "Контент"
    status = _label(item.get("status"), STATUSES, "Состояние не передано")
    if advertisement and "status" not in item and mode == "ad":
        status = "Воспроизводится"
    if media_type == 2 and not advertisement and status == "Воспроизводится":
        status = "Показывается"
    name = item.get("name")
    duration = _time(item, "duration", duration=True)
    if advertisement and "duration_ms" not in item and "duration_seconds" in item:
        # Older Player exported its millisecond callback under this wrong name.
        # Keep those already saved snapshots readable until Player is updated.
        duration = human_duration(item["duration_seconds"], unknown_zero=True)
    return {
        "name": name if isinstance(name, str) and name else "Название не передано",
        "type": label, "status": status,
        "duration": duration,
        "position": _time(item, "position"),
    }


def broadcast_context(runtime):
    state = runtime if isinstance(runtime, dict) else {}
    mode = state.get("mode")
    advertisement = state.get("current_ad")
    backgrounds = state.get("background")
    error = state.get("last_error")
    return {
        "has_state": any(key in state for key in ("mode", "maintenance_mode", "current_ad", "background", "last_error")),
        "mode": _label(mode, MODES, "Режим не определён"),
        "maintenance": "Включён" if state.get("maintenance_mode") is True else "Выключен" if state.get("maintenance_mode") is False else "Состояние не передано",
        "advertisement": _content(advertisement, advertisement=True, mode=mode) if isinstance(advertisement, dict) and advertisement else None,
        "background": [_content(item) for item in backgrounds if isinstance(item, dict)] if isinstance(backgrounds, list) else [],
        "error": error if isinstance(error, str) else None,
    }
