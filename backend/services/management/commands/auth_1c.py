# feedback/management/commands/auth_1c.py

import os
from django.core.management.base import BaseCommand

from services.api_1c_client import get_service_user, APIService


class Command(BaseCommand):
    help = 'Первичная авторизация сервисного аккаунта в 1С'

    def handle(self, *args, **options):
        password = os.getenv("SERVICE_1C_PASSWORD")
        if not password:
            self.stderr.write("❌ Переменная окружения SERVICE_1C_PASSWORD не задана")
            return

        try:
            user = get_service_user()
            svc = APIService(user=user)
            ok = svc.authenticate(password=password)
        except Exception as e:
            self.stderr.write(f"❌ Ошибка: {e}")
            return

        if ok:
            self.stdout.write(self.style.SUCCESS(f"✅ Авторизация успешна ({user.email})"))
        else:
            self.stderr.write("❌ Авторизация не удалась")