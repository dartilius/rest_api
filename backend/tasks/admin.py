from django.contrib import admin
from datetime import timedelta
import re

from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Репликация."""

    @admin.display(description='Тип')
    def type(self, obj):
        return obj.__str__

    list_display = (
        'id',
        'client',
        'owner',
        'type',
        'created',
        'updated',
        'status'
    )
    search_fields = (
        'id',
        'client__name',
        'type',
        'status'
    )
    raw_id_fields = ('client', 'owner')
    show_full_result_count = False

    def get_queryset(self, request):
        return Task.objects.all().select_related('owner', 'client')

    def save_model(self, request, obj, form, change):
        if obj.type == 16 and not obj.parameters:
            try:
                from api.constants import get_minio_client
                
                BUILD_BUCKET = "builds"
                BUILD_PREFIX = "RMCContentPlayer-"
                BUILD_SUFFIX = ".exe"
                SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")

                client = get_minio_client()
                
                # Собираем доступные версии
                available_versions = []
                objects = client.list_objects(
                    BUILD_BUCKET,
                    prefix=BUILD_PREFIX,
                    recursive=False
                )

                for item in objects:
                    object_name = item.object_name
                    if not (object_name.startswith(BUILD_PREFIX) and object_name.endswith(BUILD_SUFFIX)):
                        continue

                    version = object_name[len(BUILD_PREFIX):-len(BUILD_SUFFIX)]
                    if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)*", version):
                        continue

                    version_key = tuple(int(part) for part in version.split("."))
                    available_versions.append((version_key, version, object_name))

                if not available_versions:
                    obj.parameters = {
                        'url': '',
                        'version': ''
                    }
                    super().save_model(request, obj, form, change)
                    self.message_user(request, 'Нет доступных версий для обновления.', level='ERROR')
                    return

                # Получаем последнюю версию
                _, latest_version, object_name = max(available_versions, key=lambda item: item[0])

                # Получаем SHA-256 из метаданных
                object_info = client.stat_object(BUILD_BUCKET, object_name)
                raw_metadata = getattr(object_info, "metadata", {}) or {}

                metadata = {
                    str(key).strip().lower(): str(value).strip()
                    for key, value in raw_metadata.items()
                }

                sha256 = (
                    metadata.get("x-amz-meta-sha256")
                    or metadata.get("sha256")
                    or ""
                ).lower()

                if not SHA256_PATTERN.fullmatch(sha256):
                    obj.parameters = {
                        'url': '',
                        'version': latest_version,
                        'sha256': '',
                        'error': 'Отсутствует корректный SHA-256'
                    }
                    super().save_model(request, obj, form, change)
                    self.message_user(request, f'Для версии {latest_version} не найден корректный SHA-256.', level='ERROR')
                    return

                # Генерируем presigned URL через внешний клиент
                external_client = get_minio_client(external=True)
                version_url = external_client.get_presigned_url(
                    'GET',
                    BUILD_BUCKET,
                    object_name,
                    expires=timedelta(hours=24)
                )

                # Сохраняем все параметры включая sha256
                obj.parameters = {
                    'url': version_url,
                    'version': latest_version,
                    'sha256': sha256,
                    'size': object_info.size,
                    'object_name': object_name,
                }

            except Exception as e:
                obj.parameters = {
                    'url': '',
                    'version': '',
                    'error': str(e)
                }
                self.message_user(request, f'Ошибка при создании обновления: {e}', level='ERROR')

        super().save_model(request, obj, form, change)