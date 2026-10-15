from datetime import timedelta
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth.models import Permission
from django.core import mail
from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory

from feedback.models import Feedback
from feedback.tasks import deliver_feedback_notification
from placement_order.models import PlacementOrder
from users.models import (
    CustomUser, PersonalDataConsent, PrivacyRequest, PrivacyErasure,
    RegistrationEmailVerification,
)
from users.privacy import DOCUMENT_VERSION, DOCUMENT_SHA256
from users.privacy_services import resolve_privacy_request
from users.tasks import cleanup_personal_data


def receipt(purpose):
    return {
        'consent': True, 'consent_version': DOCUMENT_VERSION,
        'personal_data_consent': {
            'accepted': True, 'purpose': purpose, 'version': DOCUMENT_VERSION,
            'accepted_at': '2000-01-01T00:00:00Z', 'user_id': 'untrusted',
            'source': 'trusted-frontend',
        },
    }


class PrivacyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        cache.clear()

    def post(self, path, data):
        return self.client.post('/api/' + path + '/', data, format='json')

    def feedback(self, **extra):
        return {'name': 'Test User', 'email': 'test@example.test',
                'phone': '+79991234567', 'message': 'Test', **receipt('feedback'), **extra}

    def registration(self, **extra):
        return {'email': 'new@example.test', **receipt('registration'), **extra}

    def user_data(self):
        return self.registration(first_name='Test', last_name='User',
                                 phone_number='+79991234567', password='secret-test')

    def test_invalid_consent_rejected_before_queries_and_side_effects(self):
        changes = [
            {'consent': None}, {'consent': False}, {'consent': 'true'}, {'consent': 1},
            {'consent_version': 'old'}, {'personal_data_consent': None},
            {'personal_data_consent': {'accepted': 'true', 'purpose': 'registration',
                                       'version': DOCUMENT_VERSION}},
        ]
        for path in ('feedback', 'users/check-email', 'users/send-registration-code', 'users/register'):
            for change in changes:
                data = self.feedback() if path == 'feedback' else self.user_data()
                data.update(change)
                with self.subTest(path=path, change=change), self.assertNumQueries(0):
                    response = self.post(path, data)
                self.assertEqual(response.status_code, 400)
                self.assertIn('detail', response.data)
            data = self.feedback() if path == 'feedback' else self.user_data()
            del data['consent']
            self.assertEqual(self.post(path, data).status_code, 400)
        self.assertFalse(Feedback.objects.exists())
        self.assertFalse(PersonalDataConsent.objects.exists())
        self.assertFalse(RegistrationEmailVerification.objects.exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_mismatched_receipt_and_client_lifecycle_fields(self):
        data = self.feedback()
        data['personal_data_consent']['purpose'] = 'registration'
        self.assertEqual(self.post('feedback', data).status_code, 400)
        data = self.feedback(status='closed', contract_status='none', closed_at='2000-01-01')
        response = self.post('feedback', data)
        self.assertEqual(response.status_code, 201)
        obj = Feedback.objects.get()
        self.assertEqual(obj.status, 'active')
        self.assertEqual(obj.contract_status, 'unknown')
        self.assertIsNone(obj.closed_at)

    def test_feedback_atomic_receipt_and_backend_time(self):
        before = timezone.now()
        with patch(
            'feedback.signals.deliver_feedback_notification.delay',
        ) as enqueue, self.captureOnCommitCallbacks(execute=True):
            response = self.post('feedback', self.feedback())
        self.assertEqual(response.status_code, 201)
        consent = PersonalDataConsent.objects.get()
        self.assertEqual(consent.purpose, 'feedback')
        self.assertEqual(consent.document_version, DOCUMENT_VERSION)
        self.assertEqual(consent.document_sha256, DOCUMENT_SHA256)
        self.assertGreaterEqual(consent.accepted_at, before)
        self.assertEqual(consent.accepted_at, consent.feedback.consent_at)
        self.assertEqual(consent.source, 'django-public-api')
        self.assertEqual(enqueue.call_count, 2)
        for call in enqueue.call_args_list:
            self.assertEqual(set(call.kwargs), {'request_id', 'audience'})

    def test_feedback_consent_failure_rolls_back_and_does_not_enqueue(self):
        with patch(
            'feedback.serializers.PersonalDataConsent.objects.create',
            side_effect=IntegrityError('internal-secret'),
        ), patch('feedback.signals.deliver_feedback_notification.delay') as enqueue, \
                self.captureOnCommitCallbacks(execute=True):
            response = self.post('feedback', self.feedback())
        self.assertEqual(response.status_code, 500)
        self.assertNotIn('internal-secret', str(response.data))
        self.assertFalse(Feedback.objects.exists())
        enqueue.assert_not_called()

    def test_email_empty_success_and_existing_status(self):
        for _ in range(3):
            response = self.post('users/check-email', self.registration())
            self.assertEqual(response.status_code, 200)
            response.render()
            self.assertEqual(response.content, b'')
        self.assertEqual(PersonalDataConsent.objects.count(), 1)
        CustomUser.objects.create(email='EXISTING@example.test')
        response = self.post('users/check-email', self.registration(email='existing@example.test'))
        self.assertEqual(response.status_code, 204)

    def verify(self):
        self.assertEqual(self.post('users/send-registration-code', self.registration()).status_code, 200)
        # The mocked local backend is the only place the plaintext OTP exists.
        code = mail.outbox[-1].body.split(': ')[1].split('.')[0]
        response = self.post('users/confirm-registration-code', {
            'email': 'new@example.test', 'code': code,
        })
        self.assertEqual(response.status_code, 200)

    def test_resend_deduplicates_and_register_links_initial_consent(self):
        self.post('users/check-email', self.registration())
        first = PersonalDataConsent.objects.get()
        original_accepted_at = first.accepted_at
        self.verify()
        self.verify()
        self.assertEqual(PersonalDataConsent.objects.count(), 1)
        response = self.post('users/register', self.user_data())
        self.assertEqual(response.status_code, 201, response.data)
        first.refresh_from_db()
        self.assertEqual(str(first.user_id), response.data['id'])
        self.assertEqual(first.accepted_at, original_accepted_at)
        self.assertIsNone(first.registration_id)
        self.assertFalse(RegistrationEmailVerification.objects.exists())
        self.assertTrue(first.user.check_password('secret-test'))
        self.assertNotIn('secret-test', str(response.data))

    def test_registration_requires_unexpired_verification(self):
        self.assertEqual(self.post('users/register', self.user_data()).status_code, 400)
        self.post('users/check-email', self.registration())
        self.assertEqual(self.post('users/register', self.user_data()).status_code, 400)
        self.verify()
        RegistrationEmailVerification.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.post('users/register', self.user_data()).status_code, 400)
        self.assertFalse(CustomUser.objects.exists())

    def test_failed_consent_link_rolls_back_user_and_preserves_verified_code(self):
        self.verify()
        with patch.object(PersonalDataConsent, 'save', side_effect=IntegrityError('secret-db-error')):
            response = self.post('users/register', self.user_data())
        self.assertEqual(response.status_code, 500)
        self.assertFalse(CustomUser.objects.exists())
        self.assertTrue(RegistrationEmailVerification.objects.get().is_verified)
        self.assertNotIn('secret-db-error', str(response.data))

    def test_email_send_never_occurs_if_consent_save_fails(self):
        with patch('users.models.PersonalDataConsent.objects.get_or_create',
                   side_effect=IntegrityError('secret')):
            response = self.post('users/send-registration-code', self.registration())
        self.assertEqual(response.status_code, 500)
        self.assertEqual(len(mail.outbox), 0)
        self.assertFalse(RegistrationEmailVerification.objects.exists())

    def test_existing_user_never_modified_and_djoser_cannot_bypass(self):
        user = CustomUser.objects.create(email='new@example.test', first_name='Original')
        self.assertEqual(self.post('users/send-registration-code', self.registration()).status_code, 400)
        self.assertEqual(self.post('users/register', self.user_data()).status_code, 400)
        user.refresh_from_db()
        self.assertEqual(user.first_name, 'Original')
        response = self.client.post('/auth/users/', self.user_data(), format='json')
        self.assertIn(response.status_code, (401, 403))


