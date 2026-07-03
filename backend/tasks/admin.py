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
            from api.constants import get_minio_client
            try:
                client = get_minio_client(external=True)
                version_url = client.get_presigned_url(
                    'GET',
                    'builds',
                    'RMCContentPlayer-latest.exe',
                    expires=timedelta(hours=24)
                )
                obj.parameters = {
                    'responsible': request.user.full_name,
                    'url': version_url
                }
            except Exception as e:
                obj.parameters = {
                    'responsible': request.user.full_name,
                    'url': ''
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
