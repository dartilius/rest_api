"""
Management-команда для генерации и устранения дубликатов old_catalog_slug.

Использование:
    python manage.py generate_catalog_slugs [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from nomenclatures.models import Nomenclature


class Command(BaseCommand):
    help = (
        'Генерирует пустые old_catalog_slug и устраняет дубликаты '
        'суффиксами _2, _3 и т.д.'
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать результат без записи в БД',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        qs = Nomenclature.objects.filter(
            Q(old_catalog_slug='') | Q(old_catalog_slug__isnull=True)
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
        for nom in qs:
            slug = nom.generate_old_catalog_slug()
            if not slug:
                self.stdout.write(self.style.WARNING(
                    f'  [SKIP] {nom.pk} ({nom.name}) — не удалось сгенерировать slug'
                ))
                continue

            slug = nom.make_old_catalog_slug_unique(slug)

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

        duplicate_slugs = (
            Nomenclature.objects.exclude(old_catalog_slug='')
            .exclude(old_catalog_slug__isnull=True)
            .values('old_catalog_slug')
            .annotate(count=Count('pk'))
            .filter(count__gt=1)
            .order_by('old_catalog_slug')
        )

        duplicate_groups = 0
        duplicate_records = 0
        for duplicate in duplicate_slugs:
            slug = duplicate['old_catalog_slug']
            records = list(
                Nomenclature.objects.filter(old_catalog_slug=slug).order_by(
                    'created', 'pk'
                )
            )
            duplicate_groups += 1
            duplicate_records += len(records) - 1
            self.stdout.write(
                f'Дубликат {slug!r}: сохраняем у {records[0].pk}'
            )

            for number, nom in enumerate(records[1:], start=2):
                suffix = f'_{number}'
                candidate = f'{slug[:512 - len(suffix)]}{suffix}'
                while Nomenclature.objects.exclude(pk=nom.pk).filter(
                    old_catalog_slug=candidate
                ).exists():
                    number += 1
                    suffix = f'_{number}'
                    candidate = f'{slug[:512 - len(suffix)]}{suffix}'

                self.stdout.write(f'  {nom.pk}: {candidate}')
                if not dry_run:
                    Nomenclature.objects.filter(pk=nom.pk).update(
                        old_catalog_slug=candidate
                    )

        if duplicate_groups:
            message = (
                f'Групп дубликатов: {duplicate_groups}; '
                f'переименовано slug: {duplicate_records}'
            )
            style = self.style.WARNING if dry_run else self.style.SUCCESS
            self.stdout.write(style(message))
