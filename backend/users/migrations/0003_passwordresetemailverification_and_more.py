"""Join the applied production verification migrations without duplicate DDL."""

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("users", "0004_passwordresetemailverification")]

    operations = []