class PrivacyCleanupTests(TestCase):
    def make_feedback(self, **extra):
        return Feedback.objects.create(name='PII', email='pii@example.test', **extra)

    def test_boundary_contracts_active_and_idempotency(self):
        now = timezone.now()
        due = self.make_feedback(status='closed', contract_status='none', closed_at=now - timedelta(days=30))
        PersonalDataConsent.objects.create(feedback=due, purpose='feedback',
                                           document_version=DOCUMENT_VERSION, document_sha256=DOCUMENT_SHA256)
        recent = self.make_feedback(status='closed', contract_status='none',
                                    closed_at=now - timedelta(days=30) + timedelta(seconds=1))
        active = self.make_feedback()
        unknown = self.make_feedback(status='closed', closed_at=now - timedelta(days=60))
        contract = self.make_feedback(status='closed', contract_status='contract',
                                      contract_reference='Contract-1', closed_at=now - timedelta(days=60))
        with patch('users.tasks.timezone.now', return_value=now):
            result = cleanup_personal_data(dry_run=True)
            self.assertEqual(result['feedback'], 1)
            self.assertTrue(Feedback.objects.filter(pk=due.pk).exists())
            self.assertEqual(cleanup_personal_data(dry_run=False)['feedback'], 1)
            self.assertEqual(cleanup_personal_data(dry_run=False)['feedback'], 0)
        self.assertEqual(Feedback.objects.count(), 4)
        self.assertTrue(all(Feedback.objects.filter(pk=x.pk).exists() for x in (recent, active, unknown, contract)))
        consent = PersonalDataConsent.objects.get()
        self.assertIsNone(consent.feedback_id)
        self.assertIsNotNone(consent.evidence_delete_after)
        self.assertEqual(PrivacyErasure.objects.count(), 1)
        with patch('users.tasks.timezone.now', return_value=now + timedelta(days=31)):
            self.assertEqual(cleanup_personal_data(dry_run=False)['evidence'], 1)

    def test_placement_order_is_not_a_contract_and_is_not_deleted(self):
        user = CustomUser.objects.create(email='owner@example.test')
        order = PlacementOrder.objects.create(owner=user, duration=1)
        feedback = self.make_feedback(placement_order=order, status='closed', contract_status='none',
                                      closed_at=timezone.now() - timedelta(days=31))
        self.assertEqual(cleanup_personal_data(dry_run=False)['feedback'], 1)
        self.assertFalse(Feedback.objects.filter(pk=feedback.pk).exists())
        self.assertTrue(PlacementOrder.objects.filter(pk=order.pk).exists())

    def test_temp_registration_retention_legacy_and_batch_size(self):
        now = timezone.now()
        for n in range(3):
            verification = RegistrationEmailVerification.objects.create(
                email=f'old{n}@example.test', code='hash', expires_at=now - timedelta(days=31),
                last_consent_at=now - timedelta(days=30),
            )
            PersonalDataConsent.objects.create(registration=verification, purpose='registration',
                                               document_version=DOCUMENT_VERSION)
        RegistrationEmailVerification.objects.create(
            email='legacy@example.test', code='', expires_at=now - timedelta(days=90), last_consent_at=None,
        )
        with patch('users.tasks.timezone.now', return_value=now):
            self.assertEqual(cleanup_personal_data(dry_run=False, batch_size=2)['registrations'], 2)
            self.assertEqual(cleanup_personal_data(dry_run=False, batch_size=2)['registrations'], 1)
        self.assertEqual(RegistrationEmailVerification.objects.count(), 1)
        self.assertFalse(PersonalDataConsent.objects.exists())

    def test_notification_skips_erased_and_blocked_requests(self):
        feedback = self.make_feedback(processing_blocked=True)
        with patch('feedback.tasks._send') as send:
            self.assertEqual(deliver_feedback_notification.run(str(feedback.pk), 'manager'), 'skipped')
            self.assertEqual(deliver_feedback_notification.run('00000000-0000-0000-0000-000000000000', 'manager'), 'skipped')
        send.assert_not_called()

    def test_separate_lawful_basis_prevents_cleanup_until_expiry(self):
        now = timezone.now()
        feedback = self.make_feedback(
            status='closed', contract_status='none', closed_at=now - timedelta(days=60),
            lawful_retention_until=now + timedelta(days=1), lawful_retention_basis='Reviewed basis',
        )
        self.assertEqual(cleanup_personal_data(dry_run=False)['feedback'], 0)
        with patch('users.tasks.timezone.now', return_value=now + timedelta(days=2)):
            self.assertEqual(cleanup_personal_data(dry_run=False)['feedback'], 1)
        self.assertFalse(Feedback.objects.filter(pk=feedback.pk).exists())

    @override_settings(USE_TZ=True)
    def test_aware_business_timezone_uses_the_same_thirty_day_boundary(self):
        from datetime import timezone as datetime_timezone

        now = timezone.now()
        business_zone = datetime_timezone(timedelta(hours=7))
        self.make_feedback(
            status='closed', contract_status='none',
            closed_at=(now - timedelta(days=30)).astimezone(business_zone),
        )
        with patch('users.tasks.timezone.now', return_value=now):
            self.assertEqual(cleanup_personal_data(dry_run=False)['feedback'], 1)


