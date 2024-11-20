import pytest
from http import HTTPStatus

from users.models import CustomUser


@pytest.mark.django_db
class TestUsers:

    url = '/api/users/'
    detail_url = '/api/users/{user_id}/'

    def test_avail_staff(self, admin_client, manager_client):
        response = admin_client.get(self.url)
        assert response.status_code == HTTPStatus.OK, (
            'Сотрудник ТО не имеет доступ к странице.'
        )
        response = manager_client.get(self.url)
        assert response.status_code == HTTPStatus.OK, (
            'Менеджер не имеет доступ к странице.'
        )

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
