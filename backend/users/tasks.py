import logging
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from feedback.models import Feedback
from users.models import (
    PersonalDataConsent, PrivacyRequest, RegistrationEmailVerification,
    PasswordResetEmailVerification,
)
from users.privacy_services import erase_feedback

logger = logging.getLogger(__name__)


@shared_task
def cleanup_personal_data(dry_run=True, batch_size=500):
    """One bounded batch per category; repeat until empty for a backlog."""
    if type(batch_size) is not int or not 1 <= batch_size <= 5000:
        raise ValueError('batch_size must be between 1 and 5000')
    if type(dry_run) is not bool:
        raise ValueError('dry_run must be boolean')
    now = timezone.now()
    result = {'dry_run': dry_run}
    queries = {
        'feedback': Feedback.objects.filter(
            status='closed', contract_status='none',
            closed_at__lte=now - timedelta(days=30), delete_after__lte=now,
        ).filter(Q(lawful_retention_until__isnull=True) | Q(lawful_retention_until__lte=now)),
        'registrations': RegistrationEmailVerification.objects.filter(
            last_consent_at__lte=now - timedelta(days=30), expires_at__lte=now,
        ),
        'reset_codes': PasswordResetEmailVerification.objects.filter(expires_at__lte=now),
        'evidence': PersonalDataConsent.objects.filter(evidence_delete_after__lte=now),
        'requests': PrivacyRequest.objects.filter(
            completed_at__isnull=False, delete_after__lte=now,
        ),
    }
    for name, query in queries.items():
        with transaction.atomic():
            records = list(query.select_for_update().order_by('pk')[:batch_size])
            result[name] = len(records)
            if not dry_run:
                for record in records:
                    if name == 'feedback':
                        erase_feedback(record)
                    else:
                        record.delete()
    logger.info('Privacy cleanup counts: %s', result)
    return result
