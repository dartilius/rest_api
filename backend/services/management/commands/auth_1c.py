import os
from django.core.management.base import BaseCommand

from services.api_1c_client import api_1c


class Command(BaseCommand):
    def handle(self, *args, **options):
        password = os.getenv("SERVICE_1C_PASSWORD")
        ok = api_1c.authenticate(password)
        self.stdout.write("OK" if ok else "FAILED")