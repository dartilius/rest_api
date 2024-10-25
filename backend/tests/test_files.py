import pytest
from http import HTTPStatus
from dotenv import load_dotenv

from files.models import File, Playlist, Tag

load_dotenv()


@pytest.mark.django_db
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

    def create_file(self, tag_1, tag_2, user_client):
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
        file_count += 1
        assert file_count == File.objects.count()
        return response.json()

    def test_create_valid_playlist(self, user_client, user, tag_1, tag_2):
        pls_count = Playlist.objects.count()
        file_obj = self.create_file(tag_1, tag_2, user_client)
        file_id = [file_obj['id']]
        data = {
            'name': 'test',
            'files': file_id
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

    def test_create_invalid_playlist(self, user_client, tag_1, tag_2):
        pls_count = Playlist.objects.count()
        file_obj = self.create_file(tag_1, tag_2, user_client)
        file_id = [file_obj['id']]
        invalid_data = [
            # {
            #     'name': None,
            #     'files': [file_id]
            # },
            {
                'name': 'test',
                'files': 'file_id'
            },
            {
                'name': 'test',
                'files': file_id
            }
        ]
        for data in invalid_data:
            response = user_client.post(self.playlists_url, data=data, format='json')
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                'Код статуса в ответе != 400.'
            )
            pls_count += 1
            assert pls_count != File.objects.count(), (
                f'Удалось создать плейлист с неправильными данными: {data}.'
            )

    def create_playlist(self, tag_1, tag_2, user_client):
        file_obj = self.create_file(tag_1, tag_2, user_client)
        file_id = [file_obj['id']]
        data = {
            'name': 'test',
            'files': file_id
        }
        response = user_client.post(self.playlists_url, data=data, format='json')
        return response.json()

    def test_detail_user(self, user_client, tag_1, tag_2):
        file_obj = self.create_file(user_client, tag_1, tag_2)
        file_id = [file_obj['id']]
        file_url = self.file_detail_url.format(task_id=file_id)
        playlist_obj = self.create_playlist(tag_1, tag_2, user_client)
        playlist_id = str(playlist_obj.id)
        playlist_url = self.playlist_detail_url.format(playlist_id=playlist_id)
        tag_id = tag_1.id
        tag_url = self.tag_detail_url.format(tag_id=tag_id)
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
        response = user_client.get(tag_url)
        assert response.status_code == HTTPStatus.OK, (
            f'Авторизованный пользователь не имеет доступ к странице '
            f'{tag_url}.'
        )

    def test_detail_anon(self, anon_client, tag_1, tag_2):
        file_obj = self.create_file(anon_client, tag_1, tag_2)
        file_id = [file_obj['id']]
        file_url = self.file_detail_url.format(task_id=file_id)
        playlist_obj = self.create_playlist(tag_1, tag_2, anon_client)
        playlist_id = str(playlist_obj.id)
        playlist_url = self.playlist_detail_url.format(playlist_id=playlist_id)
        tag_id = tag_1.id
        tag_url = self.tag_detail_url.format(tag_id=tag_id)
        response = anon_client.get(file_url)
        assert response.status_code == HTTPStatus.OK, (
            'Неавторизованный пользователь имеет доступ к странице.'
            f'{file_url}.'
        )
        response = anon_client.get(playlist_url)
        assert response.status_code == HTTPStatus.OK, (
            'Неавторизованный пользователь имеет доступ к странице.'
            f'{playlist_url}.'
        )
        response = anon_client.get(tag_url)
        assert response.status_code == HTTPStatus.OK, (
            'Неавторизованный пользователь имеет доступ к странице.'
            f'{tag_url}.'
        )

    def test_detail_admin(self, admin_client, tag_1, tag_2):
        file_obj = self.create_file(admin_client, tag_1, tag_2)
        file_id = [file_obj['id']]
        file_url = self.file_detail_url.format(task_id=file_id)
        playlist_obj = self.create_playlist(tag_1, tag_2, admin_client)
        playlist_id = str(playlist_obj.id)
        playlist_url = self.playlist_detail_url.format(playlist_id=playlist_id)
        tag_id = tag_1.id
        tag_url = self.tag_detail_url.format(tag_id=tag_id)
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
        response = admin_client.get(tag_url)
        assert response.status_code == HTTPStatus.OK, (
            'Пользователь-админ не имеет доступ к странице.'
            f'{tag_url}.'
        )




