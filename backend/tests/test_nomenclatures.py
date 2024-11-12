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
            assert response.status_code == HTTPStatus.OK, (
                f'Авторизованный пользователь не имеет доступ к странице '
                f'{url}.'
            )

    def test_availability_staff(
        self,
        admin_client,
        manager_client,
        nomenclature
    ):
        for url in self.no_detail_url_list:
            response = admin_client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f'Сотрудник ТО не имеет доступ к странице '
                f'{url}.'
            )
        for url in self.detail_url_list:
            response = admin_client.get(
                url.format(nomenclature_id=str(nomenclature.id))
            )
            assert response.status_code == HTTPStatus.OK, (
                f'Сотрудник ТО не имеет доступ к странице '
                f'{url}.'
            )
        for url in self.no_detail_url_list:
            response = manager_client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f'Менеджер не имеет доступ к странице '
                f'{url}.'
            )
        for url in self.detail_url_list:
            response = manager_client.get(
                url.format(nomenclature_id=str(nomenclature.id))
            )
            assert response.status_code == HTTPStatus.OK, (
                f'Менеджер не имеет доступ к странице '
                f'{url}.'
            )

    def test_availability_anon(self, anon_client, nomenclature):
        for url in self.no_detail_url_list:
            response = anon_client.get(url)
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Не авторизованный пользователь имеет доступ к странице '
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

    def test_create_valid_nomenclature_admin(self, admin_client, admin_user):
        from random import randint, choices
        from string import ascii_letters, digits
        nomenclature_count = Nomenclature.objects.count()
        from nomenclatures.models import TIMEZONES
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
            begin_time = f'{randint(9, 14)}:00:00'
            end_time = f'{randint(15, 20)}:00:00'
            custom_settings[day].update({
                'custom_volume': {
                    f'{begin_time}-{end_time}': [randint(0, 100)] * 4
                }
            })
        chars = ascii_letters + digits
        valid_data = [
            {
                'name': ''.join(choices(chars, k=10)),
                'timezone': 'Etc/GMT-7',
                'settings': settings
            },
            {
                'name': ''.join(choices(chars, k=10)),
                'timezone': 'Etc/GMT-7',
                'settings': custom_settings
            }
        ]
        for data in valid_data:
            response = admin_client.post(
                self.no_detail_url_list[0],
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201. Данные:\n{data}\nОтвет:{response.data}'
            )
            nomenclature_count += 1
            assert nomenclature_count == Nomenclature.objects.count(), (
                'Не удалось создать номенклатуру.'
            )
            response_data = response.json()
            assert response_data['main_info']['owner'] == admin_user.full_name, (
                'Создатель номенклатуры не встал в соответствующее поле.'
            )
            assert response_data['main_info']['timezone'] == TIMEZONES[data['timezone']], (
                'Часовой пояс отличаются от отправленных данных.'
            )
            check_settings = data['settings']
            for day in check_settings:
                if 'custom_volume' not in check_settings[day]:
                    check_settings[day]['custom_volume'] = {}
            assert response_data['settings'] == check_settings, (
                'Настройки вещания отличаются от отправленных данных.'
            )

    def test_create_valid_nomenclature_manager(
        self,
        manager_client,
        manager_user
    ):
        from random import randint, choices
        from string import ascii_letters, digits
        nomenclature_count = Nomenclature.objects.count()
        from nomenclatures.models import TIMEZONES
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
            begin_time = f'{randint(9, 14)}:00:00'
            end_time = f'{randint(15, 20)}:00:00'
            custom_settings[day].update({
                'custom_volume': {
                    f'{begin_time}-{end_time}': [randint(0, 100)] * 4
                }
            })
        chars = ascii_letters + digits
        valid_data = [
            {
                'name': ''.join(choices(chars, k=10)),
                'timezone': 'Etc/GMT-7',
                'settings': settings
            },
            {
                'name': ''.join(choices(chars, k=10)),
                'timezone': 'Etc/GMT-7',
                'settings': custom_settings
            }
        ]
        for data in valid_data:
            response = manager_client.post(
                self.no_detail_url_list[0],
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201. Данные:\n{data}\nОтвет:{response.data}'
            )
            nomenclature_count += 1
            assert nomenclature_count == Nomenclature.objects.count(), (
                'Не удалось создать номенклатуру.'
            )
            response_data = response.json()
            assert response_data['main_info']['owner'] == manager_user.full_name, (
                'Создатель номенклатуры не встал в соответствующее поле.'
            )
            assert response_data['main_info']['timezone'] == TIMEZONES[data['timezone']], (
                'Часовой пояс отличаются от отправленных данных.'
            )
            check_settings = data['settings']
            for day in check_settings:
                if 'custom_volume' not in check_settings[day]:
                    check_settings[day]['custom_volume'] = {}
            assert response_data['settings'] == check_settings, (
                'Настройки вещания отличаются от отправленных данных.'
            )

    def test_create_valid_nomenclature_anon(self, anon_client):
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
        data = {
            'name': 'Test Nomenclature',
            'timezone': 'Etc/GMT-7',
            'settings': settings
        }
        response = anon_client.post(
            self.no_detail_url_list[0],
            data=data,
            format='json'
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Код статуса в ответе != 401.'
        )
        nomenclature_count += 1
        assert nomenclature_count != Nomenclature.objects.count(), (
            'Удалось создать номенклатуру без авторизации.'
        )

    def test_create_valid_nomenclature_user(self, user_client):
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
        data = {
            'name': 'Test Nomenclature',
            'timezone': 'Etc/GMT-7',
            'settings': settings
        }
        response = user_client.post(
            self.no_detail_url_list[0],
            data=data,
            format='json'
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Код статуса в ответе != 403.'
        )
        nomenclature_count += 1
        assert nomenclature_count != Nomenclature.objects.count(), (
            'Удалось создать номенклатуру без должных прав.'
        )

    def test_create_invalid_nomenclature(self, admin_client):
        from random import randint
        nomenclature_count = Nomenclature.objects.count()
        valid_settings = {
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
        custom_settings = copy.deepcopy(valid_settings)
        for day in custom_settings:
            begin_time = f'{randint(9, 14)}:00:00'
            end_time = f'{randint(15, 20)}:00:00'
            custom_settings[day].update({
                'custom_volume': {
                    f'{begin_time}-{end_time}': [randint(0, 100)] * 4
                }
            })
        invalid_settings = [
            {
                'fri': {'default_volume': [50, 50, 50, 50]},
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
                },
            {
                'fri': {'worktime': None,
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
            },
            {
                'fri': {'worktime': '00:00:00-24:00:00',
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
            },
            {
                'fri': {'worktime': '20:00:00-09:00:00',
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
            },
            {
                'fri': {'worktime': ['09:00:00-20:00:00'],
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
            },
            {
                'fri': {'worktime': '09:00:00-09:00:00',
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
            },
            {
                'fri': {'worktime': '09:00:00-20:00:00'},
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
            },
            {
                'fri': {'worktime': '09:00:00-20:00:00',
                        'default_volume': None},
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
            },
            {
                'fri': {'worktime': '09:00:00-20:00:00',
                        'default_volume': [50, 50, 50, 150]},
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
            },
            {
                'fri': {'worktime': '09:00:00-20:00:00',
                        'default_volume': '50, 50, 50, 50'},
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
            },
            {
                'fri': {'worktime': '09:00:00-20:00:00',
                        'default_volume': [50, 50, 50]},
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
            },
            {
                'fri': {'worktime': '09:00:00-20:00:00',
                        'default_volume': [50, 50, 50, 50, 50]},
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
            },
            {
                'fri': {'worktime': '09:00:00-20:00:00',
                        'default_volume': [50, 50, 50, 50],
                        'invalid_key': 'invalid_val'},
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
            },
            {
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
                        'default_volume': [50, 50, 50, 50]},
                'xxx': {'worktime': '09:00:00-20:00:00',
                        'default_volume': [50, 50, 50, 50]}
            },
            {
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
                        'default_volume': [50, 50, 50, 50]}
            },
            {
                'fri': {},
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
                'wed': {'worktime': '09:00:00-20:00:00'}
            }
        ]
        invalid_custom_settings = [
            {
                'custom_volume': {
                    '12:00:00-09:00:00': [50] * 4
                }
            },
            {
                'custom_volume': {
                    '20:00:00-24:00:00': [50] * 4
                }
            },
            {
                'custom_volume': {
                    '09:00:00-12:00:00': [50] * 4,
                    '10:00:00-14:00:00': [50] * 4
                }
            },
            {
                'custom_volume': {
                    '09:00:00-12:00:00': [150] * 4,
                }
            },
            {
                'custom_volume': {
                    '09:00:00-12:00:00': [50] * 3,
                }
            },
            {
                'custom_volume': {
                    '09:00:00-12:00:00': [50] * 5,
                }
            },
            {
                'custom_volume': {
                    12: [50] * 4,
                }
            },
            {
                'custom_volume': {
                    '09:00:00-12:00:00': '[50] * 4',
                }
            },
            {
                'custom_volume': {
                    '09:00:00-09:00:00': [50] * 4,
                }
            },
            {
                'custom_volume': {
                    'invalid_key': [50] * 4,
                }
            },
            {
                'invalid_key': {
                    '09:00:00-12:00:00': [50] * 4,
                }
            },
            {
                'custom_volume': {}
            }
        ]
        invalid_data = [
            {
                'name': None,
                'timezone': 'Etc/GMT-7',
                'settings': valid_settings
            },
            {
                'name': 'Test Nomenclature',
                'timezone': None,
                'settings': valid_settings
            },
            {
                'name': 'Test Nomenclature',
                'timezone': 'Etc/GMT-7',
                'settings': None
            }
        ]
        invalid_data += [
            {
                'name': 'Test Nomenclature',
                'timezone': 'Etc/GMT-7',
                'settings': settings
            } for settings in invalid_settings
        ]
        invalid_data += [
            {
                'name': 'Test Nomenclature',
                'timezone': 'Etc/GMT-7',
                'settings': settings
            } for settings in invalid_custom_settings
        ]
        for data in invalid_data:
            response = admin_client.post(
                self.no_detail_url_list[0],
                data=invalid_data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400. Данные:\n{data}'
            )
            nomenclature_count += 1
            assert nomenclature_count != Nomenclature.objects.count(), (
                f'Удалось создать репликацию с неправильными данными.'
            )
