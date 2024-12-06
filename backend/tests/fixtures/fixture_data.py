import pytest
from datetime import datetime as dt, timedelta as td
from random import randint

from ch_statistic.models import ADStat, ImageStat, MusicStat, TickerStat, VideoStat
from files.models import File, Playlist, Tag
from nomenclatures.models import Nomenclature, StatusHistory
from orders.models import AdOrder, BgOrder
from tasks.models import Task


@pytest.fixture
def nomenclature(user) -> Nomenclature:
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
def nomenclature_1(user) -> Nomenclature:
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
        name='Test Nomenclature 2',
        owner=user,
        timezone='Etc/GMT-7',
        settings=settings
    )


@pytest.fixture
def status_history(nomenclature) -> StatusHistory:
    return StatusHistory.objects.create(
        client=nomenclature,
        change_time=dt.now(),
        status=0
    )


@pytest.fixture
def task(user, nomenclature) -> Task:
    return Task.objects.create(
        client=nomenclature,
        owner=user,
        parameters='test',
        type=17
    )


@pytest.fixture
def tag_1() -> Tag:
    return Tag.objects.create(
        name='test'
    )


@pytest.fixture
def tag_2() -> Tag:
    return Tag.objects.create(
        name='ololo'
    )


@pytest.fixture
def file_1(user_client, user, tag_1, tag_2) -> File:
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
    file_obj: File = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def file_2(user_client, user) -> File:
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
    file_obj: File = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def file_3(user_client, user) -> File:
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
    file_obj: File = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def file_4(user_client, user) -> File:
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
def file_5(user_client, user) -> File:
    with open('/app/tests/fixtures/test_audio_1.txt', 'r') as file:
        source = file.read()
    file_contents = 'data:test_1.mp3;base64,'
    file_contents += source
    data = {
        'source': file_contents,
        'type': 0
    }
    response = user_client.post('/api/files/', data=data, format='json')
    response_data = response.json()
    file_obj: File = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def playlist_1(user, file_1) -> Playlist:
    pls_obj: Playlist = Playlist.objects.create(
        name='playlist_1',
        owner=user
    )
    pls_obj.files.set([file_1.id])
    return pls_obj


@pytest.fixture
def playlist_2(user, file_2) -> Playlist:
    pls_obj: Playlist = Playlist.objects.create(
        name='playlist_2',
        owner=user
    )
    pls_obj.files.set([file_2.id])
    return pls_obj


@pytest.fixture
def playlist_3(user, file_3) -> Playlist:
    pls_obj: Playlist = Playlist.objects.create(
        name='playlist_3',
        owner=user
    )
    pls_obj.files.set([file_3.id])
    return pls_obj


@pytest.fixture
def playlist_4(user, file_4) -> Playlist:
    pls_obj: Playlist = Playlist.objects.create(
        name='playlist_4',
        owner=user
    )
    pls_obj.files.set([file_4.id])
    return pls_obj


@pytest.fixture
def playlist_5(user, file_1, file_5) -> Playlist:
    pls_obj: Playlist = Playlist.objects.create(
        name='playlist_5',
        owner=user
    )
    pls_obj.files.set([file_1.id, file_5.id])
    return pls_obj


@pytest.fixture
def playlist_6(user, file_5) -> Playlist:
    pls_obj: Playlist = Playlist.objects.create(
        name='playlist_6',
        owner=user
    )
    pls_obj.files.set([file_5.id])
    return pls_obj


@pytest.fixture
def adorder(user, file_1, playlist_1, nomenclature) -> AdOrder:
    today = f'{dt.today().date()} 09:00:00'
    tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
    return AdOrder.objects.create(
        name='test',
        owner=user,
        broadcast_interval=f"({today}, {tomorrow}]",
        client=nomenclature,
        playlist=playlist_1,
        parameters={'times_in_hour': 4}
    )


@pytest.fixture
def adorder_slides(user, file_1, file_2, playlist_5, nomenclature) -> AdOrder:
    today = f'{dt.today().date()} 09:00:00'
    tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
    return AdOrder.objects.create(
        name='test',
        owner=user,
        broadcast_interval=f"({today}, {tomorrow}]",
        client=nomenclature,
        playlist=playlist_5,
        slides={str(file_1.id): [str(file_2.id)]},
        parameters={'times_in_hour': 4}
    )


@pytest.fixture
def bgorder(user, file_1, playlist_1, nomenclature) -> BgOrder:
    today = f'{dt.today().date()} 09:00:00'
    tomorrow = f'{dt.today().date() + td(days=1)} 20:00:00'
    return BgOrder.objects.create(
        name='test',
        owner=user,
        broadcast_interval=f"({today}, {tomorrow}]",
        order_type=0,
        client=nomenclature,
        playlist=playlist_1
    )


@pytest.fixture
def ad_stat(nomenclature, file_3) -> ADStat:
    length = randint(5, 30)
    return ADStat.objects.create(
        created=f'{dt.today().date()} 12:00:{length + 1}',
        played=f'{dt.today().date()} 12:00:00',
        file=str(file_3.id),
        client=str(nomenclature.id),
        length=length,
        ad_block=randint(0, 12)
    )


@pytest.fixture
def music_stat(nomenclature, file_1) -> MusicStat:
    length = randint(5, 30)
    return MusicStat.objects.create(
        created=f'{dt.today().date()} 12:00:{length + 1}',
        played=f'{dt.today().date()} 12:00:00',
        file=str(file_1.id),
        client=str(nomenclature.id),
        length=length
    )


@pytest.fixture
def image_stat(nomenclature, file_2) -> ImageStat:
    length = randint(5, 30)
    return ImageStat.objects.create(
        created=f'{dt.today().date()} 12:00:{length + 1}',
        played=f'{dt.today().date()} 12:00:00',
        file=str(file_2.id),
        client=str(nomenclature.id),
        length=length
    )


@pytest.fixture
def video_stat(nomenclature, file_3) -> VideoStat:
    length = randint(5, 30)
    return VideoStat.objects.create(
        created=f'{dt.today().date()} 12:00:{length + 1}',
        played=f'{dt.today().date()} 12:00:00',
        file=str(file_3.id),
        client=str(nomenclature.id),
        length=length
    )


@pytest.fixture
def ticker_stat(nomenclature, file_4) -> TickerStat:
    length = randint(5, 30)
    return TickerStat.objects.create(
        created=f'{dt.today().date()} 12:00:{length + 1}',
        played=f'{dt.today().date()} 12:00:00',
        file=str(file_4.id),
        client=str(nomenclature.id),
        length=length
    )
