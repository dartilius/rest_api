"""Consent validation runs before serializers can query personal data."""
import hashlib
from pathlib import Path
from collections.abc import Mapping

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field


DOCUMENT_VERSION = '2026-10-14'
# Populated from the archived frontend document, never from the request.
DOCUMENT_SHA256 = 'e4780dbfd46934a0d6dce8f9ea0559220a58ca62efc61ba98b847526c1089239'


def validate_consent(data, purpose):
    if not isinstance(data, Mapping):
        raise ValidationError({'detail': 'Передайте объект с полями формы и согласия.'})
    if data.get('consent') is not True:
        raise ValidationError({'detail': 'Подтвердите согласие на обработку данных.'})
    if data.get('consent_version') != DOCUMENT_VERSION:
        raise ValidationError({'detail': 'Неизвестная редакция согласия.'})
    receipt = data.get('personal_data_consent')
    if not isinstance(receipt, dict) or not all((
        receipt.get('accepted') is True,
        receipt.get('purpose') == purpose,
        receipt.get('version') == DOCUMENT_VERSION,
    )):
        raise ValidationError({'detail': 'Сведения о согласии не согласованы с формой.'})
    # accepted_at is deliberately ignored; identity, FK and source are never copied.
    document = Path(__file__).parent / 'consent_documents' / f'{DOCUMENT_VERSION}.txt'
    try:
        checksum = hashlib.sha256(document.read_bytes()).hexdigest()
    except OSError:
        raise APIException('Документ согласия временно недоступен.') from None
    if checksum != DOCUMENT_SHA256:
        raise APIException('Документ согласия временно недоступен.')
    return DOCUMENT_VERSION


@transaction.atomic
def registration_consent(email):
    from users.models import PersonalDataConsent, RegistrationEmailVerification

    verification, _ = RegistrationEmailVerification.objects.select_for_update().get_or_create(
        email=email,
        defaults={'code': '', 'expires_at': timezone.now()},
    )
    consent, _ = PersonalDataConsent.objects.get_or_create(
        registration=verification, document_version=DOCUMENT_VERSION,
        purpose='registration', revoked_at__isnull=True,
        defaults={'document_sha256': DOCUMENT_SHA256, 'source': 'django-public-api',
                  'subject_reference': f'registration:{verification.pk}'},
    )
    verification.last_consent_at = timezone.now()
    verification.save(update_fields=['last_consent_at'])
    return verification, consent


class ConsentReceiptSerializer(serializers.Serializer):
    """Public receipt shape; accepted_at is advisory and never stored as proof."""

    accepted = serializers.BooleanField()
    purpose = serializers.ChoiceField(choices=['feedback', 'registration'])
    version = serializers.ChoiceField(choices=[DOCUMENT_VERSION])
    accepted_at = serializers.DateTimeField(required=False)


@extend_schema_field(ConsentReceiptSerializer)
class ConsentReceiptField(serializers.JSONField):
    """Expose the receipt structure in OpenAPI while ignoring client identity."""


class ConsentFieldsSerializer(serializers.Serializer):
    """Consent fields shared only by public registration operations."""
    consent = serializers.BooleanField(write_only=True)
    consent_version = serializers.ChoiceField(choices=[DOCUMENT_VERSION], write_only=True)
    personal_data_consent = ConsentReceiptField(write_only=True)

    def to_internal_value(self, data):
        validate_consent(data, 'registration')
        return super().to_internal_value(data)
