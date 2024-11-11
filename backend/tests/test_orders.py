import pytest

from datetime import datetime as dt, timedelta as td
from django.shortcuts import get_object_or_404
from http import HTTPStatus
from itertools import chain
from uuid import UUID

from nomenclatures.models import Nomenclature
from orders.models import AdOrder, BgOrder


@pytest.mark.django_db
class TestOrders:

    ad_list_url = '/api/adorders/'
    ad_detail_url = '/api/adorders/{adorder}/'
    bg_list_url = '/api/bgorders/'
    bg_detail_url = '/api/bgorders/{bgorder}/'

    def test_availability(self, user_client, anon_client, adorder, bgorder):
        urls = [
            self.ad_list_url,
            self.bg_list_url,
            self.ad_detail_url.format(adorder=str(adorder.id)),
            self.bg_detail_url.format(bgorder=str(bgorder.id)),
        ]
        for url in urls:
            response = user_client.get(url)
            assert response.status_code == HTTPStatus.OK, (
                f'Авторизованный пользователь не имеет доступ к странице '
                f'{url}.'
            )
            response = anon_client.get(url)
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Не авторизованный пользователь имеет доступ к странице '
                f'{url}.'
            )

    def test_create_valid_adorder(
            self,
            user_client,
            user,
            nomenclature,
            playlist_1
    ):
        today = f'{dt.today().date()} 09:00:00'
        tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
        adorder_count = AdOrder.objects.count()
        valid_data = [
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 1,
                'parameters': {'times_in_hour': 4, 'timedelta': '01:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 2,
                'parameters': {'times_in_hour': 4, 'timedelta': '01:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '12:00:00',
                               'daily_end_time': '16:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 4,
                'parameters': {'times_in_hour': 4,
                               'daily_end_time': '12:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 5,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '18:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'event': 'click',
                               'active_ad': 'stop'}
            }],
        ]
        for data in valid_data:
            response = user_client.post(
                self.ad_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201 для данных: {data}.'
            )
            adorder_count += 1
            assert adorder_count == AdOrder.objects.count(), (
                f'Не удалось создать рекламный заказ.'
            )
            response_data = response.json()
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
            assert response_data[0][0]['owner'] == user.full_name, (
                'Создатель заказа не встал в соответствующее поле.'
            )
            assert (
                response_data[0][0]['client']['id'] == data[0]['clients'][0]
            ), (
                'Целевая рабочая станция созданного заказа отличается от '
                'таковой в отправленных данных.'
            )
            assert (
                response_data[0][0]['playlist']['id'] == data[0]['playlist']
            ), (
                'Плейлист созданного заказа отличается от указанного '
                'в отправленных данных.'
            )
            assert (
                response_data[0][0]['broadcast_type']
                == data[0]['broadcast_type']
            ), (
                'Режим вещания заказа отличается от указанного '
                'в отправленных данных.'
            )
            assert response_data[0][0]['parameters'] == check_params, (
                'Параметры заказа отличаются от отправленных данных.'
            )
            check_params.clear()

    def test_create_invalid_adorder(
            self,
            user_client,
            nomenclature,
            playlist_1
    ):
        today = f'{dt.today().date()} 09:00:00'
        tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
        adorder_count = AdOrder.objects.count()
        invalid_data = [
            [{
                'name': None,
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': tomorrow, 'upper': today},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'client': 'nomenclature.id',
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': 'playlist.id',
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 7,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 5}
            }],
            [{
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'client': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 0,
                'parameters': {'times_in_hour': 4, 'weight': 111}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 1,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 1,
                'parameters': {'times_in_hour': 4, 'timedelta': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 2,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 2,
                'parameters': {'times_in_hour': 4, 'timedelta': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4, 'daily_start_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4, 'daily_end_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '01:00:00',
                               'daily_end_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': 1,
                               'daily_end_time': '01:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '09:00:00',
                               'daily_end_time': '08:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 3,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '09:00:00',
                               'daily_end_time': '24:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 4,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 4,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 4,
                'parameters': {'times_in_hour': 4,
                               'daily_start_time': '24:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 5,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 5,
                'parameters': {'times_in_hour': 4,
                               'daily_end_time': 1}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 5,
                'parameters': {'times_in_hour': 4,
                               'daily_end_time': '24:00:00'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'event': 'click'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'active_ad': 'skip'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'event': 'invalid_event',
                               'active_ad': 'skip'}
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'broadcast_type': 6,
                'parameters': {'times_in_hour': 4,
                               'event': 'click',
                               'active_ad': 'invalid_behavior'}
            }],
        ]
        for data in invalid_data:
            response = user_client.post(
                self.ad_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400. для данных: {data}'
            )
            adorder_count += 1
            assert adorder_count != AdOrder.objects.count(), (
                f'Удалось создать неправильный рекламный заказ: {data}.'
            )

    def test_create_valid_bgorder(
            self,
            user_client,
            user,
            nomenclature,
            playlist_1,
            playlist_2,
            playlist_3,
            playlist_4
    ):
        today = f'{dt.today().date()} 09:00:00'
        tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
        bgorder_count = BgOrder.objects.count()
        valid_data = [
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_2.id),
                'order_type': 1
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_3.id),
                'order_type': 2
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_4.id),
                'order_type': 3
            }]
        ]
        for data in valid_data:
            response = user_client.post(
                self.bg_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.CREATED, (
                'Код статуса в ответе != 201.'
            )
            bgorder_count += 1
            assert bgorder_count == BgOrder.objects.count(), (
                f'Не удалось создать рекламный заказ.'
            )
            response_data = response.json()
            assert response_data[0][0]['owner'] == user.full_name, (
                'Создатель заказа не встал в соответствующее поле.'
            )
            assert (
                response_data[0][0]['client']['id'] == data[0]['clients'][0]
            ), (
                'Целевая рабочая станция созданного заказа отличается от '
                'таковой в отправленных данных.'
            )
            assert (
                response_data[0][0]['playlist']['id'] == data[0]['playlist']
            ), (
                'Плейлист созданного заказа отличается от указанного '
                'в отправленных данных.'
            )
            assert (
                response_data[0][0]['order_type'] == data[0]['order_type']
            ), 'Тип заказа отличается от указанного в отправленных данных.'

    def test_create_invalid_bgorder(
            self,
            user_client,
            nomenclature,
            playlist_1
    ):
        today = f'{dt.today().date()} 09:00:00'
        tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
        bgorder_count = BgOrder.objects.count()
        invalid_data = [
            [{
                'name': None,
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': None,
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'client': None,
                'playlist': str(playlist_1.id),
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': None,
                'order_type': 0
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': today, 'upper': tomorrow},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'order_type': None
            }],
            [{
                'name': 'test',
                'broadcast_interval': {'lower': tomorrow, 'upper': today},
                'clients': [str(nomenclature.id)],
                'playlist': str(playlist_1.id),
                'order_type': 0
            }],
        ]
        for data in invalid_data:
            response = user_client.post(
                self.bg_list_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                'Код статуса в ответе != 400.'
            )
            bgorder_count += 1
            assert bgorder_count != BgOrder.objects.count(), (
                f'Удалось создать неправильный рекламный заказ: {data}.'
            )

    def test_chain_and_id(self, nomenclature, adorder, bgorder):
        nom = get_object_or_404(Nomenclature, id=str(nomenclature.id))
        orders_list = chain(
            nom.adorders.filter(status__in=[0, 1]),
            nom.bgorders.filter(status__in=[0, 1])
        )

        for order in orders_list:
            assert isinstance(order.id, UUID)
