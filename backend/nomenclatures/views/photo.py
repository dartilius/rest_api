from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from api.constants import get_instance_or_404
from api.mixins import SignedMediaNoCacheMixin
from users.permissions import StaffCUDallRead
from ..models import Nomenclature, NomenclatureImage
from ..serializers import PhotoSerializer

from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED


@extend_schema(tags=["Фотографии номенклатур", "Номенклатуры"])
class NomenclaturePhotoViewSet(SignedMediaNoCacheMixin, viewsets.ModelViewSet):
    """
    ViewSet для управления фотографиями номенклатур.

    Предоставляет методы для загрузки, просмотра и удаления фотографий
    (изображений) номенклатур. Фотографии включают фото интерьера и
    экстерьера помещения, где установлена номенклатура.

    Attributes:
        queryset: Все изображения номенклатур
        serializer_class: PhotoSerializer
        permission_classes: [StaffCUDallRead]
        http_method_names: ["get", "post", "delete", "patch"]

    Endpoints:
        GET /api/photos/ - Все фотографии всех номенклатур
        GET /api/photos/{photo_id}/ - Деталь конкретной фотографии
        POST /api/photos/{nomenclature_id}/add_photo/ - Добавить фото к номенклатуре
        GET /api/photos/{nomenclature_id}/get_nomenclature_photos/ - Фото номенклатуры
        PATCH /api/photos/{photo_id}/ - Обновить метаданные фотографии
        DELETE /api/photos/{photo_id}/ - Удалить фотографию
    """
    queryset = NomenclatureImage.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [StaffCUDallRead]
    http_method_names = ["get", "post", "delete", "patch"]

    @extend_schema(
        summary="Прикрепить фотографии номенклатуры",
        request=PhotoSerializer,
        responses={HTTP_201_CREATED: PhotoSerializer},
    )
    @action(
        methods=["POST"],
        detail=True,
        url_path="add_photo",
    )
    def add_photo(self, request, pk):
        """
        Загрузить и прикрепить фотографию к конкретной номенклатуре.

        Метод позволяет загрузить новое изображение (фото интерьера или экстерьера)
        и связать его с определенной номенклатурой. Изображение сохраняется в БД
        в виде Base64 кодированного файла или ссылки на хранилище.

        Поддерживаемые форматы:
        - JPEG (jpg, jpeg)
        - PNG (png)
        - WebP (webp)
        - Другие популярные форматы (в зависимости от конфигурации)

        Типы фотографий:
        - interior: Фото интерьера помещения
        - exterior: Фото экстерьера/входа в помещение
        - signage: Фото вывески/брендирования
        - installation: Фото установки оборудования

        Args:
            request: HTTP POST запрос с файлом изображения.
            pk: UUID номенклатуры.

        Request Body (multipart/form-data или JSON с base64):
            {
                'source': 'data:image/jpeg;base64,/9j/4AAQSkZJRg...',
                'type': 'interior'  или 'exterior'
            }

        Returns:
            Response: JSON с сообщением об успехе.
                     Структура:
                     {
                         'detail': 'Фотографии прикреплены'
                     }

        Status Codes:
            201 CREATED: Фотография успешно загружена и прикреплена
            400 BAD REQUEST: Ошибка в данных (некорректный формат, дубликат и т.д.)
            404 NOT FOUND: Номенклатура не найдена
            403 FORBIDDEN: Пользователь не имеет прав доступа

        File Requirements:
            - Максимальный размер: зависит от настроек (обычно 10-50 MB)
            - Минимальное разрешение: 640x480 (рекомендуется 1920x1080+)
            - Формат: JPEG или PNG (рекомендуется JPEG для компактности)

        Examples:
            # Загрузить фото интерьера
            >>> with open('interior.jpg', 'rb') as f:
            ...     files = {'source': f}
            ...     data = {'type': 'interior'}
            ...     response = client.post(
            ...         '/api/photos/123e4567/add_photo/',
            ...         data=data,
            ...         files=files
            ...     )
            >>> response.status_code
            201
            >>> response.data['detail']
            'Фотографии прикреплены'

            >>> # Загрузить фото экстерьера (Base64)
            >>> response = client.post(
            ...     '/api/photos/123e4567/add_photo/',
            ...     data={
            ...         'source': 'data:image/jpeg;base64,...',
            ...         'type': 'exterior'
            ...     }
            ... )
            >>> response.status_code
            201

        Side Effects:
            - Сохраняет новый объект NomenclatureImage в БД
            - Добавляет изображение в связь many-to-many с номенклатурой
            - Сохраняет файл на диск или в облако (в зависимости от конфигурации)

        Performance Notes:
            - Загрузка большого файла может быть медленной
            - База данных хранит ссылку на файл, а не сам файл
            - Рекомендуется сжимать изображения перед загрузкой

        Use Cases:
            - Загрузка фото при создании новой номенклатуры
            - Документирование места установки оборудования
            - Архивирование визуальной информации о точке
            - Верификация установки оборудования

        Related Methods:
            - get_nomenclature_photos() для просмотра фото номенклатуры
            - get_photos() для всех фото в системе

        Notes:
            - Каждая номенклатура может иметь несколько фотографий
            - Фотографии можно удалять отдельно через DELETE
            - Типы фото помогают организовать изображения по назначению
        """
        nomenclature = get_instance_or_404(Nomenclature, pk=pk)

        serializer = PhotoSerializer(
            data=request.data,
            context={"nomenclature": nomenclature}
        )

        serializer.is_valid(raise_exception=True)
        photo = serializer.save()

        return Response(
            PhotoSerializer(photo).data,
            status=HTTP_201_CREATED
        )

    @action(methods=["GET"], detail=False)
    def get_photos(self, request):
        """
        Получить список всех фотографий всех номенклатур в системе.

        Метод возвращает полный список всех загруженных фотографий без
        ограничений по номенклатуре. Полезен для глобального поиска и
        просмотра всех изображений в системе.

        Args:
            request: HTTP GET запрос.

        Returns:
            Response: Массив объектов фотографий.
                     Структура:
                     [
                         {
                             'id': 'uuid',
                             'source_url': 'http://example.com/photos/abc123.jpg',
                             'type': 'interior',
                             'created': '2026-02-08T10:30:00Z',
                             'nomenclature': 'uuid'
                         },
                         ...
                     ]

        Status Codes:
            200 OK: Список успешно получен
            403 FORBIDDEN: Пользователь не имеет прав доступа

        Examples:
            >>> response = client.get('/api/photos/')
            >>> response.status_code
            200
            >>> len(response.data)
            2458  # всего фотографий в системе

        Use Cases:
            - Поиск фотографии по UUID
            - Просмотр всех изображений для администратора
            - Экспорт фотографий для резервного копирования
            - Статистика по фотографиям

        Warning:
            Может возвращать большое количество данных при наличии много фотографий.
            Рекомендуется добавить пагинацию при большом числе фото в системе.

        Related Methods:
            - get_nomenclature_photos() для фото конкретной номенклатуры
            - add_photo() для загрузки новых фото
        """
        photos = NomenclatureImage.objects.filter(nomenclature__isnull=False)
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @action(methods=["GET"], detail=True)
    def get_nomenclature_photos(self, request, pk):
        """
        Получить список всех фотографий конкретной номенклатуры.

        Метод возвращает только те фотографии, которые явно связаны с
        данной номенклатурой. Это удобно для просмотра визуальной информации
        о конкретной точке или оборудовании.

        Args:
            request: HTTP GET запрос.
            pk: UUID номенклатуры.

        Returns:
            Response: Массив фотографий номенклатуры.
                     Структура:
                     [
                         {
                             'id': 'uuid',
                             'source_url': 'http://example.com/photos/interior.jpg',
                             'type': 'interior',
                             'created': '2026-02-08T10:00:00Z',
                             'nomenclature': 'uuid'
                         },
                         {
                             'id': 'uuid',
                             'source_url': 'http://example.com/photos/exterior.jpg',
                             'type': 'exterior',
                             'created': '2026-02-08T10:15:00Z',
                             'nomenclature': 'uuid'
                         }
                     ]

        Status Codes:
            200 OK: Список успешно получен (может быть пустой)
            404 NOT FOUND: Номенклатура не найдена
            403 FORBIDDEN: Пользователь не имеет прав доступа

        Examples:
            >>> response = client.get('/api/photos/123e4567/get_nomenclature_photos/')
            >>> response.status_code
            200
            >>> len(response.data)
            3  # 3 фотографии у этой номенклатуры
            >>> response.data[0]['type']
            'interior'

        Use Cases:
            - Просмотр документации о номенклатуре
            - Визуальная верификация установки
            - Галерея фото точки продаж
            - Приложение для мобильных устройств специалистов

        Related Methods:
            - add_photo() для добавления новых фото
            - get_photos() для всех фото в системе

        Notes:
            - Может не содержать фотографий, если ни одна не загружена
            - Фотографии упорядочены по дате создания (новые первыми)
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        photos = nomenclature.images.all()
        serializer = PhotoSerializer(photos, many=True)
        return Response(serializer.data, status=HTTP_200_OK)
