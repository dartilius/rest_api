import api.base_objects
import django.db.models.deletion
import django.db.models.manager
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('corporate_broadcast', '0001_initial'),
        ('files', '0004_alter_file_subtype_alter_tag_name'),
        ('nomenclatures', '0012_nomenclature_broadcast'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.RunSQL("SET LOCAL lock_timeout = '2s'", reverse_sql=migrations.RunSQL.noop),
        migrations.CreateModel(
            name='TypesOfPlaceBroadcast',
            fields=[
                ('id', api.base_objects.UUIDPKField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Уникальный идентификатор')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Актуальность')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('title', models.CharField(max_length=250, verbose_name='Название формата')),
                ('format_type', models.CharField(choices=[('audio', 'Аудиовещание'), ('screens', 'Вещание на экранах'), ('audio-screens', 'Аудио + экраны'), ('video-menu', 'Видеоменю'), ('multimedia', 'Мультимедийное вещание'), ('corporate-network', 'Корпоративная сеть')], max_length=32, verbose_name='Тип формата')),
                ('description', models.TextField(blank=True, max_length=5000, verbose_name='Описание')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='Создатель')),
                ('type_of_place', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='type_of_place', to='nomenclatures.typeofplace', verbose_name='Тип места размещения')),
            ],
            options={
                'verbose_name': 'Формат размещения',
                'verbose_name_plural': 'Форматы размещения',
                'db_table': 'types_of_place_broadcast',
            },
            managers=[
                ('active', django.db.models.manager.Manager()),
            ],
        ),
        migrations.CreateModel(
            name='BroadcastLanding',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=250, verbose_name='Заголовок')),
                ('description', models.TextField(blank=True, max_length=5000, verbose_name='Описание')),
                ('demo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='broadcast_landing_demo', to='corporate_broadcast.broadcastdemo', verbose_name='Демо вещания')),
                ('logo_brands', models.ManyToManyField(blank=True, related_name='broadcast_landing_logos', to='files.file', verbose_name='Логотипы брендов')),
                ('format_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='broadcast_landing_format_type', to='corporate_broadcast.typesofplacebroadcast', verbose_name='Тип формата')),
            ],
            options={
                'verbose_name': 'Лендинг корп вещания',
                'verbose_name_plural': 'Лендинги корп вещания',
                'db_table': 'broadcast_landing',
            },
        ),
        migrations.CreateModel(
            name='TypeOfFormats',
            fields=[
                ('id', api.base_objects.UUIDPKField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='Уникальный идентификатор')),
                ('name', models.CharField(max_length=255, verbose_name='Название')),
                ('is_active', models.BooleanField(default=True, verbose_name='Актуальность')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('format_type', models.CharField(choices=[('audio', 'Аудиовещание'), ('screens', 'Вещание на экранах'), ('audio-screens', 'Аудио + экраны'), ('video-menu', 'Видеоменю'), ('multimedia', 'Мультимедийное вещание'), ('corporate-network', 'Корпоративная сеть')], max_length=32, verbose_name='Тип формата')),
                ('description', models.TextField(blank=True, max_length=5000, verbose_name='Описание')),
                ('demo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='type_of_formats_demo', to='corporate_broadcast.broadcastdemo', verbose_name='Демо вещания')),
                ('owner', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='%(class)ss', to=settings.AUTH_USER_MODEL, verbose_name='Создатель')),
            ],
            options={
                'verbose_name': 'Тип формата',
                'verbose_name_plural': 'Типы форматов',
                'db_table': 'type_of_formats',
                'constraints': [models.UniqueConstraint(fields=('format_type',), name='type_of_formats_unique')],
            },
            managers=[
                ('active', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AddConstraint(
            model_name='typesofplacebroadcast',
            constraint=models.UniqueConstraint(fields=('type_of_place', 'format_type'), name='types_of_place_broadcast_unique'),
        ),
        migrations.RunSQL(migrations.RunSQL.noop, reverse_sql="SET LOCAL lock_timeout = '2s'"),
    ]
