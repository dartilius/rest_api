import copy

import pytest
from http import HTTPStatus

from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability,
    StatusHistory
)


@pytest.mark.django_db
class TestNomenclatures:

    no_detail_url_list = [
        '/api/nomenclatures/',
        '/api/nomenclatures/versions/'
    ]
    detail_url_list = [
        '/api/nomenclatures/{nomenclature_id}/status_history/',
        '/api/nomenclatures/{nomenclature_id}/pending_tasks/',
        '/api/nomenclatures/{nomenclature_id}/ad_stat/',
        '/api/nomenclatures/{nomenclature_id}/music_stat/',
        '/api/nomenclatures/{nomenclature_id}/image_stat/',
        '/api/nomenclatures/{nomenclature_id}/video_stat/',
        '/api/nomenclatures/{nomenclature_id}/ticker_stat/'
    ]

    def test_availability_user(self, user_client, nomenclature):
        for url in self.no_detail_url_list:
            response = user_client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f'Авторизованный пользователь не имеет доступ к странице '
                f'{url}.'
            )
        for url in self.detail_url_list:
            response = user_client.get(
                url.format(nomenclature_id=str(nomenclature.id))
            )
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Авторизованный пользователь не имеет доступ к странице '
                f'{url}.'
            )

    def test_availability_anon(self, anon_client, nomenclature):
        for url in self.no_detail_url_list:
            response = anon_client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f'Не вторизованный пользователь имеет доступ к странице '
                f'{url}.'
            )
        nomenclature_id = str(nomenclature.id)
        detail_url_list = [
            url.format(nomenclature_id=nomenclature_id)
            for url in self.detail_url_list
            ]
        for url in detail_url_list:
            response = anon_client.get(url)
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Не авторизованный пользователь имеет доступ к странице '
                f'{url}.'
            )

    def test_create_valid_nomenclature(self, user_client, user):
        nomenclature_count = Nomenclature.objects.count()
        settings = {
            'fri': {'worktime': '09:00:00-20:00:00',
                    'default_volume': [50, 50, 50, 50]},
            'mon': {'worktime': '09:00:00-20:00:00',
                    'default_volume': [50, 50, 50, 50]},
            'sat': {'worktime': '09:00:00-20:00:00',
                    'default_volume': [50, 50, 50, 50]},
            'sun': {'worktime': '09:00:00-20:00:00',
                    'default_volume': [50, 50, 50, 50]},
            'thu': {'worktime': '09:00:00-20:00:00',
                    'default_volume': [50, 50, 50, 50]},
            'tue': {'worktime': '09:00:00-20:00:00',
                    'default_volume': [50, 50, 50, 50]},
            'wed': {'worktime': '09:00:00-20:00:00',
                    'default_volume': [50, 50, 50, 50]}
        }
        custom_settings = copy.deepcopy(settings)
        for day in custom_settings:
            custom_settings[day].update({
                'custom_volume': {
                    '09:00:00-11:00:00': [40, 40, 40, 40],
                    '17:00:00-20:00:00': [70, 70, 70, 70]
                }
            })

        data = {
            'name': 'Test Nomenclature',
            'owner': user,
            'timezone': 'Etc/GMT-7',
            'settings': settings
        }
        response = user_client.post(
            self.no_detail_url_list[0],
            data=data,
            format='json'
        )
        assert response.status_code == HTTPStatus.CREATED, (
            'Код статуса в ответе != 201.'
        )
        nomenclature_count += 1
        assert nomenclature_count == Nomenclature.objects.count(), (
            'Не удалось создать репликацию.'
        )
        response_data = response.json()
        assert response_data['owner'] == user.full_name, (
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
