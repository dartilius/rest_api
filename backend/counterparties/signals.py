from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Counterparty
from users.models import CustomUser


@receiver(m2m_changed, sender=Counterparty.contact_persons.through)
def update_user_role_on_link(sender, instance, action, pk_set, **kwargs):
    """
    Автоматическая установка роли пользователя при добавлении/удалении
    к/от контрагента.
    """
    if action == "post_add":
        for user_id in pk_set:
            user = CustomUser.objects.get(pk=user_id)
            # Если broadcast у контрагента True → роль broadcast
            if instance.broadcast:
                user.role = "broadcast"
            else:
                # Иначе, можно ставить ad или contact_person
                user.role = "ad"  # или "contact_person", если есть такая роль
            user.save(update_fields=["role"])

    if action == "post_remove":
        for user_id in pk_set:
            user = CustomUser.objects.get(pk=user_id)
            # Если пользователь больше нигде не контактное лицо
            if user.counterparties.count() == 0:
                user.role = "ordinary"
                user.save(update_fields=["role"])
