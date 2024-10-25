import pytest
from http import HTTPStatus
from dotenv import load_dotenv

from users.models import CustomUser

load_dotenv()


@pytest.mark.django_db
class TestUsers:

    url = '/api/users/'

    def test_avail_user(self, user_client):
        response = user_client.get(self.url)
        assert response.status_code == HTTPStatus.OK, (
            'Авторизованный пользователь не имеет доступ к странице.'
        )

    def test_avail_anon(self, anon_client):
        response = anon_client.get(self.url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Неавторизованный пользователь имеет доступ к странице.'
        )

    def test_avail_admin(self, admin_client):
        response = admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK, (
            'Пользователь-админ не имеет доступ к странице.'
        )

    def test_create_user_valid_data(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            'email': 'test@test.com',
            'password': 'test',
            'phone_number': '+78005559999',
            'first_name': 'test',
            'last_name': 'user'
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.CREATED, (
            'Код статуса в ответе != 201.'
        )
        user_count += 1
        assert user_count == CustomUser.objects.count(), (
            'Не удалось создать нового пользователя.'
        )
        test_data = response.json()
        assert test_data['email'] == data['email'], (
            'Email нового пользователя отличается от отправленного.'
        )
        assert test_data['phone_number'] == data['phone_number'], (
            'Номер телефона нового пользователя отличается от отправленного.'
        )
        assert test_data['first_name'] == data['first_name'], (
            'Имя нового пользователя отличается от отправленного.'
        )
        assert test_data['last_name'] == data['last_name'], (
            'Фамилия нового пользователя отличается от отправленного.'
        )

    def test_create_user_valid_data_middle_name(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            'email': 'test1@test.com',
            'password': 'test',
            'phone_number': '+78005559998',
            'first_name': 'test',
            'last_name': 'user',
            'middle_name': 'django'
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.CREATED, (
            'Код статуса в ответе != 201.'
        )
        user_count += 1
        assert user_count == CustomUser.objects.count(), (
            'Не удалось создать нового пользователя.'
        )
        test_data = response.json()
        assert test_data['email'] == data['email'], (
            'Email нового пользователя отличается от отправленного.'
        )
        assert test_data['phone_number'] == data['phone_number'], (
            'Номер телефона нового пользователя отличается от отправленного.'
        )
        assert test_data['first_name'] == data['first_name'], (
            'Имя нового пользователя отличается от отправленного.'
        )
        assert test_data['last_name'] == data['last_name'], (
            'Фамилия нового пользователя отличается от отправленного.'
        )
        assert test_data['middle_name'] == data['middle_name'], (
            'Отчество нового пользователя отличается от отправленного.'
        )

    def test_create_user_invalid_email(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            "email": "test.test.com",
            "password": "test",
            "phone_number": "+78005559999",
            "first_name": "test",
            "last_name": "user"
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        user_count += 1
        assert user_count > CustomUser.objects.count(), (
            'Удалось создать пользователя с неправильным email.'
        )

    def test_create_user_no_email(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            "password": "test",
            "phone_number": "+78005559999",
            "first_name": "test",
            "last_name": "user"
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        user_count += 1
        assert user_count > CustomUser.objects.count(), (
            'Удалось создать пользователя без email.'
        )

    def test_create_user_invalid_phone_number_1(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            "email": "test@test.com",
            "password": "test",
            "phone_number": "99999999999",
            "first_name": "test",
            "last_name": "user"
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        user_count += 1
        assert user_count > CustomUser.objects.count(), (
            'Удалось создать пользователя с неправильным номером телефона.'
        )

    def test_create_user_invalid_phone_number_2(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            "email": "test@test.com",
            "password": "test",
            "phone_number": "test",
            "first_name": "test",
            "last_name": "user"
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        user_count += 1
        assert user_count > CustomUser.objects.count(), (
            'Удалось создать пользователя с неправильным номером телефона.'
        )

    def test_create_user_no_phone_number(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            "email": "test@test.com",
            "password": "test",
            "first_name": "test",
            "last_name": "user"
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        user_count += 1
        assert user_count > CustomUser.objects.count(), (
            'Удалось создать пользователя без номера телефона.'
        )

    def test_create_user_no_first_name(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            "email": "test@test.com",
            "phone_number": "+78005559999",
            "password": "test",
            "last_name": "user"
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        user_count += 1
        assert user_count > CustomUser.objects.count(), (
            'Удалось создать пользователя без имени.'
        )

    def test_create_user_no_last_name(self, admin_client):
        user_count = CustomUser.objects.count()
        data = {
            "email": "test@test.com",
            "phone_number": "+78005559999",
            "password": "test",
            "first_name": "test"
        }
        response = admin_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        user_count += 1
        assert user_count > CustomUser.objects.count(), (
            'Удалось создать пользователя без фамилии.'
        )


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
