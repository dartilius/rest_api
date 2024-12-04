import pytest

from datetime import datetime as dt, timedelta as td
from http import HTTPStatus
from itertools import product

from orders.models import AdOrder, BgOrder


@pytest.mark.django_db
class TestOrders:

    ad_list_url = '/api/adorders/'
    ad_detail_url = '/api/adorders/{adorder}/'
    ad_cancel_url = '/api/adorders/{adorder}/cancel/'
    bg_list_url = '/api/bgorders/'
    bg_detail_url = '/api/bgorders/{bgorder}/'
    bg_cancel_url = '/api/bgorders/{bgorder}/cancel/'

    @staticmethod
    def get_today_date() -> str:
        return f'{dt.today().date()} 09:00:00'

    @staticmethod
    def get_tomorrow_date() -> str:
        return f'{dt.today().date() + td(days=1)} 20:00:00'

    @staticmethod
    def get_new_tomorrow_date() -> str:
        return f'{dt.today().date() + td(days=2)} 20:00:00'

    @staticmethod
    def get_valid_adorder_data(nomenclature_id, playlist_id) -> list:
        today = TestOrders.get_today_date()
        tomorrow = TestOrders.get_tomorrow_date()
        valid_data = [
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 1,
                'parameters': {'times_in_hour': 4, 'timedelta': '01:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 2,
                'parameters': {'times_in_hour': 4, 'timedelta': '01:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '12:00:00',
                               'daily_end_time': '16:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 4,
                'parameters': {'times_in_hour': 4,
                               'daily_end_time': '12:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 5,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '18:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'event': 'click',
                               'active_ad': 'stop'}
            }],
        ]
        return valid_data

    @staticmethod
    def get_valid_bgorder_data(
            nomenclature,
            playlist_1,
            playlist_2,
            playlist_3,
            playlist_4
    ) -> list:
        today = TestOrders.get_today_date()
        tomorrow = TestOrders.get_tomorrow_date()
        nomenclature_id = str(nomenclature.id)
        playlist_1_id = str(playlist_1.id)
        playlist_2_id = str(playlist_2.id)
        playlist_3_id = str(playlist_3.id)
        playlist_4_id = str(playlist_4.id)
        valid_data = [
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_1_id,
                'order_type': 0,
                'parameters': {'test': 'test'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_2_id,
                'order_type': 1,
                'parameters': {'test': 'test'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_3_id,
                'order_type': 2,
                'parameters': {'test': 'test'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_4_id,
                'order_type': 3,
                'parameters': {'test': 'test'}
            }]
        ]
        return valid_data

    @staticmethod
    def check_valid_create_adorder_response(data, user, response) -> None:
        check_params = data[0]['parameters']
        if 'timedelta' in check_params:
            timedelta = check_params['timedelta']
            timedelta = list(map(int, timedelta.split(':')))
            check_params.update({'timedelta': timedelta})
        if 'daily_start_time' in check_params:
            start_time = check_params.pop('daily_start_time')
            start_time = list(map(int, start_time.split(':')))
            check_params.update({'start_time': start_time})
        if 'daily_end_time' in check_params:
            end_time = check_params.pop('daily_end_time')
            end_time = list(map(int, end_time.split(':')))
            check_params.update({'end_time': end_time})
        check_params.update({'weight': 50})
        assert response[0][0]['owner'] == user.full_name, (
            'Создатель заказа не встал в соответствующее поле.'
        )
        assert (
                response[0][0]['client']['id'] == data[0]['clients'][0]
        ), (
            'Целевая рабочая станция созданного заказа отличается от '
            'таковой в отправленных данных.'
        )
        assert (
                response[0][0]['playlist']['id'] == data[0]['playlist']
        ), (
            'Плейлист созданного заказа отличается от указанного '
            'в отправленных данных.'
        )
        assert (
                response[0][0]['broadcast_type']
                == data[0]['broadcast_type']
        ), (
            'Режим вещания заказа отличается от указанного '
            'в отправленных данных.'
        )
        assert response[0][0]['parameters'] == check_params, (
            'Параметры заказа отличаются от отправленных данных.'
        )
        check_params.clear()

    @staticmethod
    def check_valid_create_bgorder_response(data, user, response) -> None:

        assert response[0][0]['owner'] == user.full_name, (
            'Создатель заказа не встал в соответствующее поле.'
        )
        assert (
                response[0][0]['client']['id'] == data[0]['clients'][0]
        ), (
            'Целевая рабочая станция созданного заказа отличается от '
            'таковой в отправленных данных.'
        )
        assert (
                response[0][0]['playlist']['id'] == data[0]['playlist']
        ), (
            'Плейлист созданного заказа отличается от указанного '
            'в отправленных данных.'
        )
        assert (
                response[0][0]['order_type'] == data[0]['order_type']
        ), 'Тип заказа отличается от указанного в отправленных данных.'

    @staticmethod
    def get_valid_partial_update_adorder_data(
            playlist_id,
            file_1_id,
            file_2_id
    ) -> list:
        valid_data = [
            {'name': 'new_name'},
            {'description': 'description'},
            {'playlist': playlist_id},
            {'slides': {file_1_id: [file_2_id]}}
        ]
        return valid_data

    @staticmethod
    def get_valid_partial_update_bgorder_data(playlist_id) -> list:
        valid_data = [
            {'name': 'new_name'},
            {'description': 'description'},
            {'playlist': playlist_id}
        ]
        return valid_data

    @staticmethod
    def check_valid_update_response(data, response, updated_key):
        message = f'Поле {updated_key} не обновилось.\nОтвет: {response}'
        normal_keys = ('name', 'description')
        if updated_key in normal_keys:
            assert response[updated_key] == data[updated_key], message
        match updated_key:
            case 'playlist':
                assert response['playlist']['id'] == data['playlist'], message
            case 'slides':
                assert response['slides'].keys() == data['slides'].keys(), message
            case _: pass

    def test_chain_list_or_instance(self, playlist_1, adorder, bgorder):
        from itertools import chain
        from django.core.exceptions import ValidationError
        pls_list = [playlist_1]
        try:
            orders_list = chain(AdOrder.objects.filter(playlist=pls_list),
                                BgOrder.objects.filter(playlist=pls_list))
        except ValidationError:
            orders_list = chain(AdOrder.objects.filter(playlist__in=pls_list),
                                BgOrder.objects.filter(playlist__in=pls_list))
        list_chain = len(list(orders_list))
        assert list_chain == 2, f'{list_chain}'

    def test_availability_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        adorder,
        bgorder
    ):
        urls = [
            self.ad_list_url,
            self.bg_list_url,
            self.ad_detail_url.format(adorder=str(adorder.id)),
            self.bg_detail_url.format(bgorder=str(bgorder.id)),
        ]
        clients = [admin_client, manager_client, superuser_client, user_client]
        for combo in product(clients, urls):
            response = combo[0].get(combo[1])
            assert response.status_code == HTTPStatus.OK, (
                f'Пользователь {combo[0]} не имеет доступ к странице {combo[1]}.'
            )

    def test_availability_anon(self, anon_client, adorder, bgorder):
        urls = [
            self.ad_list_url,
            self.bg_list_url,
            self.ad_detail_url.format(adorder=str(adorder.id)),
            self.bg_detail_url.format(bgorder=str(bgorder.id)),
        ]
        for url in urls:
            response = anon_client.get(url)
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Не авторизованный пользователь имеет доступ к странице {url}.'
            )

    def test_create_valid_adorder_admin(
        self,
        admin_client,
        admin_user,
        nomenclature,
        playlist_1
    ):
        nomenclature_id = str(nomenclature.id)
        playlist_id = str(playlist_1.id)
        valid_data = self.get_valid_adorder_data(nomenclature_id, playlist_id)
        for data in valid_data:
            adorder_count = AdOrder.objects.count()
            response = admin_client.post(
                self.ad_list_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nДанные: {data}\nОтвет: {response_data}.'
            )
            adorder_count += 1
            assert adorder_count == AdOrder.objects.count(), (
                f'Не удалось создать рекламный заказ.'
            )
            self.check_valid_create_adorder_response(data, admin_user, response_data)

    def test_create_valid_adorder_manager(
        self,
        manager_client,
        manager_user,
        nomenclature,
        playlist_1
    ):
        nomenclature_id = str(nomenclature.id)
        playlist_id = str(playlist_1.id)
        valid_data = self.get_valid_adorder_data(nomenclature_id, playlist_id)
        for data in valid_data:
            adorder_count = AdOrder.objects.count()
            response = manager_client.post(
                self.ad_list_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nДанные: {data}\nОтвет: {response_data}.'
            )
            adorder_count += 1
            assert adorder_count == AdOrder.objects.count(), (
                f'Не удалось создать рекламный заказ.'
            )
            self.check_valid_create_adorder_response(data, manager_user, response_data)

    def test_create_valid_adorder_user(
        self,
        user_client,
        nomenclature,
        playlist_1
    ):

        adorder_count = AdOrder.objects.count()
        nomenclature_id = str(nomenclature.id)
        playlist_id = str(playlist_1.id)
        valid_data = self.get_valid_adorder_data(nomenclature_id, playlist_id)
        for data in valid_data:
            response = user_client.post(
                self.ad_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                f'Код статуса в ответе != 403.'
            )
            adorder_count += 1
            assert adorder_count != AdOrder.objects.count(), (
                f'Удалось создать рекламный заказ без должных прав.'
            )

    def test_create_valid_adorder_anon(
        self,
        anon_client,
        nomenclature,
        playlist_1
    ):
        adorder_count = AdOrder.objects.count()
        nomenclature_id = str(nomenclature.id)
        playlist_id = str(playlist_1.id)
        valid_data = self.get_valid_adorder_data(nomenclature_id, playlist_id)
        for data in valid_data:
            response = anon_client.post(
                self.ad_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Код статуса в ответе != 401.'
            )
            adorder_count += 1
            assert adorder_count != AdOrder.objects.count(), (
                f'Удалось создать рекламный заказ без авторизации.'
            )

    def test_create_invalid_adorder(
        self,
        admin_client,
        nomenclature,
        playlist_1
    ):
        adorder_count = AdOrder.objects.count()
        nomenclature_id = str(nomenclature.id)
        playlist_id = str(playlist_1.id)
        today = TestOrders.get_today_date()
        tomorrow = TestOrders.get_tomorrow_date()
        invalid_data = [
            [{
                'name': None,
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': tomorrow, 'upper': today},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': 'nomenclature.id',
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': 'playlist.id',
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 7,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 5}
            }],
            [{
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4, 'weight': 111}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 1,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 1,
                'parameters': {'times_in_hour': 4, 'timedelta': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 2,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 2,
                'parameters': {'times_in_hour': 4, 'timedelta': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4, 'daily_start_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4, 'daily_end_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '01:00:00',
                               'daily_end_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': 1,
                               'daily_end_time': '01:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '09:00:00',
                               'daily_end_time': '08:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '09:00:00',
                               'daily_end_time': '24:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 4,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 4,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 4,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '24:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 5,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 5,
                'parameters': {'times_in_hour': 4,
                               'daily_end_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 5,
                'parameters': {'times_in_hour': 4,
                               'daily_end_time': '24:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'event': 'click'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'active_ad': 'skip'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'event': 'invalid_event',
                               'active_ad': 'skip'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'event': 'click',
                               'active_ad': 'invalid_behavior'}
            }],
        ]
        for data in invalid_data:
            response = admin_client.post(
                self.ad_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400: {data}.'
            )
            adorder_count += 1
            assert adorder_count != AdOrder.objects.count(), (
                f'Удалось создать неправильный рекламный заказ.'
            )

    def test_create_valid_bgorder_admin(
        self,
        admin_client,
        admin_user,
        nomenclature,
        playlist_1,
        playlist_2,
        playlist_3,
        playlist_4
    ):
        valid_data = self.get_valid_bgorder_data(
            nomenclature,
            playlist_1,
            playlist_2,
            playlist_3,
            playlist_4
        )
        for data in valid_data:
            bgorder_count = BgOrder.objects.count()
            response = admin_client.post(
                self.bg_list_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nДанные: {data}\nОтвет:{response_data}'
            )
            bgorder_count += 1
            assert bgorder_count == BgOrder.objects.count(), (
                f'Не удалось создать рекламный заказ.'
            )
            self.check_valid_create_bgorder_response(data, admin_user, response_data)

    def test_create_valid_bgorder_manager(
        self,
        manager_client,
        manager_user,
        nomenclature,
        playlist_1,
        playlist_2,
        playlist_3,
        playlist_4
    ):
        valid_data = self.get_valid_bgorder_data(
            nomenclature,
            playlist_1,
            playlist_2,
            playlist_3,
            playlist_4
        )
        for data in valid_data:
            bgorder_count = BgOrder.objects.count()
            response = manager_client.post(
                self.bg_list_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nДанные: {data}\nОтвет:{response_data}'
            )
            bgorder_count += 1
            assert bgorder_count == BgOrder.objects.count(), (
                f'Не удалось создать рекламный заказ.'
            )
            self.check_valid_create_bgorder_response(data, manager_user, response_data)

    def test_create_valid_bgorder_user(
        self,
        user_client,
        nomenclature,
        playlist_1,
        playlist_2,
        playlist_3,
        playlist_4
    ):
        bgorder_count = BgOrder.objects.count()
        valid_data = self.get_valid_bgorder_data(
            nomenclature,
            playlist_1,
            playlist_2,
            playlist_3,
            playlist_4
        )
        for data in valid_data:
            response = user_client.post(
                self.bg_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                'Код статуса в ответе != 403.'
            )
            bgorder_count += 1
            assert bgorder_count != BgOrder.objects.count(), (
                f'Удалось создать рекламный заказ без должных прав.'
            )

    def test_create_valid_bgorder_anon(
        self,
        anon_client,
        nomenclature,
        playlist_1,
        playlist_2,
        playlist_3,
        playlist_4
    ):
        bgorder_count = BgOrder.objects.count()
        valid_data = self.get_valid_bgorder_data(
            nomenclature,
            playlist_1,
            playlist_2,
            playlist_3,
            playlist_4
            )
        for data in valid_data:
            response = anon_client.post(
                self.bg_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                'Код статуса в ответе != 401.'
            )
            bgorder_count += 1
            assert bgorder_count != BgOrder.objects.count(), (
                f'Удалось создать рекламный заказ без авторизации.'
            )

    def test_create_invalid_bgorder(
        self,
        admin_client,
        nomenclature,
        playlist_1
    ):
        bgorder_count = BgOrder.objects.count()
        nomenclature_id = str(nomenclature.id)
        playlist_id = str(playlist_1.id)
        today = TestOrders.get_today_date()
        tomorrow = TestOrders.get_tomorrow_date()
        invalid_data = [
            [{
                'name': None,
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': None,
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': None,
                'playlist': playlist_id,
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': None,
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'order_type': None
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': tomorrow, 'upper': today},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [nomenclature_id],
                'playlist': playlist_id,
                'order_type': 1
            }]
        ]
        for data in invalid_data:
            response = admin_client.post(
                self.bg_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400: {data}.'
            )
            bgorder_count += 1
            assert bgorder_count != BgOrder.objects.count(), (
                'Удалось создать неправильный рекламный заказ.'
            )

    def test_valid_partial_update_adorder_admin(
        self,
        admin_client,
        adorder_slides,
        nomenclature_1,
        playlist_5,
        file_2,
        file_5
    ):
        playlist_5_id = str(playlist_5.id)
        track_id = str(file_5.id)
        slide_id = str(file_2.id)
        update_data = TestOrders.get_valid_partial_update_adorder_data(
            playlist_5_id,
            track_id,
            slide_id
        )
        adorder_id = str(adorder_slides.id)
        url = self.ad_detail_url.format(adorder=adorder_id)
        for data in update_data:
            response = admin_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Код статуса в ответе != 200.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )
            updated_key = ''.join(data.keys())
            self.check_valid_update_response(data, response_data, updated_key)

    def test_valid_partial_update_adorder_manager(
        self,
        manager_client,
        adorder_slides,
        nomenclature_1,
        playlist_5,
        file_2,
        file_5
    ):
        playlist_5_id = str(playlist_5.id)
        track_id = str(file_5.id)
        slide_id = str(file_2.id)
        update_data = TestOrders.get_valid_partial_update_adorder_data(
            playlist_5_id,
            track_id,
            slide_id
        )
        adorder_id = str(adorder_slides.id)
        url = self.ad_detail_url.format(adorder=adorder_id)
        for data in update_data:
            response = manager_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Код статуса в ответе != 200.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )
            updated_key = ''.join(data.keys())
            self.check_valid_update_response(data, response_data, updated_key)

    def test_valid_partial_update_adorder_user(
        self,
        user_client,
        adorder_slides,
        nomenclature_1,
        playlist_5,
        file_2,
        file_5
    ):
        playlist_5_id = str(playlist_5.id)
        track_id = str(file_5.id)
        slide_id = str(file_2.id)
        update_data = TestOrders.get_valid_partial_update_adorder_data(
            playlist_5_id,
            track_id,
            slide_id
        )
        adorder_id = str(adorder_slides.id)
        url = self.ad_detail_url.format(adorder=adorder_id)
        for data in update_data:
            response = user_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                f'Код статуса в ответе != 403.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )

    def test_valid_partial_update_adorder_anon(
        self,
        anon_client,
        adorder_slides,
        nomenclature_1,
        playlist_5,
        file_2,
        file_5
    ):
        playlist_5_id = str(playlist_5.id)
        track_id = str(file_5.id)
        slide_id = str(file_2.id)
        update_data = TestOrders.get_valid_partial_update_adorder_data(
            playlist_5_id,
            track_id,
            slide_id
        )
        adorder_id = str(adorder_slides.id)
        url = self.ad_detail_url.format(adorder=adorder_id)
        for data in update_data:
            response = anon_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Код статуса в ответе != 401.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )

    def test_invalid_partial_update_adorder(
        self,
        admin_client,
        user,
        adorder_slides,
        nomenclature_1,
        playlist_5,
        file_2,
        file_3,
        file_4
    ):
        today = TestOrders.get_today_date()
        new_end = TestOrders.get_new_tomorrow_date()
        nomenclature_id = str(nomenclature_1.id)
        user_id = str(user.id)
        invalid_data = [
            {'name': None},
            {'clients': [nomenclature_id]},
            {'clients': None},
            {'owner': user_id},
            {'owner': None},
            {'broadcast_interval': {'lower': today, 'upper': new_end}},
            {'broadcast_interval': {'lower': 'today', 'upper': 'new_end'}},
            {'broadcast_interval': None},
            {'broadcast_type': 1},
            {'broadcast_type': None},
            {'parameters': {}},
            {'parameters': None},
            {'status': 4},
            {'status': 5},
            {'status': None},
            {'playlist': 'str(playlist_5.id)'},
            {'playlist': None},
            {'slides': '{str(file_3.id): [str(file_2.id)]}'},
            {'slides': {str(file_4.id): [str(file_2.id)]}}
        ]
        url = self.ad_detail_url.format(adorder=str(adorder_slides.id))
        for data in invalid_data:
            response = admin_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400.'
                f'\nДанные:{data}\nОтвет:{response_data}'
            )

    def test_update_adorder(
        self,
        admin_client,
        adorder_slides,
        nomenclature,
        playlist_5,
        file_2,
        file_3
    ):
        today = TestOrders.get_today_date()
        tomorrow = TestOrders.get_tomorrow_date()
        nomenclature_id = str(nomenclature.id)
        playlist_id = str(playlist_5.id)
        track_id = str(file_3.id)
        slide_id = str(file_2.id)
        valid_data = [
            {
                'name': 'new_name',
                'description': 'description',
                'clients': [nomenclature_id],
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'playlist': playlist_id,
                'slides': {track_id: [slide_id]}
            },
            {
                'name': 'new_name',
                'clients': [nomenclature_id],
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'playlist': playlist_id
            }
        ]
        adorder_id = str(adorder_slides.id)
        for data in valid_data:
            url = self.ad_detail_url.format(adorder=adorder_id)
            response = admin_client.put(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
                f'Код статуса в ответе != 405.\nОтвет:{response_data}'
            )

    def test_valid_partial_update_bgorder_admin(
        self,
        admin_client,
        bgorder,
        playlist_6
    ):
        playlist_id = str(playlist_6.id)
        update_data = TestOrders.get_valid_partial_update_bgorder_data(playlist_id)
        bgorder_id = str(bgorder.id)
        url = self.bg_detail_url.format(bgorder=bgorder_id)
        for data in update_data:
            response = admin_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Код статуса в ответе != 200.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )
            updated_key = ''.join(data.keys())
            self.check_valid_update_response(data, response_data, updated_key)

    def test_valid_partial_update_bgorder_manager(
        self,
        manager_client,
        bgorder,
        playlist_6
    ):
        playlist_id = str(playlist_6.id)
        update_data = TestOrders.get_valid_partial_update_bgorder_data(playlist_id)
        bgorder_id = str(bgorder.id)
        url = self.bg_detail_url.format(bgorder=bgorder_id)
        for data in update_data:
            response = manager_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Код статуса в ответе != 200.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )
            updated_key = ''.join(data.keys())
            self.check_valid_update_response(data, response_data, updated_key)

    def test_valid_partial_update_bgorder_user(
        self,
        user_client,
        bgorder,
        playlist_6
    ):
        playlist_id = str(playlist_6.id)
        update_data = TestOrders.get_valid_partial_update_bgorder_data(playlist_id)
        bgorder_id = str(bgorder.id)
        url = self.bg_detail_url.format(bgorder=bgorder_id)
        for data in update_data:
            response = user_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                f'Код статуса в ответе != 403.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )

    def test_valid_partial_update_bgorder_anon(
        self,
        anon_client,
        bgorder,
        playlist_6
    ):
        playlist_id = str(playlist_6.id)
        update_data = TestOrders.get_valid_partial_update_bgorder_data(playlist_id)
        bgorder_id = str(bgorder.id)
        url = self.bg_detail_url.format(bgorder=bgorder_id)
        for data in update_data:
            response = anon_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Код статуса в ответе != 401.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )

    def test_invalid_partial_update_bgorder(
        self,
        admin_client,
        user,
        bgorder,
        nomenclature_1,
        playlist_6
    ):
        today = TestOrders.get_today_date()
        new_end = TestOrders.get_new_tomorrow_date()
        nomenclature_id = str(nomenclature_1.id)
        user_id = str(user.id)
        invalid_data = [
            {'name': None},
            {'clients': [nomenclature_id]},
            {'clients': None},
            {'owner': user_id},
            {'owner': None},
            {'broadcast_interval': {'lower': today, 'upper': new_end}},
            {'broadcast_interval': {'lower': 'today', 'upper': 'new_end'}},
            {'broadcast_interval': None},
            {'order_type': 1},
            {'order_type': None},
            {'parameters': {}},
            {'parameters': None},
            {'status': 4},
            {'status': 5},
            {'status': None},
            {'playlist': 'str(playlist_5.id)'},
            {'playlist': None}
        ]
        bgorder_id = str(bgorder.id)
        url = self.bg_detail_url.format(bgorder=bgorder_id)
        for data in invalid_data:
            response = admin_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400.'
                f'\nДанные:{data}\nОтвет:{response_data}'
            )

    def test_update_bgorder(
        self,
        admin_client,
        bgorder,
        nomenclature,
        playlist_1
    ):
        today = TestOrders.get_today_date()
        tomorrow = TestOrders.get_tomorrow_date()
        nomenclature_id = str(nomenclature.id)
        playlist_id = str(playlist_1.id)
        valid_data = [
            {
                'name': 'new_name',
                'clients': [nomenclature_id],
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'order_type': 0,
                'playlist': playlist_id
            },
            {
                'name': 'test',
                'description': 'description',
                'clients': [nomenclature_id],
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'order_type': 0,
                'playlist': playlist_id
            }
        ]
        bgorder_id = str(bgorder.id)
        url = self.bg_detail_url.format(bgorder=bgorder_id)
        for data in valid_data:
            response = admin_client.put(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
                f'Код статуса в ответе != 405.'
                f'\nДанные:{data}.\nОтвет:{response_data}'
            )


