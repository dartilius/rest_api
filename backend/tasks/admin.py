from django.contrib import admin
from datetime import timedelta

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

                client = get_minio_client()
                objects = client.list_objects(
                    'builds',
                    prefix='RMCContentPlayer-',
                    recursive=False
                )

                versions = []
                for item in objects:
                    name = item.object_name
                    if name.startswith('RMCContentPlayer-') and name.endswith('.exe'):
                        version = name.replace('RMCContentPlayer-', '').replace('.exe', '')
                        versions.append(version)

                if not versions:
                    obj.parameters = {
                        'url': '',
                        'version': ''
                    }
                    super().save_model(request, obj, form, change)
                    self.message_user(request, 'Нет доступных версий для обновления.', level='ERROR')
                    return

                versions.sort(key=lambda v: tuple(map(int, v.split('.'))))
                latest_version = versions[-1]

                external_client = get_minio_client(external=True)
                version_url = external_client.get_presigned_url(
                    'GET',
                    'builds',
                    f'RMCContentPlayer-{latest_version}.exe',
                    expires=timedelta(hours=24)
                )

                obj.parameters = {
                    'url': version_url,
                    'version': latest_version
                }

            except Exception as e:
                obj.parameters = {
                    'url': '',
                    'version': ''
                }

        super().save_model(request, obj, form, change)


# from django.contrib import admin
# from django.utils import timezone
# from datetime import timedelta

# from tasks.models import Task


# @admin.register(Task)
# class TaskAdmin(admin.ModelAdmin):
#     """Репликация."""

#     @admin.display(description='Тип')
#     def type(self, obj):
#         return obj.__str__

#     list_display = (
#         'id',
#         'client',
#         'owner',
#         'type',
#         'created',
#         'updated',
#         'status'
#     )
#     search_fields = (
#         'id',
#         'client__name',
#         'type',
#         'status'
#     )
#     raw_id_fields = ('client', 'owner')
#     show_full_result_count = False

#     def get_queryset(self, request):
#         return Task.objects.all().select_related('owner', 'client')

#     def save_model(self, request, obj, form, change):
#         if obj.type == 16 and not obj.parameters:
#             try:
#                 from datetime import timedelta
#                 from api.constants import get_minio_client

#                 client = get_minio_client()
#                 objects = client.list_objects('builds', prefix='RMCContentPlayer-', recursive=False)

#                 versions = []
#                 for item in objects:
#                     name = item.object_name
#                     if name.startswith('RMCContentPlayer-') and name.endswith('.exe') and name != 'RMCContentPlayer-latest.exe':
#                         version = name.replace('RMCContentPlayer-', '').replace('.exe', '')
#                         versions.append(version)

#                 versions.sort()
#                 latest_version = versions[-1] if versions else 'latest'

#                 external_client = get_minio_client(external=True)
#                 version_url = external_client.get_presigned_url(
#                     'GET',
#                     'builds',
#                     f'RMCContentPlayer-{latest_version}.exe',
#                     expires=timedelta(hours=24)
#                 )

#                 obj.parameters = {
#                     'url': version_url,
#                     'version': latest_version
#                 }
#             except Exception as e:
#                 obj.parameters = {
#                     'url': '',
#                     'version': ''
#                 }
#         super().save_model(request, obj, form, change)

# from django.contrib import admin

# from tasks.models import Task


# @admin.register(Task)
# class TaskAdmin(admin.ModelAdmin):
#     """Репликация."""

#     @admin.display(description='Тип')
#     def type(self, obj):
#         return obj.__str__

#     list_display = (
#         'id',
#         'client',
#         'owner',
#         'type',
#         'created',
#         'updated',
#         'status'
#     )
#     search_fields = (
#         'id',
#         'client__name',
#         'type',
#         'status'
#     )
#     raw_id_fields = ('client', 'owner')
#     show_full_result_count = False

#     def get_queryset(self, request):
#         return Task.objects.all().select_related('owner', 'client')
