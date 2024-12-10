import pytest
from dotenv import load_dotenv
from http import HTTPStatus

from files.models import File, Playlist, Tag, TYPES

load_dotenv()


@pytest.mark.django_db(transaction=True)
# @pytest.mark.skip(reason='Чтобы быстрее проверять новые тесты')
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

    def test_get_file_list_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        file_1
    ):
        file_count = File.objects.count()
        file_id = str(file_1.id)
        file_name = file_1.name
        file_length = file_1.length.strftime('%H:%M:%S')
        file_size = file_1.size
        file_type = TYPES[file_1.type]
        file_tags = [tag.name for tag in file_1.tags.all()]
        clients = [admin_client, manager_client, superuser_client, user_client]
        for client in clients:
            response = client.get(self.files_url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Пользователь {client} не имеет доступ к странице '
                f'списка файлов.\nОтвет: {response_data}'
            )
            assert response_data['count'] == file_count, (
                'Кол-во элементов в ответе не равно кол-ву файлов в базе.'
            )
            assert 'id' in response_data['results'][0], (
                'Ответ не содержит айди файла'
            )
            assert response_data['results'][0]['id'] == file_id, (
                'Айди файла в ответе не совпадает с айди файла в базе'
            )
            assert 'name' in response_data['results'][0], (
                'Ответ не содержит название файла'
            )
            assert response_data['results'][0]['name'] == file_name, (
                'Название файла в ответе не совпадает с названием файла в базе'
            )
            assert 'length' in response_data['results'][0], (
                'Ответ не содержит продолжительность файла'
            )
            assert response_data['results'][0]['length'] == file_length, (
                'Продолжительность файла в ответе не совпадает с '
                'продолжительностью файла в базе'
            )
            assert 'size' in response_data['results'][0], (
                'Ответ не содержит размер файла'
            )
            assert response_data['results'][0]['size'] == file_size, (
                'Размер файла в ответе не совпадает с размером файла в базе'
            )
            assert 'type' in response_data['results'][0], (
                'Ответ не содержит тип файла'
            )
            assert response_data['results'][0]['type'] == file_type, (
                'Тип файла в ответе не совпадает с типом файла в базе'
            )
            assert 'tags' in response_data['results'][0], (
                'Ответ не содержит тэги файла'
            )
            assert response_data['results'][0]['tags'] == file_tags, (
                'Тэги файла в ответе не совпадает с тэгами файла в базе'
            )

    def test_get_file_detail_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        user,
        file_1
    ):
        file_id = str(file_1.id)
        file_name = file_1.name
        file_length = file_1.length.strftime('%H:%M:%S')
        file_size = file_1.size
        file_type = TYPES[file_1.type]
        file_tags = [{'id': tag.id, 'name': tag.name} for tag in file_1.tags.all()]
        file_owner = user.full_name
        file_hash = file_1.hash
        file_created = file_1.created.strftime('%Y-%m-%d %H:%M:%S')
        url = self.file_detail_url.format(file_id=file_id)
        clients = [admin_client, manager_client, superuser_client, user_client]
        for client in clients:
            response = client.get(url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Пользователь {client} не имеет доступ к странице '
                f'расшифровки файла.\nОтвет: {response_data}'
            )
            assert 'id' in response_data, (
                'Ответ не содержит айди файла'
            )
            assert response_data['id'] == file_id, (
                'Айди файла в ответе не совпадает с айди файла в базе'
            )
            assert 'name' in response_data, (
                'Ответ не содержит название файла'
            )
            assert response_data['name'] == file_name, (
                'Название файла в ответе не совпадает с названием файла в базе'
            )
            assert 'length' in response_data, (
                'Ответ не содержит продолжительность файла'
            )
            assert response_data['length'] == file_length, (
                'Продолжительность файла в ответе не совпадает с '
                'продолжительностью файла в базе'
            )
            assert 'size' in response_data, (
                'Ответ не содержит размер файла'
            )
            assert response_data['size'] == file_size, (
                'Размер файла в ответе не совпадает с размером файла в базе'
            )
            assert 'type' in response_data, (
                'Ответ не содержит тип файла'
            )
            assert response_data['type'] == file_type, (
                'Тип файла в ответе не совпадает с типом файла в базе'
            )
            assert 'tags' in response_data, (
                'Ответ не содержит тэги файла'
            )
            assert response_data['tags'] == file_tags, (
                'Тэги файла в ответе не совпадает с тэгами файла в базе'
            )
            assert 'owner' in response_data, (
                'Ответ не содержит владельца файла'
            )
            assert response_data['owner'] == file_owner, (
                'Владелец файла в ответе не совпадает с владельцем файла в базе'
            )
            assert 'hash' in response_data, (
                'Ответ не содержит хэш файла'
            )
            assert response_data['hash'] == file_hash, (
                'Хэш файла в ответе не совпадает с хэшем файла в базе'
            )
            assert 'created' in response_data, (
                'Ответ не содержит дату создания файла'
            )
            assert response_data['created'] == file_created, (
                'Дата создания файла в ответе не совпадает с '
                'датой создания файла в базе'
            )

    def test_get_playlist_list_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        user,
        playlist_1
    ):
        playlist_count = Playlist.objects.count()
        playlist_id = str(playlist_1.id)
        playlist_name = playlist_1.name
        playlist_owner = user.full_name
        playlist_files_count = playlist_1.files.count()
        clients = [admin_client, manager_client, superuser_client, user_client]
        for client in clients:
            response = client.get(self.playlists_url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Пользователь {client} не имеет доступ к странице '
                f'списка плейлистов.\nОтвет: {response_data}.'
            )
            assert response_data['count'] == playlist_count, (
                'Кол-во элементов в ответе не равно кол-ву плейлистов в базе.'
            )
            assert 'id' in response_data['results'][0], (
                'Ответ не содержит айди плейлиста'
            )
            assert response_data['results'][0]['id'] == playlist_id, (
                'Айди плейлиста в ответе не совпадает с айди плейлиста в базе'
            )
            assert 'name' in response_data['results'][0], (
                'Ответ не содержит название плейлиста'
            )
            assert response_data['results'][0]['name'] == playlist_name, (
                'Название плейлиста в ответе не совпадает с '
                'названием плейлиста в базе'
            )
            assert 'files_count' in response_data['results'][0], (
                'Ответ не содержит кол-во файлов плейлиста'
            )
            assert response_data['results'][0]['files_count'] == playlist_files_count, (
                'Кол-во файлов плейлиста в ответе не совпадает с '
                'кол-вом файлов плейлиста в базе'
            )
            assert 'owner' in response_data['results'][0], (
                'Ответ не содержит владельца плейлиста'
            )
            assert response_data['results'][0]['owner'] == playlist_owner, (
                'Владелец плейлиста в ответе не совпадает с '
                'владельцем плейлиста в базе'
            )

    def test_get_playlist_detail_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        user,
        playlist_1
    ):
        playlist_id = str(playlist_1.id)
        playlist_name = playlist_1.name
        playlist_description = playlist_1.description
        playlist_owner = user.full_name
        playlist_files_count = playlist_1.files.count()
        playlist_files = [
            {'id': str(file.id),
             'name': file.name,
             'url': file.url} for file in playlist_1.files.all()
        ]
        url = self.playlist_detail_url.format(playlist_id=playlist_id)
        clients = [admin_client, manager_client, superuser_client, user_client]
        for client in clients:
            response = client.get(url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Пользователь {client} не имеет доступ к странице '
                f'расшифровки плейлиста.\nОтвет: {response_data}.'
            )
            assert 'id' in response_data, (
                'Ответ не содержит айди плейлиста'
            )
            assert response_data['id'] == playlist_id, (
                'Айди плейлиста в ответе не совпадает с айди плейлиста в базе'
            )
            assert 'name' in response_data, (
                'Ответ не содержит название плейлиста'
            )
            assert 'description' in response_data, (
                'Ответ не содержит описание плейлиста'
            )
            assert response_data['description'] == playlist_description, (
                'Описание плейлиста в ответе не совпадает с '
                'описанием плейлиста в базе'
            )
            assert response_data['name'] == playlist_name, (
                'Название плейлиста в ответе не совпадает с '
                'названием плейлиста в базе'
            )
            assert 'files_count' in response_data, (
                'Ответ не содержит кол-во файлов плейлиста'
            )
            assert response_data['files_count'] == playlist_files_count, (
                'Кол-во файлов плейлиста в ответе не совпадает с '
                'кол-вом файлов плейлиста в базе'
            )
            assert 'owner' in response_data, (
                'Ответ не содержит владельца плейлиста'
            )
            assert response_data['owner'] == playlist_owner, (
                'Владелец плейлиста в ответе не совпадает с '
                'владельцем плейлиста в базе'
            )
            assert 'files' in response_data, (
                'Ответ не содержит списка файлов плейлиста'
            )
            assert response_data['files'] == playlist_files, (
                'Список файлов плейлиста в ответе не совпадает со '
                'списком файлов плейлиста в базе'
            )

    def test_get_tag_list_auth(
        self,
        admin_client,
        manager_client,
        superuser_client,
        user_client,
        tag_1
    ):
        tag_count = Tag.objects.count()
        tag_id = tag_1.id
        tag_name = tag_1.name
        clients = [admin_client, manager_client, superuser_client, user_client]
        for client in clients:
            response = client.get(self.tags_url)
            response_data = response.json()
            assert response.status_code == HTTPStatus.OK, (
                f'Пользователь {client} не имеет доступ к странице '
                f'списка тэгов.\nОтвет: {response_data}.'
            )
            assert response_data['count'] == tag_count, (
                'Кол-во элементов в ответе не совпадает с кол-вом тэгов в базе'
            )
            assert 'id' in response_data['results'][0], (
                'Ответ не содержит айди тэга'
            )
            assert response_data['results'][0]['id'] == tag_id, (
                'Айди тэга в ответе не совпадает с айди тэга в базе'
            )
            assert 'name' in response_data['results'][0], (
                'Ответ не содержит название тэга'
            )
            assert response_data['results'][0]['name'] == tag_name, (
                'Название тэга в ответе не совпадает с названием тэга в базе'
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
        data = {
            'name': 'new_name',
            'tags': [{'name': 'new_tag'}],
        }
        url = self.file_detail_url.format(file_id=file_id)
        response = admin_client.patch(url, data=data, format='json')
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
            f'Код статуса в ответе != 405.Ответ: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.name != data['name'], 'Имя файла обновилось'
        file_tags = file_obj.tags.values_list('name', flat=True)
        assert file_tags != data['tags'], 'Тэги файла обновились'

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

    def test_invalid_remove_file_tags(self, admin_client, file_1):
        file_id = str(file_1.id)
        data = {
            'tags': ['no_tag']
        }
        url = self.file_remove_tags.format(file_id=file_id)
        response = admin_client.post(url, data=data, format='json')
        assert response.status_code == HTTPStatus.NOT_FOUND, (
            f'Код статуса в ответе != 404.\nОтвет: {response.json()}'
        )

    def test_update_playlist(self, admin_client, playlist_1, file_5):
        playlist_id = str(playlist_1.id)
        data = {
            'name': 'new_name',
            'description': 'description',
            'files': [str(file_5.id)]
        }
        url = self.playlist_detail_url.format(playlist_id=playlist_id)
        response = admin_client.put(url, data=data, format='json')
        assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED, (
            f'Код статуса в ответе != 405.\nОтвет: {response.json()}'
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
        assert data['files'][0] in pls_files_ids, (
            'Новый файл не добавился в плейлист.'
        )

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
        assert data['files'][0] in pls_files_ids, (
            'Новый файл не добавился в плейлист.'
        )

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
        file_3,
        file_1
    ):
        playlist_id = str(playlist_1.id)
        invalid_data = [
            {'files': [str(file_3.id)]},
            {'files': [str(file_1.id)]},
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
            'Файл не был убран из плейлиста.'
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
            'Файл не был убран из плейлиста.'
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

    def test_delete_file_admin(
        self,
        admin_client,
        file_1
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = admin_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is False, (
            'Статус актуальности файла не изменился.'
        )

    def test_delete_file_manager(
        self,
        manager_client,
        file_1
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = manager_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is False, (
            'Статус актуальности файла не изменился.'
        )

    def test_delete_file_owner(
        self,
        user_client,
        file_1
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = user_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is False, (
            'Статус актуальности файла не изменился.'
        )

    def test_delete_file_not_owner(
        self,
        another_user_client,
        file_1
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = another_user_client.delete(url)
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is not False, (
            'Статус актуальности файла изменился без должных прав.'
        )

    def test_delete_file_anon(
        self,
        anon_client,
        file_1
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = anon_client.delete(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is not False, (
            'Статус актуальности файла изменился без авторизации.'
        )

    def test_delete_file_in_playlist_admin(
        self,
        admin_client,
        file_1,
        playlist_5
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = admin_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is False, (
            'Статус актуальности файла не изменился.'
        )
        pls_obj = Playlist.objects.get(id=str(playlist_5.id))
        pls_files = list(map(str, [
                file_id
                for file_id
                in pls_obj.files.values_list('id', flat=True)
            ]))
        assert file_id not in pls_files, 'Файл остался в плейлисте'

    def test_delete_file_in_playlist_manager(
        self,
        manager_client,
        file_1,
        playlist_5
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = manager_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is False, (
            'Статус актуальности файла не изменился.'
        )
        pls_obj = Playlist.objects.get(id=str(playlist_5.id))
        pls_files = list(map(str, [
                file_id
                for file_id
                in pls_obj.files.values_list('id', flat=True)
            ]))
        assert file_id not in pls_files, 'Файл остался в плейлисте'

    def test_delete_file_in_playlist_owner(
        self,
        user_client,
        file_1,
        playlist_5
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = user_client.delete(url)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is False, (
            'Статус актуальности файла не изменился.'
        )
        pls_obj = Playlist.objects.get(id=str(playlist_5.id))
        pls_files = list(map(str, [
                file_id
                for file_id
                in pls_obj.files.values_list('id', flat=True)
            ]))
        assert file_id not in pls_files, 'Файл остался в плейлисте'

    def test_delete_file_in_playlist_not_owner(
        self,
        another_user_client,
        file_1,
        playlist_5
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = another_user_client.delete(url)
        assert response.status_code == HTTPStatus.FORBIDDEN, (
            f'Код статуса в ответе != 403.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is not False, (
            'Статус актуальности файла изменился без должных прав.'
        )
        pls_obj = Playlist.objects.get(id=str(playlist_5.id))
        pls_files = list(map(str, [
                file_id
                for file_id
                in pls_obj.files.values_list('id', flat=True)
            ]))
        assert file_id in pls_files, 'Файл остался в плейлисте'

    def test_delete_file_in_playlist_anon(
        self,
        anon_client,
        file_1,
        playlist_5
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = anon_client.delete(url)
        assert response.status_code == HTTPStatus.UNAUTHORIZED, (
            f'Код статуса в ответе != 401.\nОтвет: {response.json()}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is not False, (
            'Статус актуальности файла изменился без авторизации.'
        )
        pls_obj = Playlist.objects.get(id=str(playlist_5.id))
        pls_files = list(map(str, [
                file_id
                for file_id
                in pls_obj.files.values_list('id', flat=True)
            ]))
        assert file_id in pls_files, (
            'Файл был удалён из плейлиста без авторизации'
        )

    def test_delete_active_playlist(
        self,
        admin_client,
        playlist_1,
        adorder,
        nomenclature
    ):
        pls_count = Playlist.objects.count()
        playlist_id = str(playlist_1.id)
        url = self.playlist_detail_url.format(playlist_id=playlist_id)
        response = admin_client.delete(url)
        assert response.status_code == HTTPStatus.BAD_REQUEST, (
            f'Код статуса в ответе != 400.\nОтвет: {response.json()}'
        )
        pls_count -= 1
        assert pls_count != Playlist.objects.count(), (
            'Удалось удалить активный плейлист.'
        )

    def test_get_stat_ad(
        self,
        admin_client,
        file_3,
        ad_stat
    ):
        file_id = str(file_3.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = admin_client.get(url + 'stat/')
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response_data}'
        )
        assert 'played' in response_data[0], (
            'В ответе нет информации о времени, когда сыграл файл.'
        )
        assert 'length' in response_data[0], (
            'В ответе нет информации о времени, сколько играл файл.'
        )
        assert 'client' in response_data[0], (
            'В ответе нет информации о номенклатуре.'
        )
        assert 'ad_block' in response_data[0], (
            'В ответе нет информации о рекламном блоке.'
        )

    def test_get_stat_music(
        self,
        admin_client,
        file_1,
        music_stat
    ):
        file_id = str(file_1.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = admin_client.get(url + 'stat/')
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response_data}'
        )
        assert 'played' in response_data[0], (
            'В ответе нет информации о времени, когда сыграл файл.'
        )
        assert 'length' in response_data[0], (
            'В ответе нет информации о времени, сколько играл файл.'
        )
        assert 'client' in response_data[0], (
            'В ответе нет информации о номенклатуре.'
        )

    def test_get_stat_image(
        self,
        admin_client,
        file_2,
        image_stat
    ):
        file_id = str(file_2.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = admin_client.get(url + 'stat/')
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response_data}'
        )
        assert 'played' in response_data[0], (
            'В ответе нет информации о времени, когда сыграл файл.'
        )
        assert 'length' in response_data[0], (
            'В ответе нет информации о времени, сколько играл файл.'
        )
        assert 'client' in response_data[0], (
            'В ответе нет информации о номенклатуре.'
        )

    def test_get_stat_video(
        self,
        admin_client,
        file_3,
        video_stat
    ):
        file_id = str(file_3.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = admin_client.get(url + 'stat/')
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response_data}'
        )
        assert 'played' in response_data[0], (
            'В ответе нет информации о времени, когда сыграл файл.'
        )
        assert 'length' in response_data[0], (
            'В ответе нет информации о времени, сколько играл файл.'
        )
        assert 'client' in response_data[0], (
            'В ответе нет информации о номенклатуре.'
        )

    def test_get_stat_ticker(
        self,
        admin_client,
        file_4,
        ticker_stat
    ):
        file_id = str(file_4.id)
        url = self.file_detail_url.format(file_id=file_id)
        response = admin_client.get(url + 'stat/')
        response_data = response.json()
        assert response.status_code == HTTPStatus.OK, (
            f'Код статуса в ответе != 200.\nОтвет: {response_data}'
        )
        assert 'played' in response_data[0], (
            'В ответе нет информации о времени, когда сыграл файл.'
        )
        assert 'length' in response_data[0], (
            'В ответе нет информации о времени, сколько играл файл.'
        )
        assert 'client' in response_data[0], (
            'В ответе нет информации о номенклатуре.'
        )


@pytest.mark.django_db(transaction=True, databases=['default', 'clickhouse'])
# @pytest.mark.skip
class TestNew:

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


@pytest.mark.django_db(transaction=True)
class TestMockCeleryTasks:
    from orders.models import AdOrder, BgOrder
    from tasks.models import Task

    @staticmethod
    def update_ad_order_task(
            order_list: list[str],
            files: list[dict[str, str]] | list[str],
            action_type
    ):
        Task = TestMockCeleryTasks.Task
        AdOrder = TestMockCeleryTasks.AdOrder
        orders = AdOrder.objects.filter(id__in=order_list)
        UPDATE_AD = 14
        task_list = []
        for order in orders:
            task_list.append(
                Task(
                    owner=order.owner,
                    client=order.client,
                    type=UPDATE_AD,
                    parameters={
                        'order_id': str(order.id),
                        'update_type': action_type,
                        'files': files
                    }
                )
            )
        Task.objects.bulk_create(task_list)
        return f'Обновлено заказов: {len(task_list)}'

    @staticmethod
    def update_bg_order_task(
            order_list: list[str],
            files: list[dict[str, str]] | list[str],
            action_type
    ):
        from api.constants import get_bg_task_type
        Task = TestMockCeleryTasks.Task
        BgOrder = TestMockCeleryTasks.BgOrder
        orders = BgOrder.objects.filter(id__in=order_list)
        task_type = get_bg_task_type(orders[0].order_type, action='update')
        task_list = []
        for order in orders:
            task_list.append(
                Task(
                    owner=order.owner,
                    client=order.client,
                    type=task_type,
                    parameters={
                        'order_id': str(order.id),
                        'update_type': action_type,
                        'files': files
                    }
                )
            )
        Task.objects.bulk_create(task_list)
        return f'Репликаций создано: {len(task_list)}'

    @staticmethod
    def check_for_orders(pls_obj: Playlist | list[Playlist]) -> list | None:
        from django.core.exceptions import ValidationError as DjangoValidationError
        from itertools import chain
        AdOrder = TestMockCeleryTasks.AdOrder
        BgOrder = TestMockCeleryTasks.BgOrder
        try:
            orders = chain(
                AdOrder.objects.filter(playlist=pls_obj),
                BgOrder.objects.filter(playlist=pls_obj)
            )
        except DjangoValidationError:
            orders = chain(
                AdOrder.objects.filter(playlist__in=pls_obj),
                BgOrder.objects.filter(playlist__in=pls_obj)
            )
        orders = list(orders)
        try:
            test = orders[0]
            del test
        except IndexError:
            return None
        else:
            return orders

    @staticmethod
    def perform_remove_files(playlists: Playlist | list[Playlist],
                             files: list[str]) -> list | None:
        def _remove_files_and_update_orders(playlist, file_list) -> None:
            from copy import deepcopy
            playlist_files = list(map(str, [
                file_id
                for file_id
                in playlist.files.values_list('id', flat=True)
            ]))
            actual_file_list = deepcopy(file_list)
            for file in file_list:
                if file in playlist_files:
                    playlist.files.remove(file)
                else:
                    actual_file_list.remove(file)
            playlist.save()
            orders = TestMockCeleryTasks.check_for_orders(playlists)
            if orders:
                TestMockCeleryTasks.perform_update_orders(
                    orders,
                    actual_file_list,
                    action_type='remove_files'
                )
            return

        data = []
        if isinstance(playlists, Playlist):
            data.append(_remove_files_and_update_orders(playlists, files))
        else:
            for playlist in playlists:
                data.append(_remove_files_and_update_orders(playlist, files))
        return data if data else None

    @staticmethod
    def perform_update_orders(order_list: list, files: list, action_type: str):
        AdOrder = TestMockCeleryTasks.AdOrder
        update_ad_order_task = TestMockCeleryTasks.update_ad_order_task
        update_bg_order_task = TestMockCeleryTasks.update_bg_order_task
        ad_orders = []
        bg_orders = []
        for order in order_list:
            if isinstance(order, AdOrder):
                ad_orders.append(str(order.id))
            else:
                bg_orders.append(str(order.id))
        if ad_orders:
            update_ad_order_task(ad_orders, files, action_type)
        if bg_orders:
            update_bg_order_task(bg_orders, files, action_type)

    @staticmethod
    def delete_file(file_id):
        from rest_framework.response import Response
        file = File.objects.get(id=file_id)
        playlists = list(Playlist.objects.filter(files__id=file_id))
        if playlists:
            data = TestMockCeleryTasks.perform_remove_files(playlists, [file_id])
        file.is_active = False
        file.save(update_fields=['is_active'])
        return Response(
            data=data if data else None,
            status=HTTPStatus.NO_CONTENT
        )

    @staticmethod
    def delete_playlist(playlist):
        """Запрет на удаление плейлиста, если он сейчас где-то играет."""
        from rest_framework.exceptions import ValidationError
        orders = TestMockCeleryTasks.check_for_orders(playlist)
        if orders:
            orders_names = [order.name for order in orders]
            return ValidationError(
                'Нельзя удалить плейлист, т.к. он указан в активных заказах: '
                f'{orders_names}'
            )

    def test_delete_file_in_adorder_playlist(
        self,
        file_1,
        playlist_1,
        adorder,
        nomenclature
    ):
        Task = TestMockCeleryTasks.Task
        task_count = Task.objects.count()
        file_id = str(file_1.id)
        response = self.delete_file(file_id)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.\nОтвет: {response.data}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is False, (
            'Статус актуальности файла не изменился.'
        )
        pls_obj = Playlist.objects.get(id=str(playlist_1.id))
        pls_files = list(map(str, [
                file_id
                for file_id
                in pls_obj.files.values_list('id', flat=True)
            ]))
        assert file_id not in pls_files, 'Файл остался в плейлисте'
        task_count += 1
        assert task_count == Task.objects.count(), (
            'Репликация на обновление активного заказа не была создана'
        )
        task = Task.objects.last()
        check_task_params = {
            'order_id': str(adorder.id),
            'update_type': 'remove_files',
            'files': [file_id]
        }
        assert task.parameters == check_task_params, (
            'Параметры репликации не правильные.'
        )

    def test_delete_file_in_bgorder_playlist(
        self,
        file_1,
        playlist_1,
        bgorder,
        nomenclature
    ):
        from api.constants import get_bg_task_type
        Task = TestMockCeleryTasks.Task
        task_count = Task.objects.count()
        file_id = str(file_1.id)
        response = self.delete_file(file_id)
        assert response.status_code == HTTPStatus.NO_CONTENT, (
            f'Код статуса в ответе != 204.\nОтвет: {response.data}'
        )
        file_obj = File.objects.get(id=file_id)
        assert file_obj.is_active is False, (
            'Статус актуальности файла не изменился.'
        )
        pls_obj = Playlist.objects.get(id=str(playlist_1.id))
        pls_files = list(map(str, [
                file_id
                for file_id
                in pls_obj.files.values_list('id', flat=True)
            ]))
        assert file_id not in pls_files, 'Файл остался в плейлисте'
        task_count += 1
        assert task_count == Task.objects.count(), (
            'Репликация на обновление активного заказа не была создана'
        )
        task = Task.objects.last()
        check_task_params = {
            'order_id': str(bgorder.id),
            'update_type': 'remove_files',
            'files': [file_id]
        }
        assert task.parameters == check_task_params, (
            'В репликации указаны не правильные параметры.'
        )
        check_task_type = get_bg_task_type(bgorder.order_type, 'update')
        assert task.type == check_task_type, 'Репликация имеет не правильный тип'
