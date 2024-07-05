from django.apps import AppConfig


class FilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'files'
    verbose_name = 'Файлы'

    def ready(self):
        """Вызов функции по инициализации бакетов при запуске приложения."""
        from . import minio_setup
        minio_setup.initialize_minio_buckets()
