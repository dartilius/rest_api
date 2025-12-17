import pytest

from datetime import datetime as dt, timedelta as td
from http import HTTPStatus
from random import randint, choices
from string import ascii_letters, digits
from uuid import uuid4

import tests.test_tasks
from nomenclatures.models import (
    Nomenclature,
    NomenclatureAvailability,
    StatusHistory,
    TIMEZONES
)


@pytest.mark.django_db
class TestNomenclaturesCRUD:

    nomenclature_list_url = '/api/nomenclatures/'
    nomenclature_detail_url = '/api/nomenclatures/{nomenclature_id}/'

    @staticmethod
    def check_get_nomenclature_list_response(nom_data, nom_count, response_data):
        assert nom_count == response_data['count'], (
            'Кол-во элементов в ответе не равно кол-ву репликаций в базе.'
        )
        for key in nom_data:
            assert key in response_data['results'][0], (
                f'Ответ не содержит ключ {key}.'
            )
            assert response_data['results'][0][key] == nom_data[key], (
                f'{key} номенклатуры в ответе не совпадает с '
                f'{key} номенклатуры в базе'
            )

    @staticmethod
    def check_get_nomenclature_detail_response(nom_data, response_data):
        for key in nom_data:
            assert key in response_data, (
                f'Ответ не содержит ключ {key}.'
            )
            assert response_data[key] == nom_data[key], (
                f'{key} номенклатуры в ответе не совпадает с '
                f'{key} номенклатуры в базе'
            )

    @staticmethod
    def get_valid_settings() -> dict:
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

        return valid_settings

    @staticmethod
    def get_valid_custom_settings() -> dict:
        custom_settings = TestNomenclaturesCRUD.get_valid_settings()
        for day in custom_settings:
            begin_time = f'{randint(9, 14)}:00:00'
            end_time = f'{randint(15, 20)}:00:00'
            custom_settings[day].update({
                'custom_volume': {
                    f'{begin_time}-{end_time}': [randint(0, 100)] * 4
                }
            })
        return custom_settings

    @staticmethod
    def get_invalid_settings() -> list[dict]:
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
        return invalid_settings

    @staticmethod
    def get_invalid_custom_settings() -> list[dict]:
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
        return invalid_custom_settings

    @staticmethod
    def get_valid_data() -> list[dict]:
        settings = TestNomenclaturesCRUD.get_valid_settings()
        custom_settings = TestNomenclaturesCRUD.get_valid_custom_settings()
        chars = ascii_letters + digits
        valid_data = [
            {
                'timezone': 'Etc/GMT-7',
                'settings': settings
            },
            {
                'timezone': 'Etc/GMT-7',
                'settings': custom_settings
            }
        ]
        for data in valid_data:
            data['name'] = ''.join(choices(chars, k=10))
            data['description'] = ''.join(choices(chars, k=30))
        return valid_data

    @staticmethod
    def get_valid_partial_update_data() -> list[dict]:
        valid_data = [
            {'name': 'new_name'},
            {'description': 'description'},
            {'timezone': 'Etc/GMT-3'},
            {'settings': {
                'fri': {'worktime': '09:00:00-20:00:00', 'default_volume': [70, 50, 70, 50]},
                'mon': {'worktime': '09:00:00-20:00:00', 'default_volume': [70, 50, 70, 50]},
                'sat': {'worktime': '09:00:00-20:00:00', 'default_volume': [70, 50, 70, 50]},
                'sun': {'worktime': '09:00:00-20:00:00', 'default_volume': [70, 50, 70, 50]},
                'thu': {'worktime': '09:00:00-20:00:00', 'default_volume': [70, 50, 70, 50]},
                'tue': {'worktime': '09:00:00-20:00:00', 'default_volume': [70, 50, 70, 50]},
                'wed': {'worktime': '09:00:00-20:00:00', 'default_volume': [70, 50, 70, 50]}
            }}
        ]
        return valid_data

    @staticmethod
    def check_create_response(nom_data, response_data, user):
        normal_keys = {'article', 'hw_info'}
        for key in nom_data:
            if key in normal_keys:
                assert key in response_data, f'{key} отсутствует в ответе.'
                assert response_data[key] == nom_data[key], (
                    f'{key} отличается от отправленных данных'
                )
            elif key == 'main_info':
                assert response_data['main_info']['name'] == nom_data['name'], (
                    'Название отличается от отправленных данных.'
                )
                assert response_data['main_info']['description'] == nom_data['description'], (
                    'Описание отличается от отправленных данных.'
                )
                assert response_data['main_info']['owner'] == user.full_name, (
                    'Создатель не встал в соответствующее поле.'
                )
                assert response_data['main_info']['timezone'] == TIMEZONES[nom_data['timezone']], (
                    'Часовой пояс отличается от отправленных данных.'
                )
            elif key == 'settings':
                check_settings = nom_data['settings']
                for day in check_settings:
                    if 'custom_volume' not in check_settings[day]:
                        check_settings[day]['custom_volume'] = {}
                assert response_data['settings'] == check_settings, (
                    'Настройки вещания отличаются от отправленных данных.'
                )

    @staticmethod
    def check_partial_update_response(data, response_data, updated_key):
        message = f'Поле {updated_key} не обновилось.\nОтвет: {response_data}'
        if updated_key == 'settings':
            check_settings = data['settings']
            for day in check_settings:
                if 'custom_volume' not in check_settings[day]:
                    check_settings[day]['custom_volume'] = {}
            assert response_data['settings'] == check_settings, message
        else:
            if updated_key == 'timezone':
                assert response_data['main_info'][updated_key] == TIMEZONES[data[updated_key]], message
            else:
                assert response_data['main_info'][updated_key] == data[updated_key], message

    def test_get_nomenclature_list_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        nomenclature,
        nomenclature_availability
    ):
        try:
            last_answer = f'{nomenclature.availability.last_answer_date:%Y-%m-%d %H:%M:%S}'
        except AttributeError:
            last_answer = 'Не выходила в сеть'
        try:
            status = nomenclature.availability.status
        except AttributeError:
            status = None
        nom_data = {
            'id': str(nomenclature.id),
            'article': nomenclature.article,
            'name': nomenclature.name,
            'timezone': TIMEZONES[nomenclature.timezone],
            'status': status,
            'last_answer': last_answer,
            'version': nomenclature.version
        }
        nom_count = Nomenclature.objects.count()
        clients = {admin_client: 'Сотрудник ТО',
                   manager_client: 'Менеджер',
                   superuser_client: 'Суперпользователь',
                   user_client: 'Авторизованный пользователь'}
        url = self.nomenclature_list_url
        for client in clients:
            response = client.get(url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'{clients[client]} не имеет доступ к странице.'
            )
            self.check_get_nomenclature_list_response(
                nom_data,
                nom_count,
                response_data
            )

    def test_get_nomenclature_list_anon(self, anon_client, nomenclature):
        response = anon_client.get(self.nomenclature_list_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Не авторизованный пользователь имеет доступ к странице.'
        )

    def test_get_nomenclature_detail_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        user,
        nomenclature,
        nomenclature_availability
    ):
        try:
            last_answer = f'{nomenclature.availability.last_answer_date:%Y-%m-%d %H:%M:%S}'
        except AttributeError:
            last_answer = 'Не выходила в сеть'
        try:
            status = nomenclature.availability.status
        except AttributeError:
            status = None
        settings = dict()
        for day, setting in nomenclature.settings.items():
            settings[day] = {
                'worktime': setting['worktime'],
                'default_volume': setting['default_volume'],
                'custom_volume': setting['custom_volume']
                if 'custom_volume' in setting else {}
            }
        nomenclature_id = str(nomenclature.id)
        nom_data = {
            'id': nomenclature_id,
            'article': nomenclature.article,
            'settings': settings,
            'main_info': {
                'name': nomenclature.name,
                'description': nomenclature.description,
                'owner': user.full_name,
                'timezone': TIMEZONES[nomenclature.timezone],
                'status': status,
                'last_answer': last_answer,
                'version': nomenclature.version,
                'created': f'{nomenclature.created:%Y-%m-%d %H:%M:%S}'
            },
            'hw_info': nomenclature.hw_info if nomenclature.hw_info else None
        }
        clients = {admin_client: 'Сотрудник ТО',
                   manager_client: 'Менеджер',
                   superuser_client: 'Суперпользователь',
                   user_client: 'Авторизованный пользователь'}
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        for client in clients:
            response = client.get(url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'{clients[client]} не имеет доступ к странице.'
            )
            self.check_get_nomenclature_detail_response(
                nom_data,
                response_data
            )

    def test_get_nomenclature_detail_anon(self, anon_client, nomenclature):
        url = self.nomenclature_detail_url.format(nomenclature_id=str(nomenclature.id))
        response = anon_client.get(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Не авторизованный пользователь имеет доступ к странице.'
        )

    def test_create_valid_nomenclature_admin(self, admin_client, admin_user,):
        nomenclature_count = Nomenclature.objects.count()
        valid_data = self.get_valid_data()
        for data in valid_data:
            response = admin_client.post(
                self.nomenclature_list_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201. Данные:\n{data}\nОтвет:{response_data}'
            )
            nomenclature_count += 1
            assert nomenclature_count == Nomenclature.objects.count(), (
                'Не удалось создать номенклатуру.'
            )
            self.check_create_response(data, response_data, admin_user)

    def test_create_valid_nomenclature_manager(self, manager_client, manager_user):
        nomenclature_count = Nomenclature.objects.count()
        valid_data = self.get_valid_data()
        for data in valid_data:
            response = manager_client.post(
                self.nomenclature_list_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201. Данные:\n{data}\nОтвет:{response_data}'
            )
            nomenclature_count += 1
            assert nomenclature_count == Nomenclature.objects.count(), (
                'Не удалось создать номенклатуру.'
            )
            self.check_create_response(data, response_data, manager_user)

    def test_create_valid_nomenclature_user(self, user_client):
        nomenclature_count = Nomenclature.objects.count()
        valid_data = self.get_valid_data()
        for data in valid_data:
            response = user_client.post(
                self.nomenclature_list_url,
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

    def test_create_valid_nomenclature_anon(self, anon_client):
        nomenclature_count = Nomenclature.objects.count()
        valid_data = self.get_valid_data()
        for data in valid_data:
            response = anon_client.post(
                self.nomenclature_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                'Код статуса в ответе != 401. Данные:\n{data}\nОтвет:{response.data}'
            )
            nomenclature_count += 1
            assert nomenclature_count != Nomenclature.objects.count(), (
                'Удалось создать номенклатуру без авторизации.'
            )

    def test_create_invalid_nomenclature(self, admin_client):
        valid_settings = self.get_valid_settings()
        invalid_settings = self.get_invalid_settings()
        invalid_custom_settings = self.get_invalid_custom_settings()
        nomenclature_count = Nomenclature.objects.count()
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
                self.nomenclature_list_url,
                data=invalid_data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400. Данные:\n{data}\nОтвет:{response.data}'
            )
            nomenclature_count += 1
            assert nomenclature_count != Nomenclature.objects.count(), (
                f'Удалось создать репликацию с неправильными данными.'
            )

    def test_valid_partial_update_nomenclature_admin(
        self,
        admin_client,
        nomenclature
    ):
        nomenclature_id = str(nomenclature.id)
        update_data = self.get_valid_partial_update_data()
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        for data in update_data:
            response = admin_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                'Код статуса в ответе != 200.'
                f'\nДанные: {data}\nОтвет: {response_data}'
            )
            updated_key = ''.join(data.keys())
            self.check_partial_update_response(data, response_data, updated_key)

    def test_valid_partial_update_nomenclature_manager(
        self,
        manager_client,
        nomenclature
    ):
        nomenclature_id = str(nomenclature.id)
        update_data = self.get_valid_partial_update_data()
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        for data in update_data:
            response = manager_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                'Код статуса в ответе != 200.'
                f'\nДанные: {data}\nОтвет: {response_data}'
            )
            updated_key = ''.join(data.keys())
            self.check_partial_update_response(data, response_data, updated_key)

    def test_valid_partial_update_nomenclature_user(self, user_client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        update_data = self.get_valid_partial_update_data()
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        for data in update_data:
            response = user_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                'Код статуса в ответе != 403.'
                f'\nДанные: {data}\nОтвет: {response_data}'
            )

    def test_valid_partial_update_nomenclature_anon(self, anon_client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        update_data = self.get_valid_partial_update_data()
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        for data in update_data:
            response = anon_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                'Код статуса в ответе != 401.'
                f'\nДанные: {data}\nОтвет: {response_data}'
            )

    def test_invalid_partial_update_nomenclature(self, admin_client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        invalid_settings = self.get_invalid_settings()
        invalid_custom_settings = self.get_invalid_custom_settings()
        invalid_data = [
            {'name': None},
            {'timezone': None},
            {'timezone': 'ololo'},
            {'settings': None}
        ]
        invalid_data += [{'settings': settings} for settings in invalid_settings]
        invalid_data += [{'settings': settings} for settings in invalid_custom_settings]
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        for data in invalid_data:
            response = admin_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                'Код статуса в ответе != 400.'
                f'\nДанные: {data}\nОтвет: {response_data}'
            )

    def test_update_nomenclature(self, admin_client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        settings = self.get_valid_settings()
        data = {
            'name': 'new_name',
            'description': 'description',
            'timezone': 'Etc/GMT-3',
            'settings': settings
        }
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        response = admin_client.put(url, data=data, format='json')
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
            f'Код статуса в ответе != 405.\nОтвет: {response.json()}'
        )

    def test_deactivate_nomenclature_staff(
        self,
        admin_client,
        manager_client,
        nomenclature
    ):
        nomenclature_id = str(nomenclature.id)
        clients = {admin_client: 'Сотрудник ТО', manager_client: 'Менеджер'}
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        for client in clients:
            response = client.delete(url)
            assert response.status_code == HTTPStatus.NO_CONTENT, (
                f'Код статуса в ответе != 204.\nОтвет: {response.json()}'
            )
            nom_obj = Nomenclature.objects.get(id=nomenclature_id)
            assert nom_obj.is_active is False, (
                f'{clients[client]} не смог деактивировать номенклатуру.'
            )
            nom_obj.is_active = True
            nom_obj.save(update_fields=['is_active'])

    def test_deactivate_nomenclature_user(self, user_client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        response = user_client.delete(url)
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            'Код статуса в ответе != 403.'
        )
        nom_obj = Nomenclature.objects.get(id=nomenclature_id)
        assert nom_obj.is_active is True, (
            f'Обычный пользователь смог деактивировать номенклатуру.'
        )

    def test_deactivate_nomenclature_anon(self, anon_client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        url = self.nomenclature_detail_url.format(nomenclature_id=nomenclature_id)
        response = anon_client.delete(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Код статуса в ответе != 401.'
        )
        nom_obj = Nomenclature.objects.get(id=nomenclature_id)
        assert nom_obj.is_active is True, (
            f'Неавторизованный пользователь смог деактивировать номенклатуру.'
        )


@pytest.mark.django_db(databases=['clickhouse', 'default'])
class TestNomenclatureActions:

    from ch_statistic.models import (
        ADStat,
        MusicStat,
        ImageStat,
        VideoStat,
        TickerStat
    )
    from tasks.models import Task

    status_history_url = '/api/nomenclatures/{nomenclature_id}/status_history/'
    pending_tasks_url = '/api/nomenclatures/{nomenclature_id}/pending_tasks/'
    send_tasks_url = '/api/nomenclatures/{nomenclature_id}/actions/'
    get_tasks_url = '/api/nomenclatures/{nomenclature_id}/tasks/'

    @staticmethod
    def update_nomenclature_status() -> None:
        statuses = NomenclatureAvailability.objects.all()
        statuses_to_update = []
        status_histories_to_create = []
        ONLINE = 0
        OFFLINE_5_MIN = 1
        OFFLINE_1_HOUR = 2

        for status in statuses:
            now_time = dt.now()
            new_status = ONLINE
            current_status = status.status
            last_answer = status.last_answer_date
            if current_status == ONLINE:
                if now_time - last_answer > td(hours=1):
                    new_status = OFFLINE_1_HOUR
                elif now_time - last_answer > td(minutes=5):
                    new_status = OFFLINE_5_MIN
                if new_status != current_status:
                    status.status = new_status
                    statuses_to_update.append(status)
                    status_histories_to_create.append(
                        StatusHistory(
                            status=new_status,
                            client=status.client
                        )
                    )

            if current_status == OFFLINE_5_MIN:
                new_status = OFFLINE_5_MIN
                if now_time - last_answer > td(hours=1):
                    new_status = OFFLINE_1_HOUR
                elif now_time - last_answer < td(minutes=5):
                    new_status = ONLINE
                if new_status != current_status:
                    status.status = new_status
                    statuses_to_update.append(status)
                    status_histories_to_create.append(
                        StatusHistory(
                            status=new_status,
                            client=status.client
                        )
                    )

            if current_status == OFFLINE_1_HOUR:
                if now_time - last_answer < td(minutes=5):
                    status.status = ONLINE
                    statuses_to_update.append(status)
                    status_histories_to_create.append(
                        StatusHistory(
                            status=new_status,
                            client=status.client
                        )
                    )

        NomenclatureAvailability.objects.bulk_update(statuses_to_update, ['status'])
        StatusHistory.objects.bulk_create(status_histories_to_create)

    @staticmethod
    def create_statistic(stat_type, nomenclature_id, stat_list):
        AdStat = TestNomenclatureActions.ADStat
        MusicStat = TestNomenclatureActions.MusicStat
        ImageStat = TestNomenclatureActions.ImageStat
        VideoStat = TestNomenclatureActions.VideoStat
        TickerStat = TestNomenclatureActions.TickerStat
        stat_objects = []
        match stat_type:
            case 'ad':
                model = AdStat
                for stat_element in stat_list:
                    stat_objects += [model(
                        client=nomenclature_id,
                        file=stat_element['file'],
                        played=stat_element['played'],
                        length=stat_element['length'],
                        ad_block=stat_element['ad_block']
                    )]
            case 'music':
                model = MusicStat
            case 'video':
                model = VideoStat
            case 'image':
                model = ImageStat
            case 'ticker':
                model = TickerStat
            case _:
                model = None

        if model:
            if stat_type != 'ad':
                for stat_element in stat_list:
                    stat_objects += [model(
                        client=nomenclature_id,
                        file=stat_element['file'],
                        played=stat_element['played'],
                        length=stat_element['length']
                    )]
            model.objects.bulk_create(stat_objects)

    @staticmethod
    def check_create_statistic(data, stat_type):
        ADStat = TestNomenclatureActions.ADStat
        MusicStat = TestNomenclatureActions.MusicStat
        ImageStat = TestNomenclatureActions.ImageStat
        VideoStat = TestNomenclatureActions.VideoStat
        TickerStat = TestNomenclatureActions.TickerStat
        match stat_type:
            case 'ad':
                stat_obj = ADStat.objects.last()
                assert (
                    data['statistic'][stat_type][0]['file'] == stat_obj.file
                ), 'Айди файла встал неправильно'
                assert (
                    data['statistic'][stat_type][0]['played'] ==
                    f'{stat_obj.played:%Y-%m-%d %H:%M:%S}'
                ), 'Время, когда сыграл файл, встало неправильно'
                assert (
                    data['statistic'][stat_type][0]['length'] ==
                    stat_obj.length
                ), 'Хронометраж файла встал неправильно'
                assert (
                    data['statistic']['ad'][0]['ad_block'] ==
                    stat_obj.ad_block
                ), 'Рекламный блок встал неправильно'
            case 'music':
                stat_obj = MusicStat.objects.last()
                assert (
                    data['statistic'][stat_type][0]['file'] == stat_obj.file
                ), 'Айди файла встал неправильно'
                assert (
                    data['statistic'][stat_type][0]['played'] ==
                    f'{stat_obj.played:%Y-%m-%d %H:%M:%S}'
                ), 'Время, когда сыграл файл, встало неправильно'
                assert (
                    data['statistic'][stat_type][0]['length'] ==
                    stat_obj.length
                ), 'Хронометраж файла встал неправильно'
            case 'image':
                stat_obj = ImageStat.objects.last()
                assert (
                    data['statistic'][stat_type][0]['file'] == stat_obj.file
                ), 'Айди файла встал неправильно'
                assert (
                    data['statistic'][stat_type][0]['played'] ==
                    f'{stat_obj.played:%Y-%m-%d %H:%M:%S}'
                ), 'Время, когда сыграл файл, встало неправильно'
                assert (
                    data['statistic'][stat_type][0]['length'] ==
                    stat_obj.length
                ), 'Хронометраж файла встал неправильно'
            case 'video':
                stat_obj = VideoStat.objects.last()
                assert (
                    data['statistic'][stat_type][0]['file'] == stat_obj.file
                ), 'Айди файла встал неправильно'
                assert (
                    data['statistic'][stat_type][0]['played'] ==
                    f'{stat_obj.played:%Y-%m-%d %H:%M:%S}'
                ), 'Время, когда сыграл файл, встало неправильно'
                assert (
                    data['statistic'][stat_type][0]['length'] ==
                    stat_obj.length
                ), 'Хронометраж файла встал неправильно'
            case 'ticker':
                stat_obj = TickerStat.objects.last()
                assert (
                    data['statistic'][stat_type][0]['file'] == stat_obj.file
                ), 'Айди файла встал неправильно'
                assert (
                    data['statistic'][stat_type][0]['played'] ==
                    f'{stat_obj.played:%Y-%m-%d %H:%M:%S}'
                ), 'Время, когда сыграл файл, встало неправильно'
                assert (
                    data['statistic'][stat_type][0]['length'] ==
                    stat_obj.length
                ), 'Хронометраж файла встал неправильно'

    @staticmethod
    def resend_orders(pk) -> dict:
        from api.constants import get_instance_or_404
        try:
            nomenclature = get_instance_or_404(Nomenclature, pk)
            is_adorders = nomenclature.adorders.filter(status__in=[0, 1]).count()
            is_bgorders = nomenclature.bgorders.filter(status__in=[0, 1]).count()
            if is_adorders == 0 and is_bgorders == 0:
                result_text = 'Нет активных заказов.'
                return {'data': result_text, 'status': HTTPStatus.OK}
            TestNomenclatureActions.resend_orders_task(pk)
            result_text = 'Запрос на переотправку заказов принят.'
            return {'data': result_text, 'status': HTTPStatus.CREATED}
        except Exception as e:
            return {'data': f'{type(e)}: {e}', 'status': HTTPStatus.BAD_REQUEST}

    @staticmethod
    def resend_orders_task(nomenclature_id: str) -> None:
        from itertools import chain
        from orders.models import AdOrder, BgOrder

        Task = TestNomenclatureActions.Task
        task_list = []
        AD = 4
        orders = chain(
            AdOrder.objects.filter(client=nomenclature_id, status__in=[0, 1]),
            BgOrder.objects.filter(client=nomenclature_id, status__in=[0, 1])
        )
        for order in orders:
            parameters = {
                'order_id': str(order.id),
                'broadcast_interval': f'{order.broadcast_interval.lower}-'
                                      f'{order.broadcast_interval.upper}',
                'playlist': {
                    'id': str(order.playlist.id),
                    'files': [
                        {
                            'id': str(file.id),
                            'hash': file.hash
                        } for file in order.playlist.files.all()
                    ]
                }
            }
            if isinstance(order, AdOrder):
                parameters.update({
                    'order_parameters': order.parameters,
                    'broadcast_type': order.broadcast_type,
                })
                parameters['playlist']['slides'] = (
                    order.slides if order.slides else None
                )
                task_type = AD
            else:
                parameters.update({'order_type': order.order_type})
                task_type = order.order_type
            task_list.append(
                Task(
                    owner=order.owner,
                    client=order.client,
                    type=task_type,
                    parameters=parameters
                )
            )
        Task.objects.bulk_create(task_list)

    @staticmethod
    def check_resend_orders_tasks(
        task_ids: list,
        adorder_id: str | None,
        bgorder_id: str | None,
        nom_id: str
    ):
        tasks = TestNomenclatureActions.Task.objects.filter(id__in=task_ids)
        for task in tasks:
            assert str(task.client.id) == nom_id, (
                'Репликацию ушла на другую машину.'
            )
            if task.type == 4:
                assert task.parameters['order_id'] == adorder_id, (
                    'В параметрах репликации указан не правильный айди заказа.'
                )
                assert task.parameters['broadcast_type'] == 0, (
                    'В параметрах репликации указан не верный тип вещания.'
                )
            else:
                assert task.parameters['order_id'] == bgorder_id, (
                    'В параметрах репликации указан не правильный айди заказа.'
                )
                assert task.parameters['order_type'] == 0, (
                    'В параметрах репликации указан не верный тип заказа.'
                )

    def test_get_status_history_auth(
        self,
        admin_client,
        manager_client,
        user_client,
        status_history
    ):
        nomenclature_id = str(status_history.client.id)
        clients = {admin_client: 'Сотрудник ТО',
                   manager_client: 'Менеджер',
                   user_client: 'Авторизованный пользователь'}
        for client in clients:
            response = admin_client.get(
                self.status_history_url.format(nomenclature_id=nomenclature_id)
            )
            assert response.status_code == HTTPStatus.OK, (
                f'{client} не может запросить историю доступности.'
            )
            response_data = response.json()
            for key in ('change_time', 'status'):
                assert key in response_data[0], (
                    f'В ответе нет обязательного ключа {key}.'
                )

    def test_get_status_history_anon(self, anon_client, status_history):
        nomenclature_id = str(status_history.client.id)
        response = anon_client.get(
            self.status_history_url.format(nomenclature_id=nomenclature_id)
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Не авторизованный пользователь может запросить историю доступности.'
        )

    def test_pending_tasks_create_status_history(self, client, nomenclature):
        status_history_count = StatusHistory.objects.count()
        url = self.pending_tasks_url.format(nomenclature_id=str(nomenclature.id))
        response = client.post(url, data={}, format='json')
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        self.update_nomenclature_status()
        status_history_count += 1
        assert status_history_count == StatusHistory.objects.count(), (
            'Не удалось создать запись об изменении статуса номенклатуры.'
        )

    def test_pending_tasks_update_nomenclature_version(self, client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        data = {'version': '1337'}
        url = self.pending_tasks_url.format(nomenclature_id=nomenclature_id)
        response = client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response.json()}.'
        )
        nom_obj = Nomenclature.objects.get(id=nomenclature_id)
        assert nom_obj.version == data['version'], (
            'Версия ПО встала неправильно.'
        )

    def test_pending_tasks_update_nomenclature_hw_info(self, client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        data = {
            'hw_info': {
                'model': 'Raspberry Pi 3 Model B Rev 1.2',
                'revision': 'a02082',
                'interfaces': [
                    {'ip': '172.31.170.227/27',
                     'mac': 'b8:27:eb:a4:d2:1f',
                     'iface': 'eth0'},
                    {'ip': '',
                     'mac': 'b8:27:eb:f1:87:4a',
                     'iface': 'wlan0'}
                ],
                'audiodevices': [
                    {'card': 0, 'name': 'bcm2835 HDMI 1'},
                    {'card': 1, 'name': 'bcm2835 Headphones'}
                ],
                'sd_card_data': {'name': 'SD32G', 'manf_id': '0x000027'},
                'serial_number': '0000000067a4d21f'
            }
        }
        url = self.pending_tasks_url.format(nomenclature_id=nomenclature_id)
        response = client.post(
            url,
            data=data,
            format='json',
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response.json()}.'
        )
        nom_obj = Nomenclature.objects.get(id=nomenclature_id)
        assert nom_obj.hw_info == data['hw_info'], (
            'Информация о железе встала неправильно.'
        )

    def test_pending_tasks_update_nomenclature_hw_info_and_version(
        self,
        client,
        nomenclature
    ):
        nomenclature_id = str(nomenclature.id)
        data = {
            'hw_info': {
                'model': 'Raspberry Pi 3 Model B Rev 1.2',
                'revision': 'a02082',
                'interfaces': [
                    {'ip': '172.31.170.227/27',
                     'mac': 'b8:27:eb:a4:d2:1f',
                     'iface': 'eth0'},
                    {'ip': '',
                     'mac': 'b8:27:eb:f1:87:4a',
                     'iface': 'wlan0'}
                ],
                'audiodevices': [
                    {'card': 0, 'name': 'bcm2835 HDMI 1'},
                    {'card': 1, 'name': 'bcm2835 Headphones'}
                ],
                'sd_card_data': {'name': 'SD32G', 'manf_id': '0x000027'},
                'serial_number': '0000000067a4d21f'
            },
            'version': '1337'
        }
        url = self.pending_tasks_url.format(nomenclature_id=nomenclature_id)
        response = client.post(
            url,
            data=data,
            format='json',
            content_type='application/json'
        )
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response.json()}.'
        )
        nom_obj = Nomenclature.objects.get(id=nomenclature_id)
        assert nom_obj.hw_info == data['hw_info'], (
            'Информация о железе встала неправильно.'
        )
        assert nom_obj.version == data['version'], (
            'Версия ПО встала неправильно.'
        )

    def test_pending_tasks_create_nomenclature_availability(
        self,
        client,
        nomenclature
    ):
        availability_count = NomenclatureAvailability.objects.count()
        url = self.pending_tasks_url.format(nomenclature_id=str(nomenclature.id))
        response = client.post(url, data={})
        assert response.status_code == HTTPStatus.OK, (
            'Код статуса в ответе != 200.'
        )
        availability_count += 1
        assert availability_count == NomenclatureAvailability.objects.count(), (
            'Запись о доступности номенклатуры не была создана при получении запроса.'
        )

    def test_pending_tasks_update_nomenclature_availability(
        self,
        client,
        nomenclature,
        nomenclature_availability
    ):
        import time
        initial_last_answer = f'{nomenclature_availability.last_answer_date:%Y-%m-%d %H:%M:%S}'
        time.sleep(2)
        url = self.pending_tasks_url.format(nomenclature_id=str(nomenclature.id))
        response = client.post(url, data={})
        assert response.status_code == HTTPStatus.OK, (
            'Код статуса в ответе != 200.'
        )
        current_last_answer = f'{NomenclatureAvailability.objects.last().last_answer_date:%Y-%m-%d %H:%M:%S}'
        assert initial_last_answer != current_last_answer, (
            'Время последнего выхода в доступ номенклатуры встало неправильно. '
        )

    def test_pending_tasks_returns_pending_tasks(self, client, nomenclature, task):
        task_id = str(task.id)
        data = {}
        url = self.pending_tasks_url.format(nomenclature_id=str(nomenclature.id))
        response = client.post(url, data=data, format='json')
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response_data}'
        )
        check_response = {
            'tasks': [
                {'task_id': task_id,
                 'task_type': task.type,
                 'parameters': task.parameters}
            ]
        }
        assert response_data == check_response, (
            'Репликации ожидающие обработки не были отправлены в ответ на запрос'
        )

    def test_pending_tasks_update_task_status(self, client, nomenclature, task):
        task_id = str(task.id)
        data = {
            'task_status': {task_id: 2}
        }
        url = self.pending_tasks_url.format(nomenclature_id=str(nomenclature.id))
        response = client.post(
            url,
            data=data,
            format='json',
            content_type='application/json'
        )
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response_data}'
        )
        task_obj = self.Task.objects.get(id=task_id)
        assert task_obj.status == data['task_status'][task_id], (
            'Статус репликации не изменился'
        )

    def test_pending_tasks_create_statistic(self, client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        stat_data = [
            {'statistic': {'ad': [{'file': f'{uuid4()}',
                                   'played': f'{dt.now().date()} 00:00:{randint(10, 59)}',
                                   'length': randint(15, 59),
                                   'ad_block': randint(1, 12)}]}},
            {'statistic': {'music': [{'file': f'{uuid4()}',
                                      'played': f'{dt.now().date()} 00:00:{randint(10, 59)}',
                                      'length': randint(15, 59)}]}},
            {'statistic': {'image': [{'file': f'{uuid4()}',
                                      'played': f'{dt.now().date()} 00:00:{randint(10, 59)}',
                                      'length': randint(15, 59)}]}},
            {'statistic': {'video': [{'file': f'{uuid4()}',
                                      'played': f'{dt.now().date()} 00:00:{randint(10, 59)}',
                                      'length': randint(15, 59)}]}},
            {'statistic': {'ticker': [{'file': f'{uuid4()}',
                                       'played': f'{dt.now().date()} 00:00:{randint(10, 59)}',
                                       'length': randint(15, 59)}]}}
        ]
        for data in stat_data:
            stat_type, stat_list = next(iter(data['statistic'].items()))
            self.create_statistic(stat_type, nomenclature_id, stat_list)
            self.check_create_statistic(data, stat_type)

    def test_resend_adorder(self, admin_client, nomenclature, adorder):
        task_count = self.Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        response = self.resend_orders(nomenclature_id)
        assert response['status'] == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nОтвет: {response["data"]}'
        )
        task_count += 1
        assert task_count == self.Task.objects.count(), (
            'Репликация на переотправку не создалась.'
        )
        task_id = self.Task.objects.last().id
        self.check_resend_orders_tasks(task_ids=[task_id],
                                       adorder_id=str(adorder.id),
                                       bgorder_id=None,
                                       nom_id=nomenclature_id)

    def test_resend_bgorder(self, admin_client, nomenclature, bgorder):
        task_count = self.Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        response = self.resend_orders(nomenclature_id)
        assert response['status'] == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nОтвет: {response["data"]}'
        )
        task_count += 1
        assert task_count == self.Task.objects.count(), (
            'Репликация на переотправку не создалась.'
        )
        task_id = self.Task.objects.last().id
        self.check_resend_orders_tasks(task_ids=[task_id],
                                       adorder_id=None,
                                       bgorder_id=str(bgorder.id),
                                       nom_id=nomenclature_id)

    def test_resend_orders(
        self,
        admin_client,
        nomenclature,
        adorder,
        bgorder
    ):
        task_count = self.Task.objects.count()
        nomenclature_id = str(nomenclature.id)
        response = self.resend_orders(nomenclature_id)
        assert response['status'] == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nОтвет: {response["data"]}'
        )
        task_count += 2
        assert task_count == self.Task.objects.count(), (
            'Репликации на переотправку не создались.'
        )
        task_ids = [task.id
                    for task
                    in self.Task.objects.all()]
        self.check_resend_orders_tasks(task_ids=task_ids,
                                       adorder_id=str(adorder.id),
                                       bgorder_id=str(bgorder.id),
                                       nom_id=nomenclature_id)

    def test_valid_send_tasks(self, admin_client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        task_data = [
            {'task': 'reboot'},
            {'task': 'update'},
            {'task': 'custom',
             'parameters': 'test'},
            {'task': 'settings',
             'parameters': TestNomenclaturesCRUD.get_valid_custom_settings()}
        ]
        url = self.send_tasks_url.format(nomenclature_id=nomenclature_id)
        for data in task_data:
            response = admin_client.post(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Код статуса в ответе != 200.'
                f'\nДанные: {data}.\nОтвет: {response_data}'
            )

    def test_invalid_send_tasks(self, admin_client, nomenclature):
        nomenclature_id = str(nomenclature.id)
        invalid_data = [
            {'task': 'invalid_task'},
            {'task': None},
            {'task': 'custom',
             'parameters': None},
            {'task': 'custom'},
            {'task': 'settings',
             'parameters': TestNomenclaturesCRUD.get_invalid_settings()[0]},
            {'task': 'settings',
             'parameters': TestNomenclaturesCRUD.get_invalid_custom_settings()[0]},
            {'task': 'settings'},
            {'task': 'settings',
             'parameters': None},
        ]
        url = self.send_tasks_url.format(nomenclature_id=nomenclature_id)
        for data in invalid_data:
            response = admin_client.post(url, data=data, format='json')
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400.\nДанные: {data}'
            )

    def test_get_tasks(self, admin_client, user, nomenclature, task):
        nomenclature_id = str(nomenclature.id)
        task_data = {
            'id': str(task.id),
            'owner': user.full_name,
            'client': {'id': str(task.client.id), 'name': task.client.name},
            'type': task.type,
            'status': task.status
        }
        url = self.get_tasks_url.format(nomenclature_id=nomenclature_id)
        response = admin_client.get(url)
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет:{response_data}'
        )
        tests.test_tasks.TestTasks().check_get_list_response(
            task_data,
            1,
            response_data
        )


