import pytest
from http import HTTPStatus
from dotenv import load_dotenv

from tasks.models import Task

load_dotenv()


@pytest.mark.django_db
class TestTasks:

    url = '/api/tasks/'
    task_url = '/api/tasks/{task_id}/'

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

    def test_task_detail_user(self, user_client, task):
        task_id = str(task.id)
        response = user_client.get(self.task_url.format(task_id=task_id))
        assert response.status_code == HTTPStatus.OK, (
            'Авторизованный пользователь не имеет доступ к странице.'
        )

    def test_task_detail_anon(self, anon_client, task):
        task_id = str(task.id)
        response = anon_client.get(self.task_url.format(task_id=task_id))
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Неавторизованный пользователь имеет доступ к странице.'
        )

    def test_create_valid_task(self, user_client, user, nomenclature):
        task_count = Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        data = {
            'client': nomenclature_id,
            'parameters': 'test'
        }
        response = user_client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.CREATED, (
            'Код статуса в ответе != 201.'
        )
        task_count += 1
        assert task_count == Task.objects.count(), (
            'Не удалось создать репликацию.'
        )
        response_data = response.json()
        assert response_data['owner'] == user.get_full_name(), (
            'Создатель репликации не встал в соответствующее поле.'
        )
        assert response_data['client']['id'] == data['client'], (
            'Целевая рабочая станция созданной репликации отличается от '
            'таковой в отправленных данных.'
        )
        assert response_data['parameters'] == data['parameters'], (
            'Параметры репликации отличаются от отправленных данных.'
        )

    def test_create_invalid_task(self, user_client, nomenclature):
        task_count = Task.objects.count()
        invalid_data = {
            'client': nomenclature.name,
            'parameters': 'test'
        }
        response = user_client.post(self.url, data=invalid_data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            'Код статуса в ответе != 400.'
        )
        task_count += 1
        assert task_count != Task.objects.count(), (
            f'Удалось создать репликацию с неправильными данными.'
        )

    def test_create_task_anon(self, client, nomenclature):
        task_count = Task.objects.count()
        parameters = 'test'
        data = {
            'client': str(nomenclature.id),
            'parameters': parameters
        }
        response = client.post(self.url, data=data, format='json')
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Код статуса в ответе != 401.'
        )
        task_count += 1
        assert task_count != Task.objects.count(), (
            'Удалось создать репликацию без авторизации.'
        )

    def test_delete_task_user(self, user_client, task):
        task_count = Task.objects.count()
        task_id = str(task.id)
        response = user_client.delete(self.task_url.format(task_id=task_id))
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Код статуса в ответе != 403.'
        )
        task_count -= 1
        assert task_count != Task.objects.count(), (
            'Удалось удалить репликацию без должных прав.'
        )

    def test_delete_task_anon(self, anon_client, task):
        task_count = Task.objects.count()
        task_id = str(task.id)
        response = anon_client.delete(self.task_url.format(task_id=task_id))
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Код статуса в ответе != 401.'
        )
        task_count -= 1
        assert task_count != Task.objects.count(), (
            'Удалось удалить репликацию без авторизации.'
        )

    @pytest.mark.xfail(
        reason='Работает в админ панели, но не через view, пока хз как починить'
    )
    def test_delete_task_admin(self, admin_client, task):
        task_count = Task.objects.count()
        assert task_count == 1
        task_id = str(task.id)
        response = admin_client.delete(self.task_url.format(task_id=task_id))
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            'Код статуса в ответе != 204.'
        )
        task_count -= 1
        assert task_count != Task.objects.count(), (
            'Пользователь-админ не может удалить репликацию.'
        )
