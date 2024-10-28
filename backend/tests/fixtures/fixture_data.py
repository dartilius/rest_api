import tempfile

import pytest

from files.models import File, Playlist, Tag
from nomenclatures.models import Nomenclature
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
    file_start = 'data:test.mp3;base64,'
    file_start += audio_source
    data = {
        'source': file_start,
        'file_type': 1,
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
    file_start = 'data:test.jpg;base64,'
    file_start += image_source
    data = {
        'source': file_start,
        'file_type': 1
    }
    response = user_client.post('/api/files/', data=data, format='json')
    response_data = response.json()
    file_obj = File.objects.get(id=response_data['id'])
    return file_obj


@pytest.fixture
def playlist(user, file_1, file_2):
    pls_obj = Playlist.objects.create(
        name='test',
        owner=user
    )
    pls_obj.files.set([str(file_1.id), str(file_2.id)])
    return pls_obj
