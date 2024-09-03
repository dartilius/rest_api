from django.contrib import admin

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

    def get_queryset(self, request):
        return Task.objects.all().select_related('owner', 'client')
