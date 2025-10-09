from django.apps import AppConfig
from django.conf import settings


class FilesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'files'
    verbose_name = 'Файлы'

    def ready(self):
        """Инициализация бакетов MinIO — только если MinIO реально доступен."""
        # 🚫 Не выполняем в DEBUG-режиме (локально)
        if getattr(settings, 'DEBUG', True):
            print("🧩 DEBUG=True → пропускаем инициализацию MinIO")
            return

        # 🚫 Не выполняем, если MINIO_ENDPOINT не задан
        if not getattr(settings, 'MINIO_ENDPOINT', None):
            print("⚠️ MINIO_ENDPOINT не задан → пропускаем инициализацию MinIO")
            return

        # ✅ Только теперь пытаемся подключиться
        try:
            from . import minio_setup
            minio_setup.initialize_minio_buckets()
            print("✅ MinIO бакеты проверены/созданы")
        except Exception as e:
            print(f"⚠️ Ошибка при инициализации MinIO: {e}")
