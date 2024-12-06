import pytest


@pytest.fixture
def super_user():
    from django.contrib.auth.backends import UserModel
    user_data = {
        'email': '123@lol.com',
        'password': 'password',
        'phone_number': '+78005553535'
    }
    user = UserModel._default_manager.create_superuser(**user_data)
    return user


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        email='user@test.com',
        phone_number='+78005553636',
        password='test',
        first_name='user',
        last_name='user',
        role='ordinary'
    )


@pytest.fixture
def another_user(django_user_model):
    return django_user_model.objects.create_user(
        email='another_user@test.com',
        phone_number='+78005553939',
        password='test',
        first_name='another',
        last_name='user',
        role='ordinary'
    )


@pytest.fixture
def admin_user(django_user_model):
    return django_user_model.objects.create_user(
        email='admin@test.com',
        phone_number='+78005553737',
        password='test',
        first_name='admin',
        last_name='admin',
        role='admin'
    )


@pytest.fixture
def manager_user(django_user_model):
    return django_user_model.objects.create_user(
        email='manager@test.com',
        phone_number='+78005553838',
        password='test',
        first_name='manager',
        last_name='manager',
        role='manager'
    )


@pytest.fixture
def superuser_token(super_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(super_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@pytest.fixture
def user_token(user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@pytest.fixture
def another_user_token(another_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(another_user)
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
def manager_token(manager_user):
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(manager_user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@pytest.fixture
def superuser_client(superuser_token):
    from rest_framework.test import APIClient
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f'access_token {superuser_token["access"]}'
    )
    return client


@pytest.fixture
def user_client(user_token):
    from rest_framework.test import APIClient
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f'access_token {user_token["access"]}'
    )
    return client


@pytest.fixture
def another_user_client(another_user_token):
    from rest_framework.test import APIClient
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f'access_token {another_user_token["access"]}'
    )
    return client


@pytest.fixture
def admin_client(admin_token):
    from rest_framework.test import APIClient
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f'access_token {admin_token["access"]}'
    )
    return client


@pytest.fixture
def manager_client(manager_token):
    from rest_framework.test import APIClient
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f'access_token {manager_token["access"]}'
    )
    return client


@pytest.fixture
def anon_client():
    from rest_framework.test import APIClient
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'access_token bad_token')
    return client
