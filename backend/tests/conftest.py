import pytest

pytest_plugins = [
    'celery.contrib.pytest',
    'tests.fixtures.fixture_user',
    'tests.fixtures.fixture_data',
]


@pytest.fixture(scope='session')
def celery_config():
    from django.conf import settings
    return {
        'broker_url': settings.CELERY_BROKER_URL,
        'result_backend': settings.CELERY_RESULT_BACKEND
    }
