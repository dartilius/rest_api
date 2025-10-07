from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ApiConfig(AppConfig):
    """
    Конфигурация приложения API.
    
    Настройки по умолчанию и инициализация приложения.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    verbose_name = _('API приложение')

    def ready(self):
        """
        Инициализация приложения.
        
        Здесь можно подключить сигналы и выполнить
        другие операции инициализации.
        """
        # Импортируем сигналы для их регистрации
        try:
            import api.signals  # noqa
        except ImportError:
            pass
