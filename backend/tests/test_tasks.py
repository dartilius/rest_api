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
    def check_get_list_response(task_data, response_data):
        task_count = task_data.pop('count')
        assert task_count == response_data['count'], (
            'Кол-во элементов в ответе не равно кол-ву репликаций в базе.'
        )
        for key in task_data:
            assert key in response_data['results'][0], (
                f'Ответ не содержит ключ {key}.'
            )
            assert response_data['results'][0][key] == task_data[key], (
                f'{key} репликации в ответе не совпадает с {key} репликации в базе'
            )

    def test_get_task_list_staff(self, admin_client, manager_client, user, task):
        task_data = {
            'count': Task.objects.count(),
            'id': str(task.id),
            'owner': user.full_name,
            'client': {'id': str(task.client.id), 'name': task.client.name},
            'type': task.type,
            'status': task.status
        }
        clients = {admin_client: 'Сотрудник ТО', manager_client: 'Менеджер'}
        for client in clients:
            response = client.get(self.url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'{clients[client]} не имеет доступ к странице списка репликаций.'
            )
            self.check_get_list_response(task_data, response_data)

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
