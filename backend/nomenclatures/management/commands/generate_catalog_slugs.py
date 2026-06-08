"""
Management-команда для генерации old_catalog_slug у всех номенклатур.

Использование:
    python manage.py generate_catalog_slugs [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db import models
from nomenclatures.models import Nomenclature


class Command(BaseCommand):
    help = 'Генерирует old_catalog_slug для всех номенклатур, у которых он пуст'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать результат без записи в БД',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        qs = Nomenclature.objects.filter(
            models.Q(old_catalog_slug='') | models.Q(old_catalog_slug__isnull=True)
        ).select_related(
            'brand',
            'typeOfPlace',
            'address__address',
            'address__address__city',
            'address__address__street',
            'address__address__region',
            'address__address__house',
        )

        total = qs.count()
        self.stdout.write(f'Найдено {total} номенклатур с пустым slug')

        updated = 0
        collisions = {}

        for nom in qs:
            slug = nom.generate_old_catalog_slug()
            if not slug:
                self.stdout.write(self.style.WARNING(
                    f'  [SKIP] {nom.pk} ({nom.name}) — не удалось сгенерировать slug'
                ))
                continue

            # Проверяем коллизии
            existing = Nomenclature.objects.filter(
                old_catalog_slug=slug
            ).exclude(pk=nom.pk).first()

            if existing:
                slug = f'{slug[:500]}-{str(nom.pk)[:8]}'
                if slug not in collisions:
                    collisions[slug] = []
                collisions[slug].append(nom.pk)

            if not dry_run:
                nom.__class__.objects.filter(pk=nom.pk).update(old_catalog_slug=slug)

            updated += 1
            self.stdout.write(f'  {nom.pk}: {slug}')

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\n[DRY RUN] Обновлено {updated} из {total}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'\nОбновлено {updated} из {total}'
            ))

        if collisions:
            self.stdout.write(self.style.WARNING(
                f'Коллизий разрешено: {len(collisions)}'
            ))
