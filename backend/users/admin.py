from django.contrib import admin

from users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Пользователь."""

    @admin.display(description='ФИО')
    def full_name(self, obj):
        """Возвращает полное имя пользователя одним полем."""
        if obj.middle_name:
            return f'{obj.last_name} {obj.first_name} {obj.middle_name}'
        else:
            return f'{obj.last_name} {obj.first_name}'

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
