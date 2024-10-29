import pytest
from http import HTTPStatus
from dotenv import load_dotenv

from files.models import File, Playlist

load_dotenv()


@pytest.mark.django_db(transaction=True)
class TestFiles:

    files_url = '/api/files/'
    playlists_url = '/api/playlists/'
    tags_url = '/api/tags/'
    file_detail_url = '/api/files/{file_id}/'
    playlist_detail_url = '/api/playlists/{playlist_id}/'
    tag_detail_url = '/api/tags/{tag_id}/'

    def test_avail_user(self, user_client):
        files_url = self.files_url
        playlists_url = self.playlists_url
        tags_url = self.tags_url
        response = user_client.get(files_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{files_url}.'
        )
        response = user_client.get(playlists_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{playlists_url}.'
        )
        response = user_client.get(tags_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{tags_url}.'
        )

    def test_avail_anon(self, anon_client):
        files_url = self.files_url
        playlists_url = self.playlists_url
        tags_url = self.tags_url
        response = anon_client.get(files_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Не авторизованный пользователь имеет доступ к странице '
            f'{files_url}.'
        )
        response = anon_client.get(playlists_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Не авторизованный пользователь имеет доступ к странице '
            f'{playlists_url}.'
        )
        response = anon_client.get(tags_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Не авторизованный пользователь имеет доступ к странице '
            f'{tags_url}.'
        )

    def test_avail_admin(self, admin_client):
        files_url = self.files_url
        playlists_url = self.playlists_url
        tags_url = self.tags_url
        response = admin_client.get(files_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{files_url}.'
        )
        response = admin_client.get(playlists_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{playlists_url}.'
        )
        response = admin_client.get(tags_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{tags_url}.'
        )

    def test_create_valid_file(self, user_client, user, tag_1, tag_2):
        file_count = File.objects.count()
        audio_source = 'data:test.mp3;base64,'
        with open('/app/tests/fixtures/test_audio.txt', 'r') as file:
            audio_source += file.read()
        data = {
            'source': audio_source,
            'file_type': 1,
            'tags': [{'name': tag_1.name}, {'name': tag_2.name}]
        }
        response = user_client.post(self.files_url, data=data, format='json')
        assert response.status_code == HTTPStatus.CREATED, (
            'Код статуса в ответе != 201.'
        )
        file_count += 1
        assert file_count == File.objects.count(), (
            'Не удалось создать файл.'
        )
        response_data = response.json()
        assert response_data['owner'] == user.get_full_name(), (
            'Владелец файла не встал в соответствующее поле.'
        )
        assert {
           tag['name'] for tag in response_data['tags']
        } == {tag_1.name, tag_2.name}, (
            'Тэги файла отличаются от отправленных.'
        )
        assert response_data.get('name'), (
            'Файлу не присвоилось имя из отправленных данных.'
        )
        assert response_data.get('url'), (
            'Не сформировалась ссылка на файл в минио.'
        )
        assert response_data.get('size'), (
            'Не удалось вычислить размер файла.'
        )
        assert response_data.get('hash'), (
            'Не удалось вычислить хэш файла.'
        )
        if response_data.get('file_type') not in (2, 5):
            assert response_data.get('length'), (
                'Не удалось вычислить продолжительность медиафайла.'
            )

    def test_create_invalid_file(self, user_client, tag_1, tag_2):
        file_count = File.objects.count()
        audio_source = 'data:test.mp3;base64,'
        with open('/app/tests/fixtures/test_audio.txt', 'r') as file:
            audio_source += file.read()
        invalid_data = [
            {
                'source': 'data:test.mp3;base64,ololo',
                'file_type': 1,
                'tags': [{'name': tag_1.name}, {'name': tag_2.name}]
            },
            {
                'source': audio_source,
                'file_type': 6,
                'tags': [{'name': tag_1.name}, {'name': tag_2.name}]
            },
            {
                'source': audio_source,
                'file_type': 1,
                'tags': [tag_1.name, tag_2.name]
            }
        ]
        for data in invalid_data:
            response = user_client.post(self.files_url, data=data, format='json')
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                'Код статуса в ответе != 400.'
            )
            file_count += 1
            assert file_count != File.objects.count(), (
                f'Удалось создать файл с неправильными данными: {data}.'
            )

    def test_create_valid_playlist(self, user_client, user, file_1):
        pls_count = Playlist.objects.count()
        file_id = file_1.id
        data = {
            'name': 'test',
            'files': [file_id]
        }
        response = user_client.post(self.playlists_url, data=data, format='json')
        assert response.status_code == HTTPStatus.CREATED, (
            'Код статуса в ответе != 201.'
        )
        pls_count += 1
        assert pls_count == File.objects.count(), (
            'Не удалось создать плейлист.'
        )
        response_data = response.json()
        assert response_data['owner'] == user.get_full_name(), (
            'Владелец плейлиста не встал в соответствующее поле.'
        )
        assert response_data['name'] == data['name'], (
            'Имя плейлиста отличается от отправленных данных.'
        )
        assert len(response_data['files']) == len(data['files']), (
            'Количество файлов в плейлисте отличается от отправленных данных.'
        )

    def test_create_invalid_playlist(self, user_client, file_1):
        pls_count = Playlist.objects.count()
        file_id = file_1.id
        invalid_data = [
            {
                'name': None,
                'files': [file_id]
            },
            {
                'name': 'test',
                'files': 'file_id'
            }
        ]
        for data in invalid_data:
            response = user_client.post(self.playlists_url, data=data, format='json')
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400\n{data}.'
            )
            pls_count += 1
            assert pls_count != Playlist.objects.count(), (
                f'Удалось создать плейлист с неправильными данными: {data}.'
            )

    def test_detail_user(self, user_client, file_1, playlist):
        file_id = str(file_1.id)
        file_url = self.file_detail_url.format(file_id=file_id)
        playlist_id = str(playlist.id)
        playlist_url = self.playlist_detail_url.format(playlist_id=playlist_id)
        response = user_client.get(file_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{file_url}.'
        )
        response = user_client.get(playlist_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{playlist_url}.'
        )

    def test_detail_anon(self, anon_client, file_1, playlist):
        file_id = str(file_1.id)
        file_url = self.file_detail_url.format(file_id=file_id)
        playlist_id = str(playlist.id)
        playlist_url = self.playlist_detail_url.format(playlist_id=playlist_id)
        response = anon_client.get(file_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Неавторизованный пользователь имеет доступ к странице.'
            f'{file_url}.'
        )
        response = anon_client.get(playlist_url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            'Неавторизованный пользователь имеет доступ к странице.'
            f'{playlist_url}.'
        )

    def test_detail_admin(self, admin_client, file_1, playlist):
        file_id = str(file_1.id)
        file_url = self.file_detail_url.format(file_id=file_id)
        playlist_id = str(playlist.id)
        playlist_url = self.playlist_detail_url.format(playlist_id=playlist_id)
        response = admin_client.get(file_url)
        assert response.status_code == HTTPStatus.OK, (
            'Пользователь-админ не имеет доступ к странице.'
            f'{file_url}.'
        )
        response = admin_client.get(playlist_url)
        assert response.status_code == HTTPStatus.OK, (
            'Пользователь-админ не имеет доступ к странице.'
            f'{playlist_url}.'
        )




