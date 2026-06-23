"""
Команда для перестройки search_vector для всех номенклатур.

ИСПОЛЬЗОВАНИЕ:
───────────────────────────────────────────────────────────────────────────────
python manage.py rebuild_search_vectors                    # Только for_web=True
python manage.py rebuild_search_vectors --all              # Все записи
python manage.py rebuild_search_vectors --batch-size=1000  # Пакетный размер

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Обновление только for_web=True (экономия ресурсов)
2. Пакетная обработка (batch_size=500 по умолчанию)
3. Транзакции по пакетам для минимизации блокировок
4. Использование iterator для экономии памяти
5. Очистка search_vector для не for_web записей
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from nomenclatures.models import Nomenclature


class Command(BaseCommand):
    """
    Команда для перестройки search_vector для всех номенклатур.

    Аргументы:
        --all: Обновить все записи, включая не для веба
        --batch-size: Размер пакета для обновления (по умолчанию 500)
    """

    help = 'Перестраивает search_vector для всех номенклатур'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Обновить все записи, включая не для веба',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Размер пакета для обновления',
        )

    def handle(self, *args, **options):
        update_all = options.get('all', False)
        batch_size = options.get('batch_size', 500)

        if update_all:
            self.stdout.write('Обновляем все номенклатуры...')
            nomenclatures = Nomenclature.objects.all()
        else:
            self.stdout.write('Обновляем только номенклатуры для веба...')
            nomenclatures = Nomenclature.objects.filter(for_web=True)

        total = nomenclatures.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('Нет номенклатур для обновления'))
            return

        self.stdout.write(f'Найдено номенклатур: {total}')

        updated = 0
        batch = []

        for nomenclature in nomenclatures.iterator(chunk_size=batch_size):
            batch.append(nomenclature)

            if len(batch) >= batch_size:
                with transaction.atomic():
                    for item in batch:
                        item.update_search_vector(force=True)
                        updated += 1
                batch = []
                self.stdout.write(f'Обновлено: {updated}/{total}')

        if batch:
            with transaction.atomic():
                for item in batch:
                    item.update_search_vector(force=True)
                    updated += 1

        if not update_all:
            cleared = Nomenclature.objects.filter(
                for_web=False
            ).exclude(search_vector='').update(search_vector='')

            if cleared > 0:
                self.stdout.write(f'Очищено search_vector: {cleared}')

        self.stdout.write(self.style.SUCCESS(
            f'Готово! Обновлено записей: {updated}, очищено: {cleared}'
        ))

# from django.core.management.base import BaseCommand
# from nomenclatures.models import Nomenclature


# class Command(BaseCommand):
#     help = 'Перестраивает search_vector для всех номенклатур'

#     def add_arguments(self, parser):
#         parser.add_argument(
#             '--all',
#             action='store_true',
#             help='Обновить все записи, включая не для веба',
#         )

#     def handle(self, *args, **options):
#         update_all = options.get('all', False)

#         if update_all:
#             self.stdout.write('Обновляем все номенклатуры...')
#             nomenclatures = Nomenclature.objects.all()
#         else:
#             self.stdout.write('Обновляем только номенклатуры для веба...')
#             nomenclatures = Nomenclature.objects.filter(for_web=True)

#         nomenclatures = nomenclatures.select_related(
#             'brand',
#             'legalEntity',
#             'typeOfPlace',
#             'responsible_radio',
#             'responsible_ad',
#             'responsible_technic',
#             'responsible_technic_on_address',
#             'responsible_placement_marketing',
#         ).prefetch_related(
#             'nomenclature_tenants__tenant',
#             'nomenclature_tenants__brand',
#         )

#         total = nomenclatures.count()

#         if total == 0:
#             self.stdout.write(self.style.WARNING('Нет номенклатур для обновления'))
#             return

#         self.stdout.write(f'Найдено номенклатур: {total}')

#         updated = 0
#         cleared = 0

#         for nomenclature in nomenclatures.iterator(chunk_size=500):
#             nomenclature.update_search_vector()
#             updated += 1

#             if updated % 100 == 0:
#                 self.stdout.write(f'Обновлено: {updated}/{total}')

#         # Очищаем search_vector у номенклатур не для веба
#         if not update_all:
#             cleared = Nomenclature.objects.filter(
#                 for_web=False
#             ).exclude(
#                 search_vector=''
#             ).update(search_vector='')

#             if cleared > 0:
#                 self.stdout.write(f'Очищено search_vector: {cleared}')

#         self.stdout.write(self.style.SUCCESS(
#             f'Готово! Обновлено записей: {updated}, очищено: {cleared}'
#         ))