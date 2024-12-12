import copy
import pytest

from datetime import datetime as dt
from http import HTTPStatus
from random import randint, choices
from string import ascii_letters, digits

from nomenclatures.models import Nomenclature, NomenclatureAvailability, TIMEZONES


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
        from random import randint
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

    status_history_url = '/api/nomenclatures/{nomenclature_id}/status_history/'
    pending_tasks_url = '/api/nomenclatures/{nomenclature_id}/pending_tasks/'

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

    def test_create_nomenclature_availability_with_pending_tasks(
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

    def test_update_nomenclature_availability_with_pending_tasks(
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
