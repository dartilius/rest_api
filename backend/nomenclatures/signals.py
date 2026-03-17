from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver

from counterparties.models import Counterparty
from nomenclatures.models import Nomenclature
from nomenclatures.tasks import update_all_search_vectors

@receiver(post_save, sender=Nomenclature)
def update_search_vector_signal(sender, instance, **kwargs):
    update_all_search_vectors.delay(batch_size=1)

@receiver(pre_save, sender=Nomenclature)
def nomenclature_store_old_legal_entity(sender, instance, **kwargs):
    """
    Сохраняем старое значение legalEntity, чтобы понять,
    кого нужно выключить после save.
    """
    if not instance.pk:
        instance._old_legal_entity_id = None
        return

    instance._old_legal_entity_id = (
        sender.objects
        .filter(pk=instance.pk)
        .values_list("legalEntity_id", flat=True)
        .first()
    )


@receiver(post_save, sender=Nomenclature)
def nomenclature_set_broadcast(sender, instance, **kwargs):

    if instance.legalEntity_id:
        Counterparty.objects.filter(
            pk=instance.legalEntity_id,
            broadcast=False
        ).update(broadcast=True)

    old_id = getattr(instance, "_old_legal_entity_id", None)

    if old_id is None and instance.pk:
        old_id = (
            sender.objects
            .filter(pk=instance.pk)
            .values_list("legalEntity_id", flat=True)
            .first()
        )

    if old_id and old_id != instance.legalEntity_id:
        if not Nomenclature.objects.filter(legalEntity_id=old_id).exists():
            Counterparty.objects.filter(pk=old_id).update(broadcast=False)



@receiver(post_delete, sender=Nomenclature)
def nomenclature_unset_broadcast_on_delete(sender, instance, **kwargs):
    """
    Если номенклатуру удалили — возможно,
    нужно выключить broadcast.
    """
    if not instance.legalEntity_id:
        return

    still_used = Nomenclature.objects.filter(
        legalEntity_id=instance.legalEntity_id
    ).exists()

    if not still_used:
        Counterparty.objects.filter(
            pk=instance.legalEntity_id,
            broadcast=True
        ).update(broadcast=False)
