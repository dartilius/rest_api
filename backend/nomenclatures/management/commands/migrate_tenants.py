from nomenclatures.models import Nomenclature, NomenclatureTenant

def migrate_tenants_to_through_table(batch_size=500):
    total = Nomenclature.objects.count()
    for start in range(0, total, batch_size):
        batch = Nomenclature.objects.all()[start:start+batch_size]
        for n in batch:
            for tenant in n.tenants.all():
                # Проверяем, чтобы не дублировать
                if not NomenclatureTenant.objects.filter(
                    nomenclature=n,
                    tenant=tenant
                ).exists():
                    NomenclatureTenant.objects.create(
                        nomenclature=n,
                        tenant=tenant,
                        floor=""  # пока пустой, потом можно заполнить
                    )
        print(f"Migrated batch {start}-{start+batch_size}")