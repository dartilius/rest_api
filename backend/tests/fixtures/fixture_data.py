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


# @pytest.fixture
# def file_1(user, tag_1):
#     with open('/app/tests/fixtures/test_audio.mp3', 'rb') as file:
#         audio_source = file.read()
#     file_obj = File.objects.create(
#         owner=user,
#         source=audio_source,
#         file_type=1
#     )
#     file_obj.tags.set([tag_1, tag_2])
#     return file_obj
#
#
# @pytest.fixture
# def file_2(user, tag_1, tag_2):
#     with open('/app/tests/fixtures/test_image.png', 'rb') as file:
#         image_source = file.read()
#     return File.objects.create(
#         owner=user,
#         source=image_source,
#         file_type=2
#     )


# @pytest.fixture
# def playlist(user, file_1, file_2):
#     return Playlist.objects.create(
#         name='test',
#         owner=user,
#         files=[str(file_1.id), str(file_2.id)]
#     )