@pytest.mark.skip(
    reason='Запросы работают. Нужно придумать как тестировать таски celery'
)
class TestCeleryTasks:

    def test_cancel_adorder_admin(
        self,
        admin_client,
        adorder
    ):
        adorder_id = str(adorder.id)
        url = TestOrders.ad_cancel_url.format(adorder=adorder_id)
        response = admin_client.delete(url)
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет:{response.json()}.'
        )
        order_obj = AdOrder.objects.get(id=adorder_id)
        assert order_obj.status == 3, 'Статус заказа не Отменён.'

    def test_cancel_adorder_manager(
        self,
        manager_client,
        adorder
    ):
        adorder_id = str(adorder.id)
        url = TestOrders.ad_cancel_url.format(adorder=adorder_id)
        response = manager_client.delete(url)
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет:{response.json()}.'
        )
        order_obj = AdOrder.objects.get(id=adorder_id)
        assert order_obj.status == 3, 'Статус заказа не Отменён.'

    def test_cancel_adorder_user(
        self,
        user_client,
        adorder
    ):
        adorder_id = str(adorder.id)
        url = TestOrders.ad_cancel_url.format(adorder=adorder_id)
        response = user_client.delete(url)
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.\nОтвет:{response.json()}.'
        )

    def test_cancel_adorder_anon(
        self,
        anon_client,
        adorder
    ):
        adorder_id = str(adorder.id)
        url = TestOrders.ad_cancel_url.format(adorder=adorder_id)
        response = anon_client.delete(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.\nОтвет:{response.json()}.'
        )

    def test_cancel_bgorder_admin(
        self,
        admin_client,
        bgorder
    ):
        bgorder_id = str(bgorder.id)
        url = TestOrders.bg_cancel_url.format(bgorder=bgorder_id)
        response = admin_client.delete(url)
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет:{response.json()}.'
        )
        order_obj = BgOrder.objects.get(id=bgorder_id)
        assert order_obj.status == 3, 'Статус заказа не Отменён.'

    def test_cancel_bgorder_manager(
        self,
        manager_client,
        bgorder
    ):
        bgorder_id = str(bgorder.id)
        url = TestOrders.bg_cancel_url.format(bgorder=bgorder_id)
        response = manager_client.delete(url)
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет:{response.json()}.'
        )
        order_obj = BgOrder.objects.get(id=bgorder_id)
        assert order_obj.status == 3, 'Статус заказа не Отменён.'

    def test_cancel_bgorder_user(
        self,
        user_client,
        bgorder
    ):
        bgorder_id = str(bgorder.id)
        url = TestOrders.bg_cancel_url.format(bgorder=bgorder_id)
        response = user_client.delete(url)
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.\nОтвет:{response.json()}.'
        )

    def test_cancel_bgorder_anon(
        self,
        anon_client,
        bgorder
    ):
        bgorder_id = str(bgorder.id)
        url = TestOrders.bg_cancel_url.format(bgorder=bgorder_id)
        response = anon_client.delete(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.\nОтвет:{response.json()}.'
        )
