import clickhouse_backend.models
from django.conf import settings
import django.db.models.manager
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ch_statistic', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BackupImageStat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', clickhouse_backend.models.DateTimeField(auto_now_add=True, verbose_name='Запись создана')),
                ('played', clickhouse_backend.models.DateTimeField(verbose_name='Когда было проиграно')),
                ('file', clickhouse_backend.models.StringField(max_length=36, verbose_name='Идентификатор файла')),
                ('client',
                 clickhouse_backend.models.StringField(max_length=36, verbose_name='Идентификатор номенклатуры')),
                ('length', clickhouse_backend.models.UInt16Field(verbose_name='Хронометраж')),
            ],
            options={
                'verbose_name': 'Бэкап статистики изображений',
                'verbose_name_plural': 'Бэкапы статистики изображений',
                'db_table': 'image_stat_backup',
                'ordering': ['-played'],
            },
            managers=[
                ('objects', django.db.models.manager.Manager()),
                ('_overwrite_base_manager', django.db.models.manager.Manager()),
            ],
        ),
    ]
