from django.contrib import admin, messages
from django.utils.translation import ngettext
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


class CustomOutstandingTokenAdmin(OutstandingTokenAdmin):
    """Даёт возможность удалять токены через админ-панель."""

    actions = ['delete']

    def has_delete_permission(self, *args, **kwargs):
        return True

    @admin.action(description='Удалить выбранные токены')
    def delete(self, request, queryset):
        """Удаление токенов."""
        try:
            updated = queryset.delete()
            self.message_user(
                request,
                ngettext(
                    f'{updated} запрос на отмену заказа принят',
                    f'{updated} запросов на отмену заказов принято',
                    updated,
                ),
                messages.SUCCESS
            )
        except Exception as e:
            self.message_user(request, e, messages.ERROR)


admin.site.unregister(OutstandingToken)
admin.site.register(OutstandingToken, CustomOutstandingTokenAdmin)
