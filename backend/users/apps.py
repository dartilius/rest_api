from django.apps import AppConfig


class CustomUsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    def ready(self):
        import users.privacy_signals  # noqa: F401
    verbose_name = 'Пользователи'
