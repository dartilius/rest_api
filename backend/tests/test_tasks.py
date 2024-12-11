import pytest
from http import HTTPStatus

from tasks.models import Task


@pytest.mark.django_db
class TestTasks:

    url = '/api/tasks/'
    task_url = '/api/tasks/{task_id}/'

    @staticmethod
    def get_valid_data(nomenclature_id) -> list:
        reboot_task = 15
        update_task = 16
        custom_task = 17
        valid_data = [
            {
                'client': nomenclature_id,
                'type': reboot_task
            },
            {
                'client': nomenclature_id,
                'type': update_task
            },
            {
                'client': nomenclature_id,
                'type': custom_task
            },
            {
                'client': nomenclature_id,
                'type': custom_task,
                'parameters': 'test'
            }
        ]
        return valid_data

    @staticmethod
    def check_get_list_response(client, task, response, user_name):
        task_count = Task.objects.count()
        task_id = str(task.id)
        task_owner = user_name
        task_client = {'id': str(task.client.id), 'name': task.client.name}
        task_type = task.type
        task_status = task.status
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'{client} не имеет доступ к странице списка репликаций.'
        )
        assert task_count == response_data['count'], (
            'Кол-во элементов в ответе не равно кол-ву репликаций в базе.'
        )
        assert 'id' in response_data['results'][0], (
            'Ответ не содержит поле айди репликации.'
        )
        assert response_data['results'][0]['id'] == task_id, (
            'Айди файла в ответе не совпадает с айди файла в базе'
        )
        assert 'owner' in response_data['results'][0], (
            'Ответ не содержит поле "Кто создал" репликации.'
        )
        assert response_data['results'][0]['owner'] == task_owner, (
            'Создатель репликации в ответе не совпадает с '
            'создателем репликации в базе'
        )
        assert 'client' in response_data['results'][0], (
            'Ответ не содержит поле целевой рабочей станции репликации.'
        )
        assert response_data['results'][0]['client'] == task_client, (
            'Целевая рабочая станция репликации в ответе и в базе не совпадает'
        )
        assert 'type' in response_data['results'][0], (
            'Ответ не содержит поле типа репликации.'
        )
        assert response_data['results'][0]['type'] == task_type, (
            'Тип репликации в ответе не совпадает с типом репликации в базе'
        )
        assert 'status' in response_data['results'][0], (
            'Ответ не содержит поле статуса репликации.'
        )
        assert response_data['results'][0]['status'] == task_status, (
            'Статус репликации в ответе не совпадает со статусом репликации в базе'
        )

    def test_get_task_list_admin(self, admin_client, user, task):
        response = admin_client.get(self.url)
        user_name = user.full_name
        self.check_get_list_response('Сотрудник ТО', task, response, user_name)

    def test_get_task_list_manager(self, manager_client, user, task):
        response = manager_client.get(self.url)
        user_name = user.full_name
        self.check_get_list_response('Менеджер', task, response, user_name)

    def test_availability_not_staff(self, user_client, anon_client, task):
        urls = [
            self.url,
            self.task_url.format(task_id=str(task.id)),
        ]
        for url in urls:
            response = user_client.get(url)
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                f'Обычный пользователь имеет доступ к странице {url}.'
            )
            response = anon_client.get(url)
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Не авторизованный пользователь имеет доступ к странице {url}.'
            )

    def test_create_valid_task_admin(
        self,
        admin_client,
        admin_user,
        nomenclature
    ):
        task_count = Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        valid_data = self.get_valid_data(nomenclature_id)
        for data in valid_data:
            response = admin_client.post(self.url, data=data, format='json')
            assert response.status_code == HTTPStatus.CREATED, (
                'Код статуса в ответе != 201.'
            )
            task_count += 1
            assert task_count == Task.objects.count(), (
                'Не удалось создать репликацию.'
            )
            response_data = response.json()
            assert response_data['owner'] == admin_user.full_name, (
                'Создатель репликации не встал в соответствующее поле.'
            )
            assert response_data['client']['id'] == nomenclature_id, (
                'Целевая рабочая станция созданной репликации отличается от '
                'таковой в отправленных данных.'
            )
            assert response_data['type'] == data['type'], (
                'Тип репликации отличается от отправленного.'
            )
            if response_data['parameters'] is not None:
                assert response_data['parameters'] == data['parameters'], (
                    'Параметры репликации отличаются от отправленных данных.'
                )

    def test_create_valid_task_manager(
        self,
        manager_client,
        manager_user,
        nomenclature
    ):
        task_count = Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        valid_data = self.get_valid_data(nomenclature_id)
        for data in valid_data:
            response = manager_client.post(self.url, data=data, format='json')
            assert response.status_code == HTTPStatus.CREATED, (
                'Код статуса в ответе != 201.'
            )
            task_count += 1
            assert task_count == Task.objects.count(), (
                'Не удалось создать репликацию.'
            )
            response_data = response.json()
            assert response_data['owner'] == manager_user.full_name, (
                'Создатель репликации не встал в соответствующее поле.'
            )
            assert response_data['client']['id'] == nomenclature_id, (
                'Целевая рабочая станция созданной репликации отличается от '
                'таковой в отправленных данных.'
            )
            if response_data['parameters'] is not None:
                assert response_data['parameters'] == data['parameters'], (
                    'Параметры репликации отличаются от отправленных данных.'
                )

    def test_create_valid_task_user(self, user_client, nomenclature):
        task_count = Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        valid_data = self.get_valid_data(nomenclature_id)
        for data in valid_data:
            response = user_client.post(self.url, data=data, format='json')
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                'Код статуса в ответе != 403.'
            )
            task_count += 1
            assert task_count != Task.objects.count(), (
                'Обычному пользователю удалось создать репликацию.'
            )

    def test_create_valid_task_anon(self, anon_client, nomenclature):
        task_count = Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        valid_data = self.get_valid_data(nomenclature_id)
        for data in valid_data:
            response = anon_client.post(self.url, data=data, format='json')
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                'Код статуса в ответе != 401.'
            )
            task_count += 1
            assert task_count != Task.objects.count(), (
                'Неавторизованному пользователю удалось создать репликацию.'
            )

    def test_create_invalid_task(self, admin_client, nomenclature):
        task_count = Task.objects.count()
        invalid_data = {
            'client': nomenclature.name,
            'parameters': 'test'
        }
        response = admin_client.post(self.url, data=invalid_data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        task_count += 1
        assert task_count != Task.objects.count(), (
            f'Удалось создать репликацию с неправильными данными.'
        )

    def test_update_task(self, admin_client, task, nomenclature_1):
        data = {
            'client': str(nomenclature_1.id),
            'parameters': None,
            'type': 16,
            'status': 4
        }
        url = self.task_url.format(task_id=str(task.id))
        response = admin_client.put(url, data=data, format='json')
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
            f'Код статуса в ответе != 405.Ответ: {response.json()}'
        )

    def test_partial_update_task(self, admin_client, task, nomenclature_1):
        update_data = [
            {'client': str(nomenclature_1.id)},
            {'parameters': None},
            {'type': 16},
            {'status': 4}
        ]
        url = self.task_url.format(task_id=str(task.id))
        for data in update_data:
            response = admin_client.patch(url, data=data, format='json')
            assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
                f'Код статуса в ответе != 405.Ответ: {response.json()}'
            )

    def test_cancel_task_staff(
        self,
        admin_client,
        manager_client,
        superuser_client,
        task
    ):
        clients = {admin_client: 'admin',
                   manager_client: 'manager',
                   superuser_client: 'superuser'}
        for client in clients:
            response = client.delete(self.task_url.format(task_id=str(task.id)))
            assert response.status_code == HTTPStatus.NO_CONTENT, (
                'Код статуса в ответе != 204.'
            )
            task_obj = Task.objects.last()
            assert task_obj.status == 3, (
                f'Не удалось отменить репликацию. Права: {clients[client]}'
            )
            task_obj.status = 0
            task_obj.save(update_fields=['status'])

    def test_cancel_task_user(
        self,
        user_client,
        task
    ):
        response = user_client.delete(self.task_url.format(task_id=str(task.id)))
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Код статуса в ответе != 403.'
        )
        task_obj = Task.objects.last()
        assert task_obj.status == 0, 'Обычный пользователь смог отменить репликацию.'

    def test_cancel_task_anon(
        self,
        anon_client,
        task
    ):
        response = anon_client.delete(self.task_url.format(task_id=str(task.id)))
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Код статуса в ответе != 401.'
        )
        task_obj = Task.objects.last()
        assert task_obj.status == 0, 'Неавторизованный пользователь смог отменить репликацию.'
