import os
from django.core.management.base import BaseCommand, CommandError

from services.api_1c_client import api_1c


class Command(BaseCommand):
    help = "Получить и сохранить access/refresh JWT сервисного пользователя 1С."

    def handle(self, *args, **options):
        password = os.getenv("SERVICE_1C_PASSWORD")
        if not password:
            raise CommandError("SERVICE_1C_PASSWORD не задан")
        ok = api_1c.authenticate(password)
        if not ok:
            raise CommandError("Авторизация в 1С не удалась")
        self.stdout.write("OK")
