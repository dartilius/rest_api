from django.db import models


class BroadcastFormat(models.TextChoices):
    AUDIO = "audio", "Аудиовещание"
    SCREENS = "screens", "Вещание на экранах"
    AUDIO_SCREENS = "audio-screens", "Аудио + экраны"
    VIDEO_MENU = "video-menu", "Видеоменю"
    MULTIMEDIA = "multimedia", "Мультимедийное вещание"


DEMO_FORMAT_CHOICES = [*BroadcastFormat.choices, ("corporate-network", "Корпоративная сеть")]
BUSINESS_TYPES = ("store", "cafe", "restaurant", "shopping-center", "office", "fitness", "hotel", "other")
CONTENT_LABELS = {
    "music": "Музыкальный фон", "announcements": "Объявления",
    "ads": "Рекламные ролики", "jingles": "Фирменные джинглы",
    "slides": "Слайд-шоу", "video_content": "Видеоконтент",
    "information": "Информация для посетителей", "menu": "Блюда и цены",
    "seasonal": "Сезонные предложения", "promotions": "Акции и рекламные вставки",
}
FORMAT_CONTENT = {
    "audio": {"music", "ads", "announcements", "jingles"},
    "screens": {"slides", "video_content", "information"},
    "audio-screens": {"music", "announcements", "slides", "promotions"},
    "video-menu": {"menu", "seasonal", "promotions"},
    "multimedia": {"music", "video_content", "slides"},
}
# Browser-compatible formats; file.type alone is insufficient (ad can be video).
MEDIA_RULES = {
    "audio": ({0, 4}, {".mp3", ".wav", ".ogg", ".m4a"}),
    "video": ({1, 4}, {".mp4", ".webm"}),
    "image": ({2}, {".jpg", ".jpeg", ".png", ".webp"}),
    "poster": ({2}, {".jpg", ".jpeg", ".png", ".webp"}),
}
