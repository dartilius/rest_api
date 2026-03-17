# nomenclatures/management/commands/migrate_tenants.py
from django.core.management.base import BaseCommand
from nomenclatures.models import Nomenclature, NomenclatureTenant

class Command(BaseCommand):
    help = "Перенос всех арендаторов в промежуточную таблицу NomenclatureTenant"

    def handle(self, *args, **options):
        batch_size = 500
        total = Nomenclature.objects.count()
        self.stdout.write(f"Total nomenclatures: {total}")

        for start in range(0, total, batch_size):
            batch = Nomenclature.objects.all()[start:start+batch_size]
            for n in batch:
                for tenant in n.tenants.all():
                    if not NomenclatureTenant.objects.filter(
                        nomenclature=n,
                        tenant=tenant
                    ).exists():
                        NomenclatureTenant.objects.create(
                            nomenclature=n,
                            tenant=tenant,
                            floor=""  # пока пустой
                        )
            self.stdout.write(f"Migrated batch {start}-{start+batch_size}")

        self.stdout.write(self.style.SUCCESS("Migration completed!"))