from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'placement_order'
    verbose_name = 'Заказ на размещение'
