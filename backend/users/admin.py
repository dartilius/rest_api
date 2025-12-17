from django.contrib import admin

from users.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Пользователь."""

    list_display = (
        'id',
        'full_name_display',
        'role',
        'email',
        'phone_number',
        'is_active',
        'created',
    )
    search_fields = (
        'id',
        'last_name',
        'first_name',
        'middle_name',
        'role',
        'is_active',
    )
    show_full_result_count = False

    @admin.display(description='ФИО')
    def full_name_display(self, obj):
        return obj.full_name
