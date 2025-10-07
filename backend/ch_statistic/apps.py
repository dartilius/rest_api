from django.apps import AppConfig


class ChStatisticConfig(AppConfig):
    """
    Конфигурация приложения статистики.
    
    Attributes:
        default_auto_field (str): Тип поля для автоматических первичных ключей
        name (str): Имя приложения
        verbose_name (str): Человекочитаемое имя приложения
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ch_statistic'
    verbose_name = 'Статистика'
