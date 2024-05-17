from django.contrib import admin

from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Пользователь."""

    @admin.display(description='ФИО')
    def full_name(self, obj):
        """Возвращает полное имя пользователя одним полем."""
        return (
            f'{obj.last_name} {obj.first_name} {obj.middle_name}'
            if obj.middle_name else f'{obj.last_name} {obj.first_name}'
        )

    list_display = (
        'id',
        'full_name',
        'role',
        'email',
        'phone_number',
        'is_active',
        'created',
    )
    search_fields = (
        'id',
        'full_name',
        'role',
        'is_active'
    )

    # def get_queryset(self, request):
    #     return CustomUser.objects.all().select_related('')
