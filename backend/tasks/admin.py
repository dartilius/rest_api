from django.contrib import admin

from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Репликация."""

    list_display = (
        'id',
        'client',
        'owner',
        'type',
        'parameters',
        'created',
        'updated',
        'status'
    )
    search_fields = (
        'id',
        'client',
        'type',
        'status'
    )

    def get_queryset(self, request):
        return Task.objects.all().select_related('owner', 'client')
