"""Authorized staff workflow and bounded erasure operations."""
from datetime import timedelta

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from feedback.models import Feedback
from users.models import PrivacyErasure


def require_privacy_staff(user):
    if not (user.is_active and user.is_staff and user.has_perm('users.manage_privacy')):
        raise PermissionDenied


@transaction.atomic
def erase_feedback(feedback):
    # Caller must lock the row or have a verified staff request, never a public email.
    if feedback.contract_status != 'none':
        raise ValueError('Contract classification is required')
    if feedback.lawful_retention_until and feedback.lawful_retention_until > timezone.now():
        raise ValueError('An active lawful retention basis prevents erasure')
    PrivacyErasure.objects.get_or_create(
        subject_type='feedback', subject_id=str(feedback.pk),
    )
    feedback.delete()


@transaction.atomic
def resolve_privacy_request(item, user):
    require_privacy_staff(user)
    item.full_clean()
    if item.pk:
        previous = type(item).objects.select_for_update().get(pk=item.pk)
        if previous.completed_at:
            raise ValueError('Completed requests are immutable')
    item.handled_by = user
    if item.status != 'pending':
        item.completed_at = timezone.now()
        item.delete_after = item.completed_at + timedelta(days=30)
        if item.status == 'retained' and item.feedback_id:
            Feedback.objects.filter(pk=item.feedback_id).update(
                lawful_retention_until=item.retention_until, lawful_retention_basis=item.lawful_basis,
            )
        consent = item.consent
        if item.kind == 'withdraw' and consent:
            consent.revoked_at = item.completed_at
            consent.save(update_fields=['revoked_at'])
            if consent.feedback_id:
                Feedback.objects.filter(pk=consent.feedback_id).update(processing_blocked=True)
        if item.kind == 'delete' and item.status == 'completed' and item.feedback_id:
            feedback = Feedback.objects.select_for_update().get(pk=item.feedback_id)
            erase_feedback(feedback)
            item.feedback = None
        # Account deletion/correction are executed by staff after checking other lawful bases.
        # Completing this record is their attestation, never an automatic account cascade.
    item.save()
