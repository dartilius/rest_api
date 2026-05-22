from django.core.management.base import BaseCommand
from nomenclatures.models import Nomenclature


class Command(BaseCommand):
    help = 'Перестраивает search_vector для всех номенклатур'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Обновить все записи, включая не для веба',
        )

    def handle(self, *args, **options):
        update_all = options.get('all', False)

        if update_all:
            self.stdout.write('Обновляем все номенклатуры...')
            nomenclatures = Nomenclature.objects.all()
        else:
            self.stdout.write('Обновляем только номенклатуры для веба...')
            nomenclatures = Nomenclature.objects.filter(for_web=True)

        nomenclatures = nomenclatures.select_related(
            'brand',
            'legalEntity',
            'typeOfPlace',
            'responsible_radio',
            'responsible_ad',
            'responsible_technic',
            'responsible_technic_on_address',
            'responsible_placement_marketing',
        ).prefetch_related(
            'nomenclature_tenants__tenant',
            'nomenclature_tenants__brand',
        )

        total = nomenclatures.count()

        if total == 0:
            self.stdout.write(self.style.WARNING('Нет номенклатур для обновления'))
            return

        self.stdout.write(f'Найдено номенклатур: {total}')

        updated = 0
        cleared = 0

        for nomenclature in nomenclatures.iterator(chunk_size=500):
            nomenclature.update_search_vector()
            updated += 1

            if updated % 100 == 0:
                self.stdout.write(f'Обновлено: {updated}/{total}')

        # Очищаем search_vector у номенклатур не для веба
        if not update_all:
            cleared = Nomenclature.objects.filter(
                for_web=False
            ).exclude(
                search_vector=''
            ).update(search_vector='')

            if cleared > 0:
                self.stdout.write(f'Очищено search_vector: {cleared}')

        self.stdout.write(self.style.SUCCESS(
            f'Готово! Обновлено записей: {updated}, очищено: {cleared}'
        ))