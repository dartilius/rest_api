from datetime import timedelta

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.utils import timezone

from users.models import CustomUser, PersonalDataConsent
from feedback.models import Feedback


@receiver(pre_delete, sender=CustomUser)
@receiver(pre_delete, sender=Feedback)
def expire_subject_evidence(sender, instance, **kwargs):
    field = 'user' if sender is CustomUser else 'feedback'
    PersonalDataConsent.objects.filter(**{field: instance}).update(
        evidence_delete_after=timezone.now() + timedelta(days=30),
    )
