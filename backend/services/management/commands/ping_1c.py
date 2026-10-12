import requests
from django.core.management.base import BaseCommand, CommandError

from services.api_1c_client import api_1c


class Command(BaseCommand):
    help = "Проверить доступность сервиса 1С через /ping/open без авторизации."

    def handle(self, *args, **options):
        try:
            response = api_1c.ping()
            response.raise_for_status()
        except requests.RequestException as e:
            raise CommandError(f"Сервис 1С недоступен: {type(e).__name__}") from e
        self.stdout.write(f"OK (HTTP {response.status_code})")
