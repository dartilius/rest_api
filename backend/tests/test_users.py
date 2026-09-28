from http import HTTPStatus
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import re

import jwt
import pytest
from django.conf import settings
from django.core.cache import cache
from django.core import mail
from django.test import override_settings
from rest_framework.test import APIClient

from users.models import CustomUser
from users.views import (
    REGISTRATION_CODE_TTL_SECONDS,
    _registration_code_cache_key,
)


@pytest.mark.django_db
class TestUsers:

    url = '/api/users/'
    detail_url = '/api/users/{user_id}/'

    def test_avail_staff(
        self,
        admin_client,
        admin_user,
        manager_client,
        user_client
    ):
        user_count = CustomUser.objects.count()
        clients = {admin_client: 'Сотрудник ТО',
                   manager_client: 'Менеджер',
                   user_client: 'Авторизованный пользователь'}
        for client in clients:
            response = client.get(self.url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'{clients[client]} не имеет доступ к странице.'
            )
            assert response_data['count'] == user_count, (
                'Кол-во элементов в ответе не равно кол-ву пользователей в базе.'
            )
            assert 'id' in response_data['results'][0], (
                'Ответ не содержит айди пользователя.'
            )
            assert 'role' in response_data['results'][0], (
                'Ответ не содержит роль пользователя.'
            )
            assert 'created' in response_data['results'][0], (
                'Ответ не содержит дату создания пользователя.'
            )

    def test_avail_anon(self, anon_client):
        response = anon_client.get(self.url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Неавторизованный пользователь имеет доступ к странице.'
        )

    def test_retrieve_duplicate_code1c_returns_latest_active_user(
        self, user, another_user, superuser_client
    ):
        code1c = 'duplicate-code1c'
        CustomUser.objects.filter(pk__in=[user.pk, another_user.pk]).update(
            code1c=code1c
        )
        CustomUser.objects.filter(pk=another_user.pk).update(is_active=False)

        response = superuser_client.get(f'{self.url}{code1c}/')

        assert response.status_code == HTTPStatus.OK
        assert response.json()['id'] == str(user.id)

    def test_create_valid_user(self, superuser_client):
        user_count = CustomUser.objects.count()
        valid_data = [
            {
                'email': 'test@test.com',
                'password': 'test',
                'phone_number': '+78005559999',
                'first_name': 'test',
                'last_name': 'user'
            },
            {
                'email': 'test1@test.com',
                'password': 'test',
                'phone_number': '+78005559998',
                'first_name': 'test',
                'last_name': 'user',
                'middle_name': 'django'
            }
        ]
        expected_fields = [
            'id',
            'role',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'created'
        ]

        for data in valid_data:
            response = superuser_client.post(self.url, data=data, format='json')
            assert response.status_code == HTTPStatus.CREATED, (
                'Код статуса в ответе != 201.'
            )
            user_count += 1
            assert user_count == CustomUser.objects.count(), (
                'Не удалось создать нового пользователя.'
            )
            response_data = response.json()
            for field in expected_fields:
                assert field in response_data, f'Ответ не содержит поле {field}'
            data.pop('password')
            for field in data:
                assert response_data[field] == data[field], (
                    f'{field} в ответе отличается от отправленного.'
                )

    def test_create_valid_user_no_permission(
            self,
            user_client,
            admin_client,
            manager_client
    ):
        clients = {user_client: 'user',
                   admin_client: 'admin',
                   manager_client: 'manager'}
        user_count = CustomUser.objects.count()
        data = {
                'email': 'test@test.com',
                'password': 'test',
                'phone_number': '+78005559999',
                'first_name': 'test',
                'last_name': 'user'
            }
        for client in clients:
            response = client.post(self.url, data=data, format='json')
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                f'Код статуса в ответе != 403.'
            )
            user_count += 1
            assert user_count != CustomUser.objects.count(), (
                f'Удалось создать нового пользователя. Права: {clients[client]}'
            )

    def test_create_valid_user_anon(self, anon_client):
        user_count = CustomUser.objects.count()
        data = {
                'email': 'test@test.com',
                'password': 'test',
                'phone_number': '+78005559999',
                'first_name': 'test',
                'last_name': 'user'
            }
        response = anon_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.'
        )
        user_count += 1
        assert user_count != CustomUser.objects.count(), (
            'Удалось создать нового пользователя без авторизации.'
        )

    def test_create_invalid_user(self, superuser_client):
        user_count = CustomUser.objects.count()
        invalid_data = [
            {
                "email": "test.test.com",
                "password": "test",
                "phone_number": "+78005559999",
                "first_name": "test",
                "last_name": "user"
            },
            {
                'password': 'test',
                'phone_number': '+78005559999',
                'first_name': 'test',
                'last_name': 'user'
            },
            {
                'email': 'test@test.com',
                'password': 'test',
                'phone_number': '99999999999',
                'first_name': 'test',
                'last_name': 'user'
            },
            {
                'email': 'test@test.com',
                'password': 'test',
                'phone_number': 'test',
                'first_name': 'test',
                'last_name': 'user'
            },
            {
                'email': 'test@test.com',
                'phone_number': '+78005559999',
                'password': 'test',
                'last_name': 'user'
            },
            {
                'email': 'test@test.com',
                'phone_number': '+78005559999',
                'password': 'test',
                'first_name': 'test'
            },

        ]
        for data in invalid_data:
            response = superuser_client.post(self.url, data=data, format='json')
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400.\n'
                f'Данные:\n{data}\nОтвет:{response.data}'
            )
            user_count += 1
            assert user_count > CustomUser.objects.count(), (
                'Удалось создать пользователя с неправильными данными.'
            )

    def test_delete_user_superuser(self, user, superuser_client):
        url = self.detail_url.format(user_id=str(user.id))
        response = superuser_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.'
        )
        user_obj = CustomUser.objects.get(id=user.id)
        assert user_obj.is_active is False, (
            f'Статус актуальности пользователя не изменился.\nОтвет:{response.json()}'
        )

    def test_delete_user_not_superuser(
        self,
        user,
        admin_client,
        manager_client,
        user_client
    ):
        clients = {admin_client: 'admin',
                   manager_client: 'manager',
                   user_client: 'ordinary'}
        url = self.detail_url.format(user_id=str(user.id))
        for client in clients:
            response = client.delete(url)
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                f'Код статуса в ответе != 403.'
            )
            user_obj = CustomUser.objects.get(id=user.id)
            assert user_obj.is_active is True, (
                f'Удалось изменить статус актуальности пользователя. Права: {clients[client]}'
            )

    def test_delete_user_anon(
        self,
        user,
        anon_client
    ):
        url = self.detail_url.format(user_id=str(user.id))
        response = anon_client.delete(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.'
        )
        user_obj = CustomUser.objects.get(id=user.id)
        assert user_obj.is_active is True, (
            f'Удалось изменить статус актуальности пользователя без авторизации.'
        )

    def test_update_user_superuser(self, user, superuser_client):
        data = {
            'email': 'new_email@test.com',
            'phone_number': '+78005557777',
            'first_name': 'new_first_name',
            'last_name': 'new_last_name',
            'middle_name': 'new_middle_name',
        }
        url = self.detail_url.format(user_id=str(user.id))
        response = superuser_client.put(url, data=data, format='json')
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response_data}'
        )
        updated_keys = [*data.keys()]
        for key in updated_keys:
            assert response_data[key] == data[key], (
                'Поле, которое было отправлено, не обновилось.'
                f'\nДанные: {data[key]}'
                f'\nОтвет: {response_data[key]}'
            )

    def test_partial_update_user_superuser(self, user, superuser_client):
        update_data = [
            {'email': 'new_email@test.com'},
            {'phone_number': '+78005557777'},
            {'first_name': 'new_first_name'},
            {'last_name': 'new_last_name'},
            {'middle_name': 'new_middle_name'},
        ]
        url = self.detail_url.format(user_id=str(user.id))
        for data in update_data:
            response = superuser_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Код статуса в ответе != 200.\nОтвет: {response_data}'
            )
            updated_key = ''.join(data.keys())
            assert response_data[updated_key] == data[updated_key], (
                'Поле, которое было отправлено, не обновилось.'
                f'\nДанные: {data[updated_key]}'
                f'\nОтвет: {response_data[updated_key]}'
            )

    def test_update_user_no_permission(
        self,
        user,
        admin_client,
        manager_client,
        user_client
    ):
        data = {
            'email': 'new_email@test.com',
            'phone_number': '+78005557777',
            'first_name': 'new_first_name',
            'last_name': 'new_last_name',
            'middle_name': 'new_middle_name',
        }
        clients = [admin_client, manager_client, user_client]
        url = self.detail_url.format(user_id=str(user.id))
        for client in clients:
            response = client.patch(url, data=data)
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                f'Код статуса в ответе != 403.'
            )
            user_obj = CustomUser.objects.get(id=str(user.id))
            updated_keys = [*data.keys()]
            for key in updated_keys:
                assert getattr(user_obj, key) != data[key], (
                    f'Данные пользователя обновились без должных прав: {key}'
                )

    def test_update_user_anon(self, user, anon_client):
        data = {
            'email': 'new_email@test.com',
            'phone_number': '+78005557777',
            'first_name': 'new_first_name',
            'last_name': 'new_last_name',
            'middle_name': 'new_middle_name',
        }
        url = self.detail_url.format(user_id=str(user.id))
        response = anon_client.patch(url, data=data)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.'
        )
        user_obj = CustomUser.objects.get(id=str(user.id))
        updated_keys = [*data.keys()]
        for key in updated_keys:
            assert getattr(user_obj, key) != data[key], (
                f'Данные пользователя обновились без авторизации: {key}'
            )


