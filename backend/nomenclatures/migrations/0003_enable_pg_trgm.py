# nomenclatures/migrations/0003_enable_pg_trgm.py
from django.db import migrations

def create_pg_trgm(apps, schema_editor):
    """Включаем расширение pg_trgm (если оно ещё не включено)."""
    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

def drop_pg_trgm(apps, schema_editor):
    """Отключаем расширение при откате миграции (опционально)."""
    schema_editor.execute("DROP EXTENSION IF EXISTS pg_trgm;")

class Migration(migrations.Migration):

    dependencies = [
        ("nomenclatures", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(create_pg_trgm, reverse_code=drop_pg_trgm),
    ]
