import pytest
from http import HTTPStatus

from tasks.models import Task


@pytest.mark.django_db
class TestTasks:

    url = '/api/tasks/'
    task_url = '/api/tasks/{task_id}/'

    def test_availability_staff(self, admin_client, manager_client, task):
        urls = [
            self.url,
            self.task_url.format(task_id=str(task.id)),
        ]
        for url in urls:
            response = admin_client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f'Сотрудник ТО не имеет доступ к странице {url}.'
            )
            response = manager_client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f'Менеджер не имеет доступ к странице {url}.'
            )

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

    def test_create_valid_task_staff(
        self,
        admin_client,
        admin_user,
        manager_client,
        manager_user,
        nomenclature
    ):
        task_count = Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        data = {
            'client': nomenclature_id,
            'parameters': 'test'
        }
        clients = {admin_client: admin_user, manager_client: manager_user}
        for client in clients:
            response = client.post(self.url, data=data, format='json')
            assert response.status_code == HTTPStatus.CREATED, (
                'Код статуса в ответе != 201.'
            )
            task_count += 1
            assert task_count == Task.objects.count(), (
                'Не удалось создать репликацию.'
            )
            response_data = response.json()
            assert response_data['owner'] == clients[client].full_name, (
                'Создатель репликации не встал в соответствующее поле.'
            )
            assert response_data['client']['id'] == data['client'], (
                'Целевая рабочая станция созданной репликации отличается от '
                'таковой в отправленных данных.'
            )
            assert response_data['parameters'] == data['parameters'], (
                'Параметры репликации отличаются от отправленных данных.'
            )

    def test_create_valid_task_user(self, user_client, nomenclature):
        task_count = Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        data = {
            'client': nomenclature_id,
            'parameters': 'test'
        }
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
        data = {
            'client': nomenclature_id,
            'parameters': 'test'
        }
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
            task_obj.save()

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
