from django.contrib import admin, messages
from django.utils.translation import ngettext
from rest_framework_simplejwt.token_blacklist.admin import OutstandingTokenAdmin
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken


class CustomOutstandingTokenAdmin(OutstandingTokenAdmin):
    """
    Кастомный администратор для OutstandingToken.
    
    Добавляет возможность массового удаления токенов через админ-панель
    с обработкой ошибок и пользовательскими сообщениями.
    """
    
    actions = ['delete_selected_tokens']

    def has_delete_permission(self, *args, **kwargs):
        """Разрешает право на удаление токенов."""
        return True

    @admin.action(description='Удалить выбранные токены')
    def delete_selected_tokens(self, request, queryset):
        """
        Массовое удаление выбранных токенов.
        
        Args:
            request: HttpRequest объект
            queryset: QuerySet выбранных токенов для удаления
            
        Returns:
            None, но показывает сообщение о результате операции
        """
        try:
            # Используем bulk delete для оптимизации
            count, _ = queryset.delete()
            
            self.message_user(
                request,
                ngettext(
                    f'{count} токен успешно удалён',
                    f'{count} токенов успешно удалено',
                    count,
                ),
                messages.SUCCESS
            )
        except Exception as e:
            # Логируем ошибку для отладки
            self.message_user(
                request, 
                f'Ошибка при удалении токенов: {str(e)}', 
                messages.ERROR
            )


# Регистрируем кастомный администратор
admin.site.unregister(OutstandingToken)
admin.site.register(OutstandingToken, CustomOutstandingTokenAdmin)
