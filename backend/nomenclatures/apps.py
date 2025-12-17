from django.apps import AppConfig


class NomenclaturesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nomenclatures'
    verbose_name = 'Номенклатуры'

    def ready(self):
        import nomenclatures.signals