class PrivacyStaffTests(TestCase):
    def setUp(self):
        self.staff = CustomUser.objects.create(email='staff@example.test', is_staff=True)
        self.staff.user_permissions.add(Permission.objects.get(codename='manage_privacy'))
        self.other = CustomUser.objects.create(email='other@example.test', is_staff=True)
        self.feedback = Feedback.objects.create(contract_status='none', name='Test')
        self.consent = PersonalDataConsent.objects.create(
            feedback=self.feedback, purpose='feedback', document_version=DOCUMENT_VERSION,
        )

    def item(self, **extra):
        return PrivacyRequest(kind='withdraw', status='completed', consent=self.consent,
                              feedback=self.feedback, identity_verified_at=timezone.now(),
                              identity_check_reference='Verified offline ref 1', result='Executed', **extra)

    def test_only_authorized_staff_and_verified_identity_can_withdraw(self):
        from django.core.exceptions import PermissionDenied, ValidationError

        with self.assertRaises(PermissionDenied):
            resolve_privacy_request(self.item(), self.other)
        item = self.item()
        item.identity_verified_at = None
        with self.assertRaises(ValidationError):
            resolve_privacy_request(item, self.staff)
        resolve_privacy_request(self.item(), self.staff)
        self.consent.refresh_from_db()
        self.feedback.refresh_from_db()
        self.assertIsNotNone(self.consent.revoked_at)
        self.assertTrue(self.feedback.processing_blocked)

    def test_admin_journal_needs_explicit_privacy_and_view_permissions(self):
        model_admin = admin.site.get_model_admin(PersonalDataConsent)
        request = APIRequestFactory().get('/')
        self.other.user_permissions.add(Permission.objects.get(codename='view_personaldataconsent'))
        request.user = self.other
        self.assertFalse(model_admin.has_view_permission(request))
        self.staff.user_permissions.add(Permission.objects.get(codename='view_personaldataconsent'))
        request.user = CustomUser.objects.get(pk=self.staff.pk)
        self.assertTrue(model_admin.has_view_permission(request))
        self.assertFalse(model_admin.has_delete_permission(request))

    def test_mismatched_subject_and_missing_retention_basis_rejected(self):
        from django.core.exceptions import ValidationError

        item = self.item(user=self.other)
        with self.assertRaises(ValidationError):
            resolve_privacy_request(item, self.staff)
        item = self.item()
        item.status = 'retained'
        with self.assertRaises(ValidationError):
            resolve_privacy_request(item, self.staff)

    def test_verified_deletion_executes_and_expires_workflow_record(self):
        item = self.item()
        item.kind = 'delete'
        resolve_privacy_request(item, self.staff)
        self.assertFalse(Feedback.objects.exists())
        item.refresh_from_db()
        self.assertIsNone(item.feedback_id)
        self.assertIsNotNone(item.delete_after)
        with patch('users.tasks.timezone.now', return_value=item.delete_after + timedelta(seconds=1)):
            cleanup_personal_data(dry_run=False)
        self.assertFalse(PrivacyRequest.objects.exists())