@pytest.mark.django_db(databases=['clickhouse', 'default'])
class TestNomenclatureStatistic:

    ad_stat_url = '/api/nomenclatures/{nomenclature_id}/ad_stat?date={date}'
    bg_stat_url_list = [
        '/api/nomenclatures/{nomenclature_id}/music_stat/',
        '/api/nomenclatures/{nomenclature_id}/image_stat/',
        '/api/nomenclatures/{nomenclature_id}/video_stat/',
        '/api/nomenclatures/{nomenclature_id}/ticker_stat/'
    ]

    def test_get_statistics_staff(
        self,
        admin_client,
        manager_client,
        nomenclature,
        ad_stat,
        music_stat,
        image_stat,
        video_stat,
        ticker_stat
    ):
        nomenclature_id = str(nomenclature.id)
        date = dt.today().date()
        ad_url = self.ad_stat_url.format(nomenclature_id=nomenclature_id, date=date)
        response = admin_client.get(ad_url, follow=True)
        assert response.status_code == HTTPStatus.OK, (
            f'Сотрудник ТО не может запросить статистику рекламы.'
        )
        response_data = response.json()
        for key in ('ad_block', 'file', 'length'):
            assert key in response_data[0], f'В ответе нет обязательного ключа {key}'
        for url in self.bg_stat_url_list:
            response = admin_client.get(
                url.format(nomenclature_id=nomenclature_id, date=date),
                follow=True
            )
            assert response.status_code == HTTPStatus.OK, (
                f'Сотрудник ТО не может запросить статистику {url.split("/")[-1]}.'
            )
            response_data = response.json()
            assert 'results' in response_data, f'В ответе нет обязательного ключа "results"'
            for key in ('played', 'file', 'length'):
                assert key in response_data['results'][0], f'В ответе нет обязательного ключа {key}'

        response = manager_client.get(ad_url, follow=True)
        assert response.status_code == HTTPStatus.OK, (
            f'Менеджер не может запросить статистику рекламы.'
        )
        response_data = response.json()
        for key in ('ad_block', 'file', 'length'):
            assert key in response_data[0], f'В ответе нет обязательного ключа {key}'
        for url in self.bg_stat_url_list:
            response = manager_client.get(
                url.format(nomenclature_id=nomenclature_id, date=date),
                follow=True
            )
            assert response.status_code == HTTPStatus.OK, (
                f'Менеджер не может запросить статистику {url.split("/")[-1]}.'
            )
            response_data = response.json()
            assert 'results' in response_data, f'В ответе нет обязательного ключа "results"'
            for key in ('played', 'file', 'length'):
                assert key in response_data['results'][0], f'В ответе нет обязательного ключа {key}'

    def test_get_statistics_user(
        self,
        user_client,
        nomenclature,
        ad_stat,
        music_stat,
        image_stat,
        video_stat,
        ticker_stat
    ):
        nomenclature_id = str(nomenclature.id)
        date = dt.today().date()
        url = self.ad_stat_url.format(nomenclature_id=nomenclature_id, date=date)
        response = user_client.get(url, follow=True)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не может запросить статистику рекламы.'
        )
        response_data = response.json()
        for key in ('ad_block', 'file', 'length'):
            assert key in response_data[0], f'В ответе нет обязательного ключа {key}'
        for url in self.bg_stat_url_list:
            response = user_client.get(
                url.format(nomenclature_id=nomenclature_id),
                follow=True
            )
            assert response.status_code == HTTPStatus.OK, (
                f'Авторизованный пользователь не может запросить статистику {url.split("/")[-1]}.'
            )
            response_data = response.json()
            assert 'results' in response_data, f'В ответе нет обязательного ключа "results"'
            for key in ('played', 'file', 'length'):
                assert key in response_data['results'][0], f'В ответе нет обязательного ключа {key}'

    def test_get_statistics_anon(
        self,
        anon_client,
        nomenclature,
        ad_stat,
        music_stat,
        image_stat,
        video_stat,
        ticker_stat
    ):
        nomenclature_id = str(nomenclature.id)
        date = dt.today().date()
        url = self.ad_stat_url.format(nomenclature_id=nomenclature_id, date=date)
        response = anon_client.get(url, follow=True)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Не авторизованный пользователь может запросить статистику рекламы.'
        )
        for url in self.bg_stat_url_list:
            response = anon_client.get(
                url.format(nomenclature_id=nomenclature_id, date=date),
                follow=True
            )
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Не авторизованный пользователь может запросить статистику {url}.'
            )
