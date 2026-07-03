from django.contrib import admin
from django.utils import timezone
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
            import os
            from datetime import timedelta
            from api.constants import get_minio_client
            from django.conf import settings
        
            try:
                client = get_minio_client(external=True)
                version_url = client.get_presigned_url(
                    'GET',
                    'builds',
                    'RMCContentPlayer-latest.exe',
                    expires=timedelta(hours=24)
                )
            
                version = os.environ.get('APP_VERSION', '1.0.0')
                version_file = os.path.join(settings.BASE_DIR, '..', 'version.txt')
                if os.path.exists(version_file):
                    with open(version_file) as f:
                        version = f.read().strip()
            
                obj.parameters = {
                    'url': version_url,
                    'version': version
                }
            except Exception as e:
                obj.parameters = {
                    'url': '',
                    'version': ''
                }
        super().save_model(request, obj, form, change)

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
