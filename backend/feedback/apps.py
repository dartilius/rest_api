from django.apps import AppConfig


class FeedbackConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "feedback"
    verbose_name = "Обратная связь"

    def ready(self) -> None:
        import feedback.signals  # noqa: F401  подключаем сигналы