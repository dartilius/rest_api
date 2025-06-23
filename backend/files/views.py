import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiExample
)
from http import HTTPStatus
from itertools import chain
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
)
from uuid import UUID

from api.constants import (
    get_instance_or_404,
    restricted_update,
    DEFAULT_SCHEMA_RESPONSES,
    DEFAULT_SCHEMA_EXAMPLES, DetailSerializer
)
from ch_statistic.models import (
    ADStat,
    MusicStat,
    ImageStat,
    VideoStat,
    TickerStat
)
from ch_statistic.serializers import (
    FileAdStatSerializer,
    FileMusicStatSerializer,
    FileImageStatSerializer,
    FileVideoStatSerializer,
    FileTickerStatSerializer, BaseFileSerializer
)

from files.filters import FileFilter, PlaylistFilter
from files.serializers import (
    PlaylistSerializer,
    PlaylistListSerializer,
    FileSerializer,
    FileListSerializer,
    TagSerializer, FileSourceSerializer, TagsFileSerializer
)
from files.models import Playlist, File, Tag, TYPES
from orders.models import AdOrder, BgOrder
from orders.tasks import (
    add_or_remove_files_ad_order_task,
    add_or_remove_files_bg_order_task
)
from users.permissions import StaffCUDAuthRetrieve, OwnerAndStaffCRUD


class NoUpdateViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin
):
    """Вьюсет без поддержки методов PUT и PATCH."""

@extend_schema_view(
    list=extend_schema(
        summary='Получить пагинированный список тэгов',
        examples=[
            OpenApiExample(
                'Список тегов',
                response_only=True,
                value={
                    'id': 1, 'name': 'Новый год'
                },
                status_codes=[HTTP_200_OK]
            )
        ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={
            HTTP_200_OK: TagSerializer(many=False)
        } | DEFAULT_SCHEMA_RESPONSES
    ),
    retrieve=extend_schema(
        summary='Получить расшифровку тега',
        examples=[
            OpenApiExample(
                'Пример тега',
                status_codes=[HTTP_200_OK],
                response_only=True,
                value={'id': 1, 'name': 'Новый год'}
            )
        ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_200_OK: TagSerializer} | DEFAULT_SCHEMA_RESPONSES
    ),
    destroy=extend_schema(
        summary='Удалить тэг',
        examples=[
            OpenApiExample(
                'Тэг успешно удален',
                status_codes=[HTTP_204_NO_CONTENT],
                response_only=True
            )
        ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_204_NO_CONTENT: {}} | DEFAULT_SCHEMA_RESPONSES
    ),
    create=extend_schema(
        summary='Создать новый тэг',
        examples=[
            OpenApiExample(
                'Успешно создан',
                value={'name': 'Новый год'},
                request_only=True,
            ),
            OpenApiExample(
                'Успешно создан',
                value={'id': 1, 'name': 'Новый год'},
                response_only=True,
                status_codes=[HTTP_201_CREATED]
            ),
            OpenApiExample(
                'Тэг уже существует',
                value={'detail': 'Tag с таким name уже существует.'},
                status_codes=[HTTP_400_BAD_REQUEST],
                response_only=True
            )
        ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_201_CREATED: TagSerializer} | DEFAULT_SCHEMA_RESPONSES
    )
)
@extend_schema(tags=['Тэги файлов'])
class TagViewSet(NoUpdateViewSet):
    """
    # Теги файлов.

    ## Наименование `name`
    - Строковое поле максимальная допустимая длинна 255 символов
    значение должно быть уникальным

    ---

    Тэги нельзя обновлять, вместо этого следует создать новый.
    Старый, при необходимости, удалить.
    """

    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer
    permission_classes = [StaffCUDAuthRetrieve]

@extend_schema_view(
    list=extend_schema(
        summary='Получить пагинированный список файлов',
        examples=[OpenApiExample(
            'Музыка',
            value={
                'id': 'df1e2629-8180-478a-af93-87c45f547e88 ',
                'length': '00:02:16',
                'type': 'music',
                'size': 2169778,
                'tags': [
                    {
                        "id": 1,
                        "name": "Музыка"
                    },
                    {
                        "id": 65,
                        "name": "Для тестов"
                    }
                ],
                'url': (
                    'http://localhost/local-media/music/Каста-ВоругШум.mp3'
                ),
                'name': '1Kla$ ft Дора - Почему (mashup) [audiovkСom].mp3',
                'hash': (
                    '33ca6a63972a90a799771dff765936f3aeb6b948ee94620b9858'
                    '2f23dd21b174d209eae0d933ee81559d13b1cf382bc3',
                ),
                'owner': {
                    'full_name': 'Фамилия Имя'
                },
                'created': '2025-04-19 19:43:41'
            }
        )],
        responses={
            HTTP_200_OK: FileListSerializer(many=True)
        } | DEFAULT_SCHEMA_RESPONSES
    ),
    retrieve=extend_schema(
        summary='Получить расшифровку файла',
        examples=[
            OpenApiExample(
                'Музыка',
                response_only=True,
                value={
                    'id': 'df1e2629-8180-478a-af93-87c45f547e88 ',
                    'length': '00:02:16',
                    'type': 'music',
                    'size': 2169778,
                    'tags': [
                        {
                            "id": 1,
                            "name": "Музыка"
                        },
                        {
                            "id": 65,
                            "name": "Для тестов"
                        }
                    ],
                    'url': (
                        'http://localhost/local-media/music/Каста-ВоругШум.mp3'
                    ),
                    'name': '1Kla$ ft Дора - Почему (mashup) [audiovkСom].mp3',
                    'hash': (
                        '33ca6a63972a90a799771dff765936f3aeb6b948ee94620b9858'
                        '2f23dd21b174d209eae0d933ee81559d13b1cf382bc3',
                    ),
                    'owner': {
                        'full_name': 'Фамилия Имя'
                    },
                    'created': '2025-04-19 19:43:41'
                },
                status_codes=[HTTP_200_OK]
            )
        ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_200_OK: FileSerializer} | DEFAULT_SCHEMA_RESPONSES
    ),
    create=extend_schema(
        summary='Загрузить файл',
        request=FileSerializer,
        examples=[
            OpenApiExample(
                'Загрузить файл',
                request_only=True,
                value={
                    'type': 2,
                    'source': 'base64:file',
                    'tags': ['Картинка', 'Еда']
                }
            ),
            OpenApiExample(
                'Файл уже существует',
                response_only=True,
                value={'detail': 'Файл с таким hash уже существует'},
                status_codes=[HTTP_400_BAD_REQUEST]
            )
        ],
        responses={HTTP_201_CREATED: FileSerializer} | DEFAULT_SCHEMA_RESPONSES
    ),
    destroy=extend_schema(
        summary='Деактивировать файл (мягкое удаление)',
        responses={HTTP_204_NO_CONTENT: {}} | DEFAULT_SCHEMA_RESPONSES
    )
)
@extend_schema(tags=['Файлы'])
class FileViewSet(NoUpdateViewSet):
    """
    # Файлы.

    ## Ссылка на файл `url`
    - ссылается на локольное облачное хранилище в котором хранятся файлы
    - стандартный период жизни ссылки 2 часа

    ## Хэш файла `hash`
    - Состоит из сопоставления `md5` и `sha256` контрольных сумм файла,
    во избежании коллизий

    ## Хронометраж файла `length`
    - для аудио / видео файлов возвращает его хронометраж

    ## Размер файла `size`
    - Размер файла в байтах

    ## Типы файлов `type`
    - `0` музыка
    - `1` видео
    - `2` изображения
    - `3` файлы бегущей строки
    - `4` рекламные файлы

    ## Тэги файла `tags`
    - Список тэгов присвоенных файлу
    """

    queryset = File.active.all().select_related('owner')
    serializer_class = FileSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = FileFilter
    parser_classes = [JSONParser]
    permission_classes = [OwnerAndStaffCRUD]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = FileListSerializer
        else:
            serializer = FileSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(
            data={'detail': data} if data else None,
            status=400 if data else 204
        )

    def perform_destroy(self, instance) -> str | None:
        """
        Мягкое удаление.

        0. Если файл уже был деактивирован, вызываем ошибку.
        1. Проверяем, находится ли файл в каких-либо плейлистах.
        2. Если такие плейлисты нашлись, вызываем метод, чтобы почистить их
            и обновить активные заказы, в которых данные плейлисты указаны.
        3. Меняем статус актуальности файла.
        """
        # 0
        if instance.is_active is False:
            return (
                'Файл уже был "удалён".'
                'Для окончательного удаления воспользуйтесь админ-панелью.'
            )
        file_id = str(instance.id)
        # 1
        playlists = list(Playlist.objects.filter(files__id=file_id))
        # 2
        if playlists:
            PlaylistViewSet.perform_remove_files(playlists, [file_id])
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return None

    @staticmethod
    def _validate_tag_data(tag_data: list[str]) -> None:
        """
        Проверка валидности полученных данных.

        1. Теги должны приходить списком.
        2. Теги должны быть в строчном формате
        """
        if not isinstance(tag_data, list):
            raise ValidationError('Теги должны приходить списком')
        if not all(isinstance(tag, str) for tag in tag_data):
            raise ValidationError('Теги должны быть в строчном формате')

    @extend_schema(
        summary='Добавить тэги к файлу',
        request=TagsFileSerializer,
        examples=[
            OpenApiExample(
                'Убрать теги',
                value={'tags': ['Мясо', 'Шашлык']},
                request_only=True
            )
        ],
        responses={HTTP_200_OK: DetailSerializer} | DEFAULT_SCHEMA_RESPONSES
    )
    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[StaffCUDAuthRetrieve]
    )
    def add_tags(self, request, pk):
        """
        Присвоить тэги файлу.

        0. Проверяем, что объект запроса существует.
        1. Проверяем валидность полученных даных.
        2. Получаем из базы, либо создаём каждый полученный тэг.
        3. Присваиваем тэги файлу.
        """
        # 0
        file = get_instance_or_404(File, pk)
        new_tags: list[str] = request.data['tags']
        # 1
        self._validate_tag_data(new_tags)
        # 2
        new_tags_ids = [
            Tag.objects.get_or_create(name=tag)[0].id
            for tag
            in new_tags
        ]
        # 3
        file.tags.add(*new_tags_ids)
        return Response(data={'message': 'Тэги успешно присвоены файлу.'})

    @extend_schema(
        summary='Убрать тэги файла',
        request=TagsFileSerializer,
        examples=[
            OpenApiExample(
                'Убрать теги',
                value={'tags': ['Мясо', 'Шашлык']},
                request_only=True
            )
        ],
        responses={HTTP_200_OK: DetailSerializer} | DEFAULT_SCHEMA_RESPONSES
    )
    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[StaffCUDAuthRetrieve]
    )
    def remove_tags(self, request, pk):
        """
        Убрать тэги файла.

        0. Проверяем, что объект запроса существует.
        1. Проверяем валидность полученных даных.
        2. Получаем айди тэгов для отвязки их от файла. Если какой-либо
            из тэгов не будет найден в базе - он будет проигнорирован.
        3. Убираем теги по полученным айдишкам.
        """
        from django.shortcuts import get_list_or_404
        # 0
        file = get_instance_or_404(File, pk)
        remove_tags: list[str] = request.data['tags']
        # 1
        self._validate_tag_data(remove_tags)
        # 2
        remove_tags_ids = [
            tag.id
            for tag
            in get_list_or_404(Tag, name__in=remove_tags)
        ]
        # 3
        file.tags.remove(*remove_tags_ids)
        return Response(data={'message': 'Тэги успешно отвязаны от файла.'})

    @extend_schema(
        summary='Получить список статистики по файлу',
        responses={HTTP_200_OK: BaseFileSerializer}
    )
    @action(detail=True, methods=['GET'], url_path='stat')
    def get_stat(self, request, pk):
        """Отображение статистики файла."""
        file = get_instance_or_404(File, pk)
        match file.type:
            case 0:
                statistics = MusicStat.objects.filter(file=pk)
                data = FileMusicStatSerializer(statistics, many=True).data
            case 1:
                statistics = ImageStat.objects.filter(file=pk)
                data = FileImageStatSerializer(statistics, many=True).data
            case 2:
                statistics_bg = VideoStat.objects.filter(file=pk)
                statistics_ad = ADStat.objects.filter(file=pk)
                data_bg = FileVideoStatSerializer(statistics_bg,
                                                  many=True).data
                data_ad = FileAdStatSerializer(statistics_ad, many=True).data
                data = data_ad + data_bg
            case 3:
                statistics = TickerStat.objects.filter(file=pk)
                data = FileTickerStatSerializer(statistics, many=True).data
            case 4:
                statistics = ADStat.objects.filter(file=pk)
                data = FileAdStatSerializer(statistics, many=True).data
            case _:
                data = []

        return Response(data, status=HTTPStatus.OK)

@extend_schema_view(
    list=extend_schema(
        summary='Получить пагинированный список плейлистов',
        responses={
            HTTP_200_OK: PlaylistListSerializer
        } | DEFAULT_SCHEMA_RESPONSES,
        examples=[
            OpenApiExample(
                'Список плейлистов',
                value={
                    'id': '57c42879-2a80-4304-9551-1c02011f559b',
                    'name': 'Наименование плейлиста',
                    'created': '2025-03-07 15:10:25',
                    'owner': {
                        'full_name':' Фамилия Имя'
                    },
                    'files_count': 2
                },
                status_codes=[HTTP_200_OK]
            )
        ] + DEFAULT_SCHEMA_EXAMPLES
    ),
    retrieve=extend_schema(
        summary='Получить расшифровку плейлиста',
        responses={
            HTTP_200_OK: PlaylistSerializer
        } | DEFAULT_SCHEMA_RESPONSES,
        examples=[
            OpenApiExample(
                'Плейлист',
                value={
                    'id': '57c42879-2a80-4304-9551-1c02011f559b',
                    'name': 'Наименование плейлиста',
                    'description': 'Описание плейлиста',
                    'created': '2025-03-07 15:10:25',
                    'owner': {
                        'full_name':' Фамилия Имя'
                    },
                    'files_count': 2,
                    'files': [
                        {
                            'id': 'be326d46-281f-40fd-b8f4-2534cf4afa25',
                            'name': '9_est_novosti_kadrovi_proekt_306514_1000.mp4',
                            'url': 'ССЫЛКА НА ФАЙЛ'
                        },
                        {
                            'id': '66f77962-5c5e-4d41-b1ec-9579b5715f97',
                            'name': '8_est_novosti_ambassador_306363_1000.mp4',
                            'url': 'ССЫЛКА НА ФАЙЛ'
                        }
                    ]
                },
                status_codes=[HTTP_200_OK]
            )
        ] + DEFAULT_SCHEMA_EXAMPLES
    ),

)
@extend_schema(tags=['Плейлисты'])
class PlaylistViewSet(viewsets.ModelViewSet):
    """
    # Плейлисты.

    ## Описание `description`
    - Текстовое поле, не обязательное к заполнению, не ограниченно длинной

    ## Наименование `name`
    - Текстовое поле максимальной длинны 255 символов

    ## Дата создания `created`
    - Дата и время когда был создан плейлист

    ## Владелец `owner`
    - Пользователь который создал плелист

    ## количество файлов в плейлисте `files_count`
    - Выщитывается при каждом запросе плейлиста

    ## Идентификатор плейлиста `id`
    - Автогенерируемый уникальный идентификатор `uuid`

    ## Файлы плейлиста `files`
    - Список файлов плейлиста с минимальной необходимой информацией о них
        - `id` идентификатор для перехода на страницу файла
        - `name` для отображения наименования фалйа в списке
        - `url` ссылка на файл в локальном облачном хранилище
        для его возможного воспроизведения
    """

    queryset = Playlist.objects.all().select_related(
        'owner'
    ).prefetch_related('files')
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlaylistFilter
    permission_classes = [StaffCUDAuthRetrieve]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = PlaylistListSerializer
        else:
            serializer = PlaylistSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @staticmethod
    def check_for_orders(pls_obj: Playlist | list[Playlist]) -> list | None:
        """
        Проверяем, указан ли плейлист в каком-либо активном заказе.

        1. Фильтруем активные заказы по-указанному плейлисту.
        1.1 Если был получен список плейлистов, то меняем условие фильтрации.
        2. Пробуем пройтись по найденным заказам.
        2.1 Если не удалось, значит ничего не нашлось, возвращаем None.
        2.2 Иначе возвращаем заказы.
        """
        # 1
        try:
            orders = chain(AdOrder.objects.filter(playlist=pls_obj),
                           BgOrder.objects.filter(playlist=pls_obj))
        # 1.1
        except DjangoValidationError:
            orders = chain(AdOrder.objects.filter(playlist__in=pls_obj),
                           BgOrder.objects.filter(playlist__in=pls_obj))
        orders = list(orders)
        # 2
        return orders if orders else None

    @staticmethod
    def perform_remove_files(playlists: Playlist | list[Playlist],
                             files: list[str]) -> None:
        """
        Удаляем файлы из плейлиста или из списка плейлистов и обновляем
        связанные с ним(и) заказы.

        1. Если пришёл один плейлист, убираем файл(ы) из него.
        2. Иначе делаем то же самое с каждым плейлистом из списка.
        """

        def _remove_files_and_update_orders(playlist, file_list) -> None:
            """
            Убираем из плейлиста только те файлы, которые реально в нём есть.

            1. Собираем список айди файлов плейлиста.
            2. Создаём независимую копию списка на удаление, в которой
                останутся только актуальные файлы.
            3.1 Если файл есть в плейлисте, удаляем его.
            3.2 Иначе удаляем его из списка актуальных файлов.
            4. Фильтруем список актуальных заказов с данным плейлистом.
            5. Если заказы нашлись, обновляем их списком актуальных файлов.
            """
            # 1
            playlist_files = list(map(str, [
                file_id
                for file_id
                in playlist.files.values_list('id', flat=True)
            ]))
            # 2
            actual_file_list = copy.deepcopy(file_list)
            for file in file_list:
                # 3.1
                if file in playlist_files:
                    playlist.files.remove(file)
                # 3.2
                else:
                    actual_file_list.remove(file)
            playlist.save()
            # 4
            orders = PlaylistViewSet.check_for_orders(playlists)
            # 5
            if orders:
                PlaylistViewSet.perform_update_orders(
                    orders,
                    actual_file_list,
                    action_type='remove_files'
                )
        # 1
        if isinstance(playlists, Playlist):
            _remove_files_and_update_orders(playlists, files)
        # 2
        else:
            for playlist in playlists:
                _remove_files_and_update_orders(playlist, files)

    @staticmethod
    def perform_update_orders(order_list: list, files: list, action_type: str):
        """
        Обновление актуальных заказов.

        1. Разделяем рекламные и фоновые заказы.
        2. Обновляем каждый тип заказов, в котором есть хотя бы один заказ.
        """
        ad_orders = []
        bg_orders = []
        # 1
        for order in order_list:
            if isinstance(order, AdOrder):
                ad_orders.append(str(order.id))
            else:
                bg_orders.append(str(order.id))
        # 2
        if ad_orders:
            add_or_remove_files_ad_order_task.delay(ad_orders, files, action_type)
        if bg_orders:
            add_or_remove_files_bg_order_task.delay(bg_orders, files, action_type)

    @staticmethod
    def _validate_request_data_format(files: list[str]) -> None:
        """
        Проверка формата полученных данных.

        1. Файлы должны быть переданы списком айди.
        2. Каждый айди должен быть строкой.
        3. Каждый айди должен быть валидным UUID.
        """
        # 1
        if not isinstance(files, list):
            raise ValidationError('Файлы должны приходить списком')
        # 2
        if not all(isinstance(file, str) for file in files):
            raise ValidationError('Айди файла должен быть в формате строки')
        # 3
        try:
            all([UUID(file) for file in files])
        except ValueError as e:
            raise ValidationError(
                f'Значение {e} не является верным UUID-ом.'
            )

    def update(self, request, *args, **kwargs):
        error_message = (
            'Изменить методом "PATCH" можно только название и описание. '
            'Лишние ключи: {keys}.\n'
            'Для добавления файлов в плейлист используйте '
            'эндпоинт /add_files, а для удаления /remove_files.'
        )
        updatable_fields = (
            'name',
            'description'
        )
        kwargs.update(updatable_fields=updatable_fields,
                      error_message=error_message)
        response = restricted_update(self, request, *args, **kwargs)
        return response

    def perform_destroy(self, instance):
        """Запрет на удаление плейлиста, если он сейчас где-то играет."""
        orders = self.check_for_orders(instance)
        if orders:
            orders_names = [order.name for order in orders]
            raise ValidationError(
                'Нельзя удалить плейлист, т.к. он указан в активных заказах: '
                f'{orders_names}'
            )

    @action(detail=True, methods=['POST'])
    def add_files(self, request, pk):
        """
        Добавить файлы в плейлист.

        0. Проверяем формат полученных данных.
        1. Проверяем, что объект запроса существует.
        2. Проверяем, что в запросе нет ранее добавленных в плейлист файлов.
        3. Проверяем, что тип файлов в запросе соответствует типу файлов
            в плейлисте.
        4. Если всё ок - добавляем файлы в плейлист, иначе
            выбрасываем исключение.
        5. Проверяем наличие активных заказов с данным плейлистом.
        6. Если заказы нашлись, создаём репликации на обновление
            соответствущего типа.
        """

        def _validate_no_duplicates(files: set, pls_files: set) -> None:
            """Проверяем, что файлы не будут дублироваться."""
            duplicates = pls_files & files
            if duplicates:
                raise ValidationError(
                    'Плейлист уже содержит данные файлы: '
                    f'{duplicates}'
                )

        # TODO: оптимизировать с использованием множеств
        # files_types = {TYPES[file.type] for file in files}
        #    if files_types.difference_update(
        #            {file_type
        #             for file_type
        #             in files_types
        #             if file_type != pls_type}
        #    ):
        def _validate_file_types(files: QuerySet, pls_type: str) -> None:
            """Проверяем, что тип файлов соответствует плейлисту."""
            bad_types = set()
            file_objs = File.objects.filter(id__in=files)
            for file in file_objs:
                file_type = TYPES[file.type]
                if file_type != pls_type:
                    bad_types.add(file_type)
            if bad_types:
                raise ValidationError(
                    'Вы пытаетесь добавить в плейлист файлы '
                    'не соответствующего типа.\n'
                    f'Тип файлов в плейлисте: {pls_type}.\n'
                    f'Среди ваших файлов есть: {bad_types}'
                )
        # 0
        new_files = request.data.get('files')
        self._validate_request_data_format(new_files)
        # 1
        playlist = get_instance_or_404(Playlist, pk)
        playlist_files = set(map(str, [
            file_id
            for file_id
            in playlist.files.values_list('id', flat=True)
        ]))
        # 2
        _validate_no_duplicates(set(new_files), playlist_files)
        # 3
        file_objs = File.objects.filter(id__in=new_files)
        playlist_type = TYPES[playlist.files.first().type]
        _validate_file_types(file_objs, playlist_type)
        # 4
        playlist.files.add(*new_files)
        # 5
        orders = PlaylistViewSet.check_for_orders(playlist)
        # 6
        if orders:
            files_list = [
                {'id': str(file.id), 'hash': file.hash}
                for file
                in file_objs
            ]
            self.perform_update_orders(
                orders,
                files_list,
                action_type='add_files'
            )

        return Response(data={'message': 'Файлы успешно добавлены в плейлист.'})

    @action(detail=True, methods=['POST'])
    def remove_files(self, request, pk):
        """
        Убрать файлы из плейлиста.

        0. Проверяем формат полученных данных.
        1. Проверяем, что объект запроса существует.
        2. Убираем из плейлиста указанные в запросе файлы, если они были
            в плейлисте. При наличии лишних - записываем их в отдельный список
            для оповещения пользователя.
        3. Получаем список активных заказов с данным плейлистом для обновления.
        4. Если заказы нашлись, создаём репликации на обновление
            соответствущего типа.
        5. Оповещаем пользователя, если выполнился пункт 2.1.
        """
        # 0
        remove_files: list[str] = request.data.get('files')
        self._validate_request_data_format(remove_files)
        # 1
        playlist = get_instance_or_404(Playlist, pk)
        # 2
        self.perform_remove_files(playlist, remove_files)
        return Response(data={'message': 'Файлы успешно убраны из плейлиста.'})


@extend_schema(tags=['Файлы'], deprecated=True)
class UploadFilesViewSet(viewsets.ModelViewSet):
    """Для загрузки файлов из старой админки."""

    queryset = File.objects.all().select_related('owner')
    serializer_class = FileSourceSerializer()

    def get_serializer(self, *args, **kwargs):
        serializer = FileSourceSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
