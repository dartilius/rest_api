import api.base_objects
import django.db.models.deletion
import django.db.models.manager
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [('files', '0004_alter_file_subtype_alter_tag_name')]
    operations = [
        migrations.CreateModel(
            name='BroadcastDemo',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=250, verbose_name='Заголовок')),
                ('format', models.CharField(choices=[('audio', 'Аудиовещание'), ('screens', 'Вещание на экранах'), ('audio-screens', 'Аудио + экраны'), ('video-menu', 'Видеоменю'), ('multimedia', 'Мультимедийное вещание'), ('corporate-network', 'Корпоративная сеть')], max_length=32, verbose_name='Формат / сценарий')),
                ('description', models.TextField(blank=True, max_length=5000, verbose_name='Описание')),
                ('transcript', models.TextField(blank=True, max_length=20000, verbose_name='Расшифровка')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('is_published', models.BooleanField(default=False, verbose_name='Опубликовано')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Демо вещания',
                'verbose_name_plural': 'Демо вещания',
                'ordering': ('sort_order', 'created', 'id'),
                'indexes': [models.Index(fields=['is_published', 'format', 'sort_order'], name='broadcast_demo_public_idx')],
            },
        ),
        migrations.CreateModel(
            name='BroadcastDemoAsset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('audio', 'audio'), ('video', 'video'), ('image', 'image'), ('poster', 'poster')], max_length=10, verbose_name='Роль')),
                ('caption', models.CharField(blank=True, max_length=250, verbose_name='Подпись')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('demo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='corporate_broadcast.broadcastdemo')),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='broadcast_demo_assets', to='files.file')),
            ],
            options={
                'verbose_name': 'Материал демо',
                'verbose_name_plural': 'Материалы демо',
                'ordering': ('sort_order', 'id'),
                'constraints': [models.UniqueConstraint(fields=('demo', 'file', 'role'), name='broadcast_demo_asset_unique')],
            },
        ),
    ]