@pytest.mark.django_db
class TestEmailAvailabilityAndRegistrationCode:
    check_email_url = '/api/users/check-email/'
    send_registration_code_url = '/api/users/send-registration-code/'
    register_url = '/api/users/register/'

    @staticmethod
    def registration_data(email, verification_code):
        return {
            'email': email,
            'verification_code': verification_code,
            'first_name': 'New',
            'last_name': 'User',
            'phone_number': '+78005550001',
            'password': 'secure-password',
        }

    def test_check_email_returns_empty_200_for_available_email(self):
        response = APIClient().get(
            self.check_email_url,
            {'email': 'available@example.com'},
        )

        assert response.status_code == HTTPStatus.OK
        assert response.content == b''

    def test_check_email_returns_empty_204_for_existing_email(self, user):
        response = APIClient().get(
            self.check_email_url,
            {'email': user.email},
        )

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert response.content == b''

    def test_check_email_rejects_invalid_email(self):
        response = APIClient().get(
            self.check_email_url,
            {'email': 'invalid-email'},
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert 'email' in response.json()

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_registration_code_sends_six_digit_code_for_available_email(self):
        mail.outbox.clear()

        response = APIClient().post(
            self.send_registration_code_url,
            {'email': 'available@example.com'},
            format='json',
        )

        assert response.status_code == HTTPStatus.OK
        assert response.content == b''
        assert len(mail.outbox) == 1
        message = mail.outbox[0]
        assert message.to == ['available@example.com']
        assert re.search(r'\b\d{6}\b', message.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_send_registration_code_returns_empty_204_for_existing_email(self, user):
        mail.outbox.clear()

        response = APIClient().post(
            self.send_registration_code_url,
            {'email': user.email},
            format='json',
        )

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert response.content == b''
        assert mail.outbox == []

    def test_send_registration_code_rejects_invalid_email(self):
        response = APIClient().post(
            self.send_registration_code_url,
            {'email': 'invalid-email'},
            format='json',
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert 'email' in response.json()

    def test_register_creates_user_with_cached_verification_code(self):
        email = 'new-user@example.com'
        code = '123456'
        cache_key = _registration_code_cache_key(email)
        cache.set(cache_key, code, timeout=REGISTRATION_CODE_TTL_SECONDS)

        response = APIClient().post(
            self.register_url,
            self.registration_data(email, code),
            format='json',
        )

        assert response.status_code == HTTPStatus.CREATED
        assert CustomUser.objects.filter(email=email).exists()
        assert cache.get(cache_key) is None

    def test_register_rejects_wrong_verification_code(self):
        email = 'wrong-code@example.com'
        cache.set(
            _registration_code_cache_key(email),
            '123456',
            timeout=REGISTRATION_CODE_TTL_SECONDS,
        )

        response = APIClient().post(
            self.register_url,
            self.registration_data(email, '654321'),
            format='json',
        )

        assert response.status_code == HTTPStatus.BAD_REQUEST
        assert not CustomUser.objects.filter(email=email).exists()

    def test_register_cannot_reuse_consumed_verification_code(self):
        email = 'single-use@example.com'
        code = '123456'
        cache.set(
            _registration_code_cache_key(email),
            code,
            timeout=REGISTRATION_CODE_TTL_SECONDS,
        )

        first_response = APIClient().post(
            self.register_url,
            self.registration_data(email, code),
            format='json',
        )
        second_response = APIClient().post(
            self.register_url,
            self.registration_data(email, code),
            format='json',
        )

        assert first_response.status_code == HTTPStatus.CREATED
        assert second_response.status_code == HTTPStatus.BAD_REQUEST
        assert CustomUser.objects.filter(email=email).count() == 1


@pytest.mark.django_db(transaction=True)
class TestJWT:
    url_create = '/auth/jwt/create/'
    url_refresh = '/auth/jwt/refresh/'
    url_verify = '/auth/jwt/verify/'

    def check_request_with_invalid_data(self, client, url, invalid_data,
                                        expected_fields):
        response = client.post(url)
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            f'Если POST-запрос, отправленный к `{url}`, не содержит всех '
            'необходимых данных - должен вернуться ответ со статусом 400.'
        )

        response = client.post(url, data=invalid_data, format='json')
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Убедитесь, что POST-запрос с некорректными данными, '
            f'отправленный к `{url}`, возвращает ответ со статусом 401.'
        )
        for field in expected_fields:
            assert field in response.json(), (
                'Убедитесь, что в ответе на POST-запрос с некорректными '
                f'данными, отправленный к `{url}`, содержится поле `{field}` '
                'с соответствующим сообщением.'
            )

    def test_jwt_create__invalid_data(self, client, user):
        url = self.url_create
        response = client.post(url)
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Убедитесь, что POST-запрос без необходимых данных, отправленный '
            f'к `{url}`, возвращает ответ со статусом код 400.'
        )
        fields_invalid = ['email', 'password']
        for field in fields_invalid:
            assert field in response.json(), (
                'Убедитесь, что в ответе на POST-запрос без необходимых '
                f'данных, отправленный к `{url}` содержится информация об '
                'обязательных для этого эндпоинта полях. Сейчас ответ не '
                f'содержит информацию о поле `{field}`.'
            )

        invalid_data = (
            {
                'email': 'invalid_email_not_exists',
                'password': 'invalid pwd'
            },
            {
                'email': user.email,
                'password': 'invalid pwd'
            }
        )
        field = 'detail'
        for data in invalid_data:
            response = client.post(url, data=data, format='json')
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                'Убедитесь, что POST-запрос с некорректными данными, '
                f'отправленный к`{url}`, возвращает ответ со статусом 401.'
            )
            assert field in response.json(), (
                'Убедитесь, что в ответе на POST-запрос с некорректными '
                f'данными, отправленный к `{url}`, содержится поле `{field}` '
                'с сообщением об ошибке.'
            )

    def test_jwt_create__valid_data(self, client, user):
        url = self.url_create
        valid_data = {
            'email': user.email,
            'password': 'test'
        }
        response = client.post(url, data=valid_data, format='json')
        assert response.status_code == HTTPStatus.OK, (
            'Убедитесь, что POST-запрос с корректными данными, отправленный '
            f'к `{url}`, возвращает ответ со статусом 200.'
        )
        fields_in_response = ['refresh', 'access']
        for field in fields_in_response:
            assert field in response.json(), (
                'Убедитесь, что в ответе на  POST-запрос с корректными '
                f'данными, отправленный к `{url}`, содержится поле `{field}` '
                'с соответствующим токеном.'
            )

        access_payload = jwt.decode(
            response.json()['access'],
            settings.SIMPLE_JWT['VERIFYING_KEY'],
            algorithms=['RS256'],
            audience='rmc-site-api',
            issuer='rmc-django',
        )
        assert access_payload['sub'] == str(user.id)
        assert access_payload['role'] == user.role
        assert access_payload['token_type'] == 'access'

    def test_jwt_refresh__invalid_data(self, client):
        invalid_data = {
            'refresh': 'invalid token'
        }
        fields_expected = ['detail', 'code']
        self.check_request_with_invalid_data(
            client, self.url_refresh, invalid_data, fields_expected
        )

    def test_jwt_refresh__valid_data(self, client, user):
        url = self.url_refresh
        valid_data = {
            'email': user.email,
            'password': 'test'
        }
        response = client.post(self.url_create, data=valid_data, format='json')
        token_refresh = response.json().get('refresh')
        response = client.post(url, data={'refresh': token_refresh})
        assert response.status_code == HTTPStatus.OK, (
            'Убедитесь, что POST-запрос с корректными данными, отправленный '
            f'к `{url}`, возвращает ответ со статусом 200.'
        )
        field = 'access'
        assert field in response.json(), (
            'Убедитесь, что в ответе на POST-запрос с корректными данными, '
            f'отправленный к `{url}`, содержится поле `{field}`, '
            'содержащее новый токен.'
        )

    def test_jwt_verify__invalid_data(self, client):
        invalid_data = {
            'token': 'invalid token'
        }
        fields_expected = ['detail', 'code']
        self.check_request_with_invalid_data(
            client, self.url_verify, invalid_data, fields_expected
        )

    def test_jwt_verify__valid_data(self, client, user):
        url = self.url_verify
        valid_data = {
            'email': user.email,
            'password': 'test'
        }
        response = client.post(self.url_create, data=valid_data, format='json')
        response_data = response.json()
        if 'detail' in response_data:
            assert response_data['detail'] is None

        for token in (response_data.get('access'),
                      response_data.get('refresh')):
            response = client.post(url, data={'token': token})
            assert response.status_code == HTTPStatus.OK, (
                'Убедитесь, что POST-запрос с корректными данными, '
                f'отправленный к `{url}`, возвращает ответ со статусом 200. '
                f'Корректными данными считаются `refresh`- и `access`-токены.'
            )

    def test_legacy_refresh_exchanges_old_hs256_token_once(self, client, user):
        now = datetime.now(timezone.utc)
        legacy_secret = 'test-legacy-django-secret'
        legacy_refresh = jwt.encode(
            {
                'token_type': 'refresh',
                'user_id': str(user.id),
                'jti': uuid4().hex,
                'iat': now,
                'exp': now + timedelta(days=1),
            },
            legacy_secret,
            algorithm='HS256',
        )

        with override_settings(
            JWT_LEGACY_HS256_SECRET=legacy_secret,
            JWT_LEGACY_HS256_ACCEPT_UNTIL=(now + timedelta(days=1)).isoformat(),
        ):
            response = client.post(
                '/auth/jwt/legacy-refresh/',
                data={'refresh': legacy_refresh},
                format='json',
            )
            replay_response = client.post(
                '/auth/jwt/legacy-refresh/',
                data={'refresh': legacy_refresh},
                format='json',
            )

        assert response.status_code == HTTPStatus.OK
        assert replay_response.status_code == HTTPStatus.UNAUTHORIZED
        payload = jwt.decode(
            response.json()['access'],
            settings.SIMPLE_JWT['VERIFYING_KEY'],
            algorithms=['RS256'],
            audience='rmc-site-api',
            issuer='rmc-django',
        )
        assert payload['sub'] == str(user.id)
        assert payload['role'] == user.role
