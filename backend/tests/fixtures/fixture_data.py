import pytest

from files.models import File, Playlist, Tag
from nomenclatures.models import Nomenclature
from orders.models import AdOrder, BgOrder
from tasks.models import Task


@pytest.fixture
def nomenclature(user):
    settings = {
        'fri': {'worktime': '09:00:00-20:00:00', 'default_volume': [50, 50, 50, 50]},
        'mon': {'worktime': '09:00:00-20:00:00', 'default_volume': [50, 50, 50, 50]},
        'sat': {'worktime': '09:00:00-20:00:00', 'default_volume': [50, 50, 50, 50]},
        'sun': {'worktime': '09:00:00-20:00:00', 'default_volume': [50, 50, 50, 50]},
        'thu': {'worktime': '09:00:00-20:00:00', 'default_volume': [50, 50, 50, 50]},
        'tue': {'worktime': '09:00:00-20:00:00', 'default_volume': [50, 50, 50, 50]},
        'wed': {'worktime': '09:00:00-20:00:00', 'default_volume': [50, 50, 50, 50]}
    }
    return Nomenclature.objects.create(
        name='Test Nomenclature',
        owner=user,
        timezone='Etc/GMT-7',
        settings=settings
    )


@pytest.fixture
def task(user, nomenclature):
    return Task.objects.create(
        client=nomenclature,
        owner=user,
        parameters='test',
        type=17
    )


@pytest.fixture
def tag_1():
    return Tag.objects.create(
        name='test'
    )


@pytest.fixture
def tag_2():
    return Tag.objects.create(
        name='ololo'
    )


@pytest.fixture
def file_1(user_client, user, tag_1, tag_2):
    with open('/app/tests/fixtures/test_audio.txt', 'r') as file:
        audio_source = file.read()
    file_contents = 'data:test.mp3;base64,'
    file_contents += audio_source
    data = {
        'source': file_contents,
        'type': 0,
        'tags': [{'name': tag_1.name}, {'name': tag_2.name}]
    }
    response = user_client.post('/api/files/', data=data, format='json')
    response_data = response.json()
    file_obj = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def file_2(user_client, user):
    with open('/app/tests/fixtures/test_image.txt', 'r') as file:
        image_source = file.read()
    file_contents = 'data:test.jpg;base64,'
    file_contents += image_source
    data = {
        'source': file_contents,
        'type': 1
    }
    response = user_client.post('/api/files/', data=data, format='json')
    response_data = response.json()
    file_obj = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def file_3(user_client, user):
    with open('/app/tests/fixtures/test_video.txt', 'r') as file:
        video_source = file.read()
    file_contents = 'data:test.mp4;base64,'
    file_contents += video_source
    data = {
        'source': file_contents,
        'type': 2
    }
    response = user_client.post('/api/files/', data=data, format='json')
    response_data = response.json()
    file_obj = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def file_4(user_client, user):
    with open('/app/tests/fixtures/test_ticker.txt', 'r') as file:
        ticker_source = file.read()
    file_contents = 'data:test.txt;base64,'
    file_contents += ticker_source
    data = {
        'source': file_contents,
        'type': 3
    }
    response = user_client.post('/api/files/', data=data, format='json')
    response_data = response.json()
    file_obj = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def playlist_1(user, file_1):
    pls_obj = Playlist.objects.create(
        name='test',
        owner=user
    )
    pls_obj.files.set([file_1.id])
    return pls_obj


@pytest.fixture
def playlist_2(user, file_2):
    pls_obj = Playlist.objects.create(
        name='test',
        owner=user
    )
    pls_obj.files.set([file_2.id])
    return pls_obj


@pytest.fixture
def playlist_3(user, file_3):
    pls_obj = Playlist.objects.create(
        name='test',
        owner=user
    )
    pls_obj.files.set([file_3.id])
    return pls_obj


@pytest.fixture
def playlist_4(user, file_4):
    pls_obj = Playlist.objects.create(
        name='test',
        owner=user
    )
    pls_obj.files.set([file_4.id])
    return pls_obj


@pytest.fixture
def adorder(user, file_1, playlist_1, nomenclature):
    from datetime import datetime as dt, timedelta as td
    today = f'{dt.today().date()} 09:00:00'
    tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
    return AdOrder.objects.create(
        name='test',
        owner=user,
        broadcast_interval=f"({today}, {tomorrow}]",
        client=nomenclature,
        playlist=playlist_1,
    )


@pytest.fixture
def adorder_slides(user, file_1, file_2, playlist_1, nomenclature):
    from datetime import datetime as dt, timedelta as td
    today = f'{dt.today().date()} 09:00:00'
    tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
    return AdOrder.objects.create(
        name='test',
        owner=user,
        broadcast_interval=f"({today}, {tomorrow}]",
        client=nomenclature,
        playlist=playlist_1,
        slides={str(file_1.id): [str(file_2.id)]}
    )


@pytest.fixture
def bgorder(user, file_1, playlist_1, nomenclature):
    from datetime import datetime as dt, timedelta as td
    today = f'{dt.today().date()} 09:00:00'
    tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
    return BgOrder.objects.create(
        name='test',
        owner=user,
        broadcast_interval=f"({today}, {tomorrow}]",
        order_type=0,
        client=nomenclature,
        playlist=playlist_1,
    )
