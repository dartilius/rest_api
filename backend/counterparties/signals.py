from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver

from .models import Counterparty
from users.models import CustomUser


def sync_user_role(user_id):
    """Set a contact person's role from all of their counterparties."""
    counterparties = Counterparty.objects.filter(contact_persons__pk=user_id)

    if counterparties.filter(broadcast=True).exists():
        role = "broadcast"
    elif counterparties.exists():
        role = "ad"
    else:
        role = "ordinary"

    CustomUser.objects.filter(pk=user_id).exclude(role=role).update(role=role)


@receiver(m2m_changed, sender=Counterparty.contact_persons.through)
def update_user_role_on_link(sender, instance, action, pk_set, **kwargs):
    """Synchronize roles after contact persons are added or removed."""
    if action in {"post_add", "post_remove"}:
        for user_id in pk_set:
            sync_user_role(user_id)


@receiver(post_save, sender=Counterparty)
def update_contact_person_roles_on_counterparty_save(sender, instance, **kwargs):
    """Resync linked users when a counterparty, including `broadcast`, changes."""
    user_ids = instance.contact_persons.values_list("pk", flat=True)

    if instance.broadcast:
        CustomUser.objects.filter(pk__in=user_ids).exclude(
            role="broadcast"
        ).update(role="broadcast")
        return

    for user_id in user_ids:
        sync_user_role(user_id)
