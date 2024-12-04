import pytest
from dotenv import load_dotenv
from http import HTTPStatus
from itertools import product

from files.models import File, Playlist

load_dotenv()


@pytest.mark.django_db(transaction=True)
class TestFiles:

    files_url = '/api/files/'
    file_detail_url = '/api/files/{file_id}/'
    file_add_tags = '/api/files/{file_id}/add_tags/'
    file_remove_tags = '/api/files/{file_id}/remove_tags/'
    playlists_url = '/api/playlists/'
    playlist_detail_url = '/api/playlists/{playlist_id}/'
    playlist_add_files_url = '/api/playlists/{playlist_id}/add_files/'
    playlist_remove_files_url = '/api/playlists/{playlist_id}/remove_files/'
    tags_url = '/api/tags/'
    tag_detail_url = '/api/tags/{tag_id}/'

    @staticmethod
    def get_valid_data(tag_1, tag_2) -> list:
        audio_source = 'data:test.mp3;base64,'
        with open('/app/tests/fixtures/test_audio.txt', 'r') as file:
            audio_source += file.read()
        image_source = 'data:test.jpg;base64,'
        with open('/app/tests/fixtures/test_image.txt', 'r') as file:
            image_source += file.read()
        video_source = 'data:test.mp4;base64,'
        with open('/app/tests/fixtures/test_video.txt', 'r') as file:
            video_source += file.read()
        ticker_source = 'data:test.txt;base64,'
        with open('/app/tests/fixtures/test_ticker.txt', 'r') as file:
            ticker_source += file.read()
        valid_data = [
            {
                'source': audio_source,
                'type': 0,
                'tags': [{'name': tag_1}, {'name': tag_2}]
            },
            {
                'source': image_source,
                'type': 1,
                'tags': [{'name': tag_1}]
            },
            {
                'source': video_source,
                'type': 2,
                'tags': [{'name': tag_2}]
            },
            {
                'source': ticker_source,
                'type': 3,
                'tags': []
            }
        ]
        return valid_data

    @staticmethod
    def check_valid_create_file_response(data, user, response):
        from files.models import TYPES
        assert response['owner'] == user.full_name, (
            'Владелец файла не встал в соответствующее поле.'
        )
        assert (
                {tag['name'] for tag in response['tags']} ==
                {tag['name'] for tag in data['tags']}
        ), 'Тэги файла отличаются от отправленных.'
        assert response['type'] == TYPES[data['type']]
        assert response.get('name'), (
            'Файлу не присвоилось имя из отправленных данных.'
        )
        assert response.get('url'), (
            'Не сформировалась ссылка на файл в минио.'
        )
        assert response.get('size'), (
            'Не удалось вычислить размер файла.'
        )
        assert response.get('hash'), (
            'Не удалось вычислить хэш файла.'
        )
        if response.get('type') not in ('image', 'ticker'):
            assert response.get('length'), (
                'Не удалось вычислить продолжительность медиафайла.'
            )

    @staticmethod
    def check_valid_create_playlist_response(data, user, response):
        assert response['owner'] == user.full_name, (
            'Владелец плейлиста не встал в соответствующее поле.'
        )
        assert response['name'] == data['name'], (
            'Имя плейлиста отличается от отправленных данных.'
        )
        assert len(response['files']) == len(data['files']), (
            'Количество файлов в плейлисте отличается от отправленных данных.'
        )

    @staticmethod
    def get_valid_partial_update_playlist_data() -> list:
        data = [
            {'name': 'new_name'},
            {'description': 'description'}
        ]
        return data

    @staticmethod
    def check_partial_update_response(data, response, updated_key):
        assert data[updated_key] == response[updated_key], (
            f'{updated_key} не был обновлён'
        )

    def test_availability_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        file_1,
        playlist_1
    ):
        file_id = str(file_1.id)
        playlist_id = str(playlist_1.id)
        urls = [
            self.files_url,
            self.playlists_url,
            self.tags_url,
            self.file_detail_url.format(file_id=file_id),
            self.playlist_detail_url.format(playlist_id=playlist_id)
        ]
        clients = [admin_client, manager_client, superuser_client, user_client]
        for combo in product(clients, urls):
            response = combo[0].get(combo[1])
            assert response.status_code == HTTPStatus.OK, (
                f'Пользователь {combo[0]} не имеет доступ к странице {combo[1]}.'
            )

    def test_availability_anon(self, anon_client, file_1, playlist_1):
        file_id = str(file_1.id)
        playlist_id = str(playlist_1.id)
        urls = [
            self.files_url,
            self.playlists_url,
            self.tags_url,
            self.file_detail_url.format(file_id=file_id),
            self.playlist_detail_url.format(playlist_id=playlist_id)
        ]
        for url in urls:
            response = anon_client.get(url)
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Не авторизованный пользователь имеет доступ к странице {url}.'
            )

    def test_create_valid_file_admin(self, admin_client, admin_user, tag_1, tag_2):
        tag_1_name = tag_1.name
        tag_2_name = tag_2.name
        valid_data = TestFiles.get_valid_data(tag_1_name, tag_2_name)
        for data in valid_data:
            file_count = File.objects.count()
            response = admin_client.post(
                self.files_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nДанные: {data}.\nОтвет: {response}'
            )
            file_count += 1
            assert file_count == File.objects.count(), (
                'Не удалось создать файл.'
            )
            self.check_valid_create_file_response(data, admin_user, response_data)

    def test_create_valid_file_manager(
        self,
        manager_client,
        manager_user,
        tag_1,
        tag_2
    ):
        tag_1_name = tag_1.name
        tag_2_name = tag_2.name
        valid_data = TestFiles.get_valid_data(tag_1_name, tag_2_name)
        for data in valid_data:
            file_count = File.objects.count()
            response = manager_client.post(
                self.files_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nДанные: {data}.\nОтвет: {response}'
            )
            file_count += 1
            assert file_count == File.objects.count(), (
                'Не удалось создать файл.'
            )
            self.check_valid_create_file_response(data, manager_user, response_data)

    def test_create_valid_file_user(self, user_client, user, tag_1, tag_2):
        from files.models import TYPES
        file_count = File.objects.count()
        tag_1_name = tag_1.name
        tag_2_name = tag_2.name
        valid_data = TestFiles.get_valid_data(tag_1_name, tag_2_name)
        for data in valid_data:
            response = user_client.post(
                self.files_url,
                data=data,
                format='json'
            )
            response_data = response.json()
            assert response.status_code == HTTPStatus.CREATED, (
                f'Код статуса в ответе != 201.\nДанные: {data}.\nОтвет: {response_data}'
            )
            file_count += 1
            assert file_count == File.objects.count(), (
                'Не удалось создать файл.'
            )
            assert response_data['owner'] == user.full_name, (
                'Владелец файла не встал в соответствующее поле.'
            )
            assert (
                {tag['name'] for tag in response_data['tags']} ==
                {tag['name'] for tag in data['tags']}
            ), 'Тэги файла отличаются от отправленных.'
            assert response_data['type'] == TYPES[data['type']]
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
            if response_data.get('type') not in ('image', 'ticker'):
                assert response_data.get('length'), (
                    'Не удалось вычислить продолжительность медиафайла.'
                )

    def test_create_valid_file_anon(self, anon_client, tag_1, tag_2):
        file_count = File.objects.count()
        tag_1_name = tag_1.name
        tag_2_name = tag_2.name
        valid_data = TestFiles.get_valid_data(tag_1_name, tag_2_name)
        for data in valid_data:
            response = anon_client.post(
                self.files_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                'Код статуса в ответе != 401.'
            )
            file_count += 1
            assert file_count != File.objects.count(), (
                'Удалось создать файл без авторизации.'
            )

    def test_create_invalid_file(self, user_client, tag_1, tag_2):
        file_count = File.objects.count()
        tag_1_name = tag_1.name
        tag_2_name = tag_2.name
        base = 'data:test.mp3;base64,'
        with open('/app/tests/fixtures/test_audio.txt', 'r') as file:
            source = file.read()
        audio_source = base + source
        invalid_data = [
            {
                'source': base + 'ololo',
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': 'test.mp3;base64,' + source,
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': 'data:.mp3;base64,' + source,
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': 'data:test.;base64,' + source,
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': 'data:testmp3;base64,' + source,
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': 'data:test.mp3base64,' + source,
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': 'data:test.mp3;base64' + source,
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': 'data:test.mp3;base64' + source,
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'type': 1,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': 'data:test.mp3;base64' + source,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': audio_source,
                'type': 6,
                'tags': [{'name': tag_1_name}, {'name': tag_2_name}]
            },
            {
                'source': audio_source,
                'type': 1,
                'tags': [tag_1_name, tag_2_name]
            },
            {
                'source': audio_source,
                'type': 3,
                'tags': []
            }
        ]
        for data in invalid_data:
            response = user_client.post(
                self.files_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                'Код статуса в ответе != 400.'
            )
            file_count += 1
            assert file_count != File.objects.count(), (
                f'Удалось создать файл с неправильными данными: {data}.'
            )

    def test_create_valid_playlist_admin(self, admin_client, admin_user, file_1):
        file_id = str(file_1.id)
        data = {
            'name': 'test',
            'files': [file_id]
        }
        pls_count = Playlist.objects.count()
        response = admin_client.post(
            self.playlists_url,
            data=data,
            format='json'
        )
        response_data = response.json()
        assert response.status_code == HTTPStatus.CREATED, (
            f'Код статуса в ответе != 201.\nДанные: {data}.\nОтвет: {response}'
        )
        pls_count += 1
        assert pls_count == Playlist.objects.count(), (
            'Не удалось создать плейлист.'
        )
        self.check_valid_create_playlist_response(data, admin_user, response_data)

    def test_create_valid_playlist_manager(self, manager_client, manager_user, file_1):
        file_id = str(file_1.id)
        data = {
            'name': 'test',
            'files': [file_id]
        }
        pls_count = Playlist.objects.count()
        response = manager_client.post(
            self.playlists_url,
            data=data,
            format='json'
        )
        response_data = response.json()
        assert response.status_code == HTTPStatus.CREATED, (
            f'Код статуса в ответе != 201.\nДанные: {data}.\nОтвет: {response}'
        )
        pls_count += 1
        assert pls_count == Playlist.objects.count(), (
            'Не удалось создать плейлист.'
        )
        self.check_valid_create_playlist_response(data, manager_user, response_data)

    def test_create_valid_playlist_user(self, user_client, file_1):
        file_id = str(file_1.id)
        data = {
            'name': 'test',
            'files': [file_id]
        }
        response = user_client.post(
            self.playlists_url,
            data=data,
            format='json'
        )
        pls_count = Playlist.objects.count()
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.'
        )
        pls_count += 1
        assert pls_count != Playlist.objects.count(), (
            'Удалось создать плейлист без должных прав.'
        )

    def test_create_valid_playlist_anon(self, anon_client, file_1):
        file_id = str(file_1.id)
        data = {
            'name': 'test',
            'files': [file_id]
        }
        response = anon_client.post(
            self.playlists_url,
            data=data,
            format='json'
        )
        pls_count = Playlist.objects.count()
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.'
        )
        pls_count += 1
        assert pls_count != Playlist.objects.count(), (
            'Удалось создать плейлист без авторизации.'
        )

    def test_create_invalid_playlist(self, admin_client, file_1, file_3):
        pls_count = Playlist.objects.count()
        file_1_id = str(file_1.id)
        file_3_id = str(file_3.id)
        invalid_data = [
            {
                'name': None,
                'files': [file_1_id]
            },
            {
                'name': 'test',
                'files': 'file_id'
            },
            {
                'name': 'test',
                'files': [file_1_id, file_3_id]
            },
            {
                'name': 'test',
                'files': [123]
            }
        ]
        for data in invalid_data:
            response = admin_client.post(
                self.playlists_url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400\n{data}.'
            )
            pls_count += 1
            assert pls_count != Playlist.objects.count(), (
                f'Удалось создать плейлист с неправильными данными: {data}.'
            )

    def test_update_file(self, admin_client, file_1):
        file_id = str(file_1.id)
        update_data = {
            'name': 'new_name',
            'description': 'description',
            'tags': [{'name': 'new_tag'}],
        }
        url = self.file_detail_url.format(file_id=file_id)
        for data in update_data:
            response = admin_client.patch(url, data=data, format='json')
            assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
                f'Код статуса в ответе != 405.Ответ: {response.json()}'
            )

    def test_partial_update_file(self, admin_client, file_1):
        file_id = str(file_1.id)
        update_data = [
            {'name': 'new_name'},
            {'description': 'description'},
            {'tags': [{'name': 'new_tag'}]},
        ]
        url = self.file_detail_url.format(file_id=file_id)
        for data in update_data:
            response = admin_client.patch(url, data=data, format='json')
            assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
                f'Код статуса в ответе != 405.Ответ: {response.json()}'
            )

    def test_valid_add_tags_file_admin(self, admin_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': ['new_tag', 'another_tag']}
        url = self.file_add_tags.format(file_id=file_id)
        response = admin_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_names = [tag.name for tag in file_tags]
        assert data['tags'][0] in file_tags_names, 'Новый тэг не присвоился файлу.'

    def test_valid_add_tags_file_manager(self, manager_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': ['new_tag']}
        url = self.file_add_tags.format(file_id=file_id)
        response = manager_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_names = [tag.name for tag in file_tags]
        assert data['tags'][0] in file_tags_names, 'Новый тэг не присвоился файлу.'

    def test_valid_add_tags_file_user(self, user_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': ['new_tag']}
        url = self.file_add_tags.format(file_id=file_id)
        response = user_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_names = [tag.name for tag in file_tags]
        assert data['tags'][0] not in file_tags_names, (
            'Новый тэг присвоился файлу без должных прав.'
        )

    def test_valid_add_tags_file_anon(self, anon_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': ['new_tag']}
        url = self.file_add_tags.format(file_id=file_id)
        response = anon_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_names = [tag.name for tag in file_tags]
        assert data['tags'][0] not in file_tags_names, (
            'Новый тэг присвоился файлу без авторизации.'
        )

    def test_invalid_add_tags_file(self, admin_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': [{'name': 'test'}]}
        url = self.file_add_tags.format(file_id=file_id)
        response = admin_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            f'Код статуса в ответе != 400.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_name_list = [tag.name for tag in file_tags]
        file_tags_name_set = set(tag.name for tag in file_tags)
        assert len(file_tags_name_list) == len(file_tags_name_set), (
            'Файл содержит два одинаковых тэга.'
        )

    def test_valid_remove_file_tags_admin(self, admin_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': ['test']}
        url = self.file_remove_tags.format(file_id=file_id)
        response = admin_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_names = [tag.name for tag in file_tags]
        assert data['tags'][0] not in file_tags_names, (
            'Не удалось убрать тэг.'
        )

    def test_valid_remove_file_tags_manager(self, manager_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': ['test']}
        url = self.file_remove_tags.format(file_id=file_id)
        response = manager_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_names = [tag.name for tag in file_tags]
        assert data['tags'][0] not in file_tags_names, (
            'Не удалось убрать тэг.'
        )

    def test_valid_remove_file_tags_user(self, user_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': ['test']}
        url = self.file_remove_tags.format(file_id=file_id)
        response = user_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_names = [tag.name for tag in file_tags]
        assert data['tags'][0] in file_tags_names, (
            'Удалось убрать тэг без должных прав.'
        )

    def test_valid_remove_file_tags_anon(self, anon_client, file_1):
        file_id = str(file_1.id)
        data = {'tags': ['test']}
        url = self.file_remove_tags.format(file_id=file_id)
        response = anon_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        file_tags = file_obj.tags.all()
        file_tags_names = [tag.name for tag in file_tags]
        assert data['tags'][0] in file_tags_names, (
            'Удалось убрать тэг без авторизации.'
        )

    def test_valid_partial_update_playlist_admin(self, admin_client, playlist_1):
        playlist_id = str(playlist_1.id)
        valid_data = TestFiles.get_valid_partial_update_playlist_data()
        url = self.playlist_detail_url.format(playlist_id=playlist_id)
        for data in valid_data:
            response = admin_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Код статуса в ответе != 200.'
                f'\nДанные: {data}.Ответ: {response_data}'
            )
            updated_key = ''.join(*data.keys())
            self.check_partial_update_response(data, response_data, updated_key)

    def test_valid_partial_update_playlist_manager(self, manager_client, playlist_1):
        playlist_id = str(playlist_1.id)
        valid_data = TestFiles.get_valid_partial_update_playlist_data()
        url = self.playlist_detail_url.format(playlist_id=playlist_id)
        for data in valid_data:
            response = manager_client.patch(url, data=data, format='json')
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Код статуса в ответе != 200.'
                f'\nДанные: {data}.Ответ: {response_data}'
            )
            updated_key = ''.join(data.keys())
            self.check_partial_update_response(data, response_data, updated_key)

    def test_valid_partial_update_playlist_user(
        self,
        user_client,
        playlist_1
    ):
        playlist_id = str(playlist_1.id)
        valid_data = TestFiles.get_valid_partial_update_playlist_data()
        url = self.playlist_detail_url.format(playlist_id=playlist_id)
        for data in valid_data:
            response = user_client.patch(url, data=data, format='json')
            assert response.status_code == HTTPStatus.FORBIDDEN, (
                f'Код статуса в ответе != 403.'
            )

    def test_valid_partial_update_playlist_anon(
        self,
        anon_client,
        playlist_1
    ):
        playlist_id = str(playlist_1.id)
        valid_data = TestFiles.get_valid_partial_update_playlist_data()
        url = self.playlist_detail_url.format(playlist_id=playlist_id)
        for data in valid_data:
            response = anon_client.patch(url, data=data, format='json')
            assert response.status_code == HTTPStatus.UNAUTHORIZED, (
                f'Код статуса в ответе != 401.'
            )

    def test_invalid_partial_update_playlist(
        self,
        admin_client,
        manager_user,
        playlist_1,
        file_3
    ):
        file_id = str(file_3.id)
        playlist_id = str(playlist_1.id)
        invalid_data = [
            {'name': None},
            {'files': file_id},
            {'files': ['file_id']},
            {'files': None}
        ]
        url = self.playlist_detail_url.format(playlist_id=playlist_id)
        for data in invalid_data:
            response = admin_client.patch(url, data=data, format='json')
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400.\nДанные: {data}'
            )

    def test_valid_add_files_playlist_admin(
        self,
        admin_client,
        playlist_1,
        file_5
    ):
        playlist_id = str(playlist_1.id)
        data = {'files': [str(file_5.id)]}
        url = self.playlist_add_files_url.format(playlist_id=playlist_id)
        response = admin_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        pls_obj = Playlist.objects.get(id=playlist_id)
        pls_files = pls_obj.files.all()
        pls_files_ids = [str(file.id) for file in pls_files]
        assert data['files'][0] in pls_files_ids, 'Новый файл не добавился в плейлист.'

    def test_valid_add_files_playlist_manager(
        self,
        manager_client,
        playlist_1,
        file_5
    ):
        playlist_id = str(playlist_1.id)
        data = {'files': [str(file_5.id)]}
        url = self.playlist_add_files_url.format(playlist_id=playlist_id)
        response = manager_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        pls_obj = Playlist.objects.get(id=playlist_id)
        pls_files = pls_obj.files.all()
        pls_files_ids = [str(file.id) for file in pls_files]
        assert data['files'][0] in pls_files_ids, 'Новый файл не добавился в плейлист.'

    def test_valid_add_files_playlist_user(
        self,
        user_client,
        playlist_1,
        file_5
    ):
        playlist_id = str(playlist_1.id)
        data = {'files': [str(file_5.id)]}
        url = self.playlist_add_files_url.format(playlist_id=playlist_id)
        response = user_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.Ответ: {response.json()}'
        )

    def test_valid_add_files_playlist_anon(
        self,
        anon_client,
        playlist_1,
        file_5
    ):
        playlist_id = str(playlist_1.id)
        data = {'files': [str(file_5.id)]}
        url = self.playlist_add_files_url.format(playlist_id=playlist_id)
        response = anon_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.Ответ: {response.json()}'
        )

    def test_invalid_add_files_playlist(
        self,
        admin_client,
        playlist_1,
        file_5,
        file_3
    ):
        playlist_id = str(playlist_1.id)
        invalid_data = [
            {'files': [str(file_3.id)]},
            {'files': ['file_3.id']},
            {'files': None},
            {'files': 'None'}
        ]
        url = self.playlist_add_files_url.format(playlist_id=playlist_id)
        for data in invalid_data:
            response = admin_client.post(url, data=data, format='json')
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                f'Код статуса в ответе != 400.\nДанные: {data}.\nОтвет: {response.json()}'
            )

    def test_valid_remove_files_playlist_admin(
        self,
        admin_client,
        playlist_5,
        file_5
    ):
        playlist_id = str(playlist_5.id)
        data = {'files': [str(file_5.id)]}
        url = self.playlist_remove_files_url.format(playlist_id=playlist_id)
        response = admin_client.post(
            url,
            data=data,
            format='json'
        )
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        pls_obj = Playlist.objects.get(id=playlist_id)
        pls_files = pls_obj.files.all()
        pls_files_ids = [str(file.id) for file in pls_files]
        assert data['files'][0] not in pls_files_ids, (
            'Новый файл не добавился в плейлист.'
        )

    def test_valid_remove_files_playlist_manager(
        self,
        manager_client,
        playlist_5,
        file_5
    ):
        playlist_id = str(playlist_5.id)
        data = {'files': [str(file_5.id)]}
        url = self.playlist_remove_files_url.format(playlist_id=playlist_id)
        response = manager_client.post(
            url,
            data=data,
            format='json'
        )
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.Ответ: {response.json()}'
        )
        pls_obj = Playlist.objects.get(id=playlist_id)
        pls_files = pls_obj.files.all()
        pls_files_ids = [str(file.id) for file in pls_files]
        assert data['files'][0] not in pls_files_ids, (
            'Новый файл не добавился в плейлист.'
        )

    def test_valid_remove_files_playlist_user(
        self,
        user_client,
        playlist_5,
        file_5
    ):
        playlist_id = str(playlist_5.id)
        data = {'files': [str(file_5.id)]}
        url = self.playlist_remove_files_url.format(playlist_id=playlist_id)
        response = user_client.post(
            url,
            data=data,
            format='json'
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.Ответ: {response.json()}'
        )

    def test_valid_remove_files_playlist_anon(
        self,
        anon_client,
        playlist_5,
        file_5
    ):
        playlist_id = str(playlist_5.id)
        data = {'files': [str(file_5.id)]}
        url = self.playlist_remove_files_url.format(playlist_id=playlist_id)
        response = anon_client.post(
            url,
            data=data,
            format='json'
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.Ответ: {response.json()}'
        )

    def test_invalid_remove_files_playlist(
        self,
        admin_client,
        playlist_1,
        file_5
    ):
        playlist_id = str(playlist_1.id)
        invalid_data = [
            {'files': ['file_5.id']},
            {'files': [None]},
            {'files': None},
            {'files': str(file_5.id)}
        ]
        url = self.playlist_remove_files_url.format(playlist_id=playlist_id)
        for data in invalid_data:
            response = admin_client.post(
                url,
                data=data,
                format='json'
            )
            assert response.status_code == HTTPStatus.BAD_REQUEST, (
                'Код статуса в ответе != 400.'
                f'\nДанные: {data}.\nОтвет: {response.json()}'
            )
