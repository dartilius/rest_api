from http import HTTPStatus

import pytest


@pytest.mark.django_db
class TestCurrentUserProfile:
    url = '/api/users/me/'

    def test_returns_only_current_user_profile(self, user_client, user):
        response = user_client.get(self.url)

        assert response.status_code == HTTPStatus.OK
        assert response.json() == {
            'id': str(user.id),
            'email': user.email,
            'phone_number': str(user.phone_number),
            'first_name': user.first_name,
            'last_name': user.last_name,
            'middle_name': user.middle_name,
            'role': user.role,
        }

    def test_updates_own_profile_but_not_role(self, user_client, user):
        response = user_client.patch(
            self.url,
            {
                'first_name': 'Пётр',
                'last_name': 'Петров',
                'role': 'superuser',
            },
            format='json',
        )

        assert response.status_code == HTTPStatus.OK
        user.refresh_from_db()
        assert user.first_name == 'Пётр'
        assert user.last_name == 'Петров'
        assert user.role == 'ordinary'


@pytest.mark.django_db
class TestCounterpartyFilterOptionsAccess:
    url = '/api/counterparties/filter-options/'

    def test_ordinary_user_cannot_get_filter_options(self, user_client):
        response = user_client.get(self.url)

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_manager_can_get_filter_options(self, manager_client):
        response = manager_client.get(self.url)

        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
class TestCounterpartySearchFilterAccess:
    url = '/api/nomenclatures/web/search/'
    payload = {
        'page': 1,
        'limit': 24,
        'counterparty_ids': ['00000000-0000-0000-0000-000000000001'],
    }

    def test_ordinary_user_cannot_filter_by_counterparty(self, user_client):
        response = user_client.post(self.url, self.payload, format='json')

        assert response.status_code == HTTPStatus.FORBIDDEN

    def test_manager_can_filter_by_counterparty(self, manager_client):
        response = manager_client.post(self.url, self.payload, format='json')

        assert response.status_code == HTTPStatus.OK
