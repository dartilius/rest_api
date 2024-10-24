import pytest


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email='user@test.com',
        username='user@test.com',
        phone_number='+78005553535',
        password='test'
    )


@pytest.fixture
def admin_user():
    from django.contrib.auth.backends import UserModel

    user_data = {
        "email": "admin@example.com",
        "password": "password"
    }
    user = UserModel._default_manager.create_superuser(**user_data)
    return user


@pytest.fixture
def user_token(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@pytest.fixture
def admin_token(admin_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(admin_user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@pytest.fixture
def user_client(user_token):
    from rest_framework.test import APIClient

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'access_token {user_token["access"]}')
    return client


@pytest.fixture
def admin_client(admin_token):
    from rest_framework.test import APIClient

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'access_token {admin_token["access"]}')
    return client


@pytest.fixture
def anon_client():
    from rest_framework.test import APIClient

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'access_token bad_token')
    return client
