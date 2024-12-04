import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from http import HTTPStatus
from itertools import chain
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from uuid import UUID

from api.constants import get_instance_or_404, restricted_update
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
    FileTickerStatSerializer
)

from files.filters import FileFilter, PlaylistFilter
from files.serializers import (
    PlaylistSerializer,
    PlaylistListSerializer,
    FileSerializer,
    FileListSerializer,
    TagSerializer, FileSourceSerializer
)
from files.models import Playlist, File, Tag, TYPES
from orders.models import AdOrder, BgOrder
from orders.tasks import update_ad_order_task, update_bg_order_task
from users.permissions import StaffCUDAuthRetrieve, OwnerAndStaffCRUD


class NoUpdateViewSet(
    viewsets.GenericViewSet,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin
):
    """Вьюсет без поддержки методов PUT и PATCH."""
    pass


class TagViewSet(NoUpdateViewSet):
    """
    Работа с тегами файлов.

    Тэги нельзя обновлять, вместо этого следует создать новый.
    Старый, при необходимости, удалить.
    """

    queryset = Tag.objects.all().order_by('id')
    serializer_class = TagSerializer
    permission_classes = [StaffCUDAuthRetrieve]


class FileViewSet(NoUpdateViewSet):
    """Работа с файлами."""

    queryset = File.objects.all().select_related('owner')
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

    @staticmethod
    def check_for_active_playlists(file: File) -> bool:
        """
        Проверяем указан ли удаляемый файл в каком-либо активном плейлисте.

        1. Фильтруем плейлисты на наличие файла.
        2. Если есть плейлист(ы) с данным файлом:
        2.1 Проверяем, есть ли активные заказы с данным(и) плейлистом(ами).
        2.2 Если есть такие заказы, удаляем файл и обновляем заказы, возвращаем
            True, для оповещения.
        2.3 Иначе просто удаляем файл из всех плейлистов, возвращаем False.
        3. Если плейлистов с данным файлом не нашлось, просто возвращаем False.
        """
        file_id = str(file.id)
        # 1
        playlists = list(Playlist.files.filter(file_id=file_id))
        # 2
        if playlists:
            # 2.1
            active_orders = PlaylistViewSet.check_for_orders(playlists)
            # 2.2
            if active_orders:
                PlaylistViewSet.perform_remove_files(playlists, [file])
                return True
            # 2.3
            else:
                for playlist in playlists:
                    playlist.files.remove(file)
                    playlist.save()
                return False
        # 3
        else:
            return False

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Добавлено сообщение об обновлении заказов, если оно произошло."""
        instance = self.get_object()
        data = self.perform_destroy(instance)
        return Response(
            data=data if data else None,
            status=HTTPStatus.NO_CONTENT
        )

    def perform_destroy(self, instance):
        """Возвращаем сообщение, если были обновлены заказы."""
        in_active_playlists = self.check_for_active_playlists(instance)
        instance.is_active = False
        instance.save()
        return (
            'Файл был удалён, а также обновлены заказы, в которых он играл.'
        ) if in_active_playlists else None

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[StaffCUDAuthRetrieve]
    )
    def add_tags(self, request, pk):
        """Присвоить тэги файлу."""
        file = get_instance_or_404(File, pk)
        new_tags = request.data['tags']
        if not isinstance(new_tags[0], str):
            raise ValidationError(
                'Теги файла должны приходить списком, а получено: '
                f'{type(new_tags)}'
            )
        new_tags = set(new_tags)
        file_tags = file.tags.all()
        file_tags_names = set(tag.name for tag in file_tags)

        good_tags = new_tags | file_tags_names
        tag_ids = [Tag.objects.get_or_create(name=tag)[0] for tag in good_tags]
        file.tags.set(tag_ids)
        file.save()
        return Response(data='Тэги успешно присвоены файлу.')

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[StaffCUDAuthRetrieve]
    )
    def remove_tags(self, request, pk):
        """Убрать тэги файла."""
        file = get_instance_or_404(File, pk)
        remove_tags = request.data['tags']
        if not isinstance(remove_tags, list):
            raise ValidationError(
                'Теги файла должны приходить списком, а получено: '
                f'{type(remove_tags)}'
            )
        remove_tags = set(remove_tags)
        file_tags = file.tags.all()
        file_tags_names = set(tag.name for tag in file_tags)

        good_tags = file_tags_names - remove_tags
        if good_tags:
            tag_ids = [Tag.objects.get(name=tag) for tag in good_tags]
            file.tags.set(tag_ids)
        else:
            file.tags.clear()
        file.save()
        return Response(data='Тэги успешно присвоены файлу.')

    @action(detail=True, methods=['GET'], url_path='stat')
    def get_stat(self, request, pk):
        """Отображение статистики файла."""
        file = get_instance_or_404(File, pk)
        match file.file_type:
            case 0:
                statistics = ADStat.objects.filter(file=pk)
                data = FileAdStatSerializer(statistics, many=True).data
            case 1:
                statistics = MusicStat.objects.filter(file=pk)
                data = FileMusicStatSerializer(statistics, many=True).data
            case 2:
                statistics = ImageStat.objects.filter(file=pk)
                data = FileImageStatSerializer(statistics, many=True).data
            case 3:
                statistics_bg = VideoStat.objects.filter(file=pk)
                statistics_ad = ADStat.objects.filter(file=pk)
                data_bg = FileVideoStatSerializer(statistics_bg,
                                                  many=True).data
                data_ad = FileAdStatSerializer(statistics_ad, many=True).data
                data = data_ad + data_bg
            case 4:
                statistics = TickerStat.objects.filter(file=pk)
                data = FileTickerStatSerializer(statistics, file=True).data
            case _:
                data = []

        return Response(data, status=HTTPStatus.OK)


class PlaylistViewSet(viewsets.ModelViewSet):
    """Работа с плейлистами."""

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
    def check_for_orders(pls_obj: Playlist | list[Playlist]) -> chain | None:
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
        # 2
        try:
            next(orders)
        # 2.1
        except StopIteration:
            return None
        # 2.2
        else:
            return orders

    @staticmethod
    def perform_remove_files(
        playlists: Playlist | list[Playlist],
        files: list[File]
    ) -> None:
        """
        Удаляем файлы из одного или из списка плейлистов и обновляем
        связанные заказы.

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
            playlist_files = [
                str(file_id)
                for file_id
                in playlist.files.values_list('id', flat=True)
            ]
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
                file_id_list = [str(file.id) for file in actual_file_list]
                PlaylistViewSet.perform_update_orders(
                    orders,
                    file_id_list,
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
    def perform_update_orders(order_list, files, action_type):
        """
        Обновление актуальных заказов.

        1. Разделяем рекламные и фоновые заказы.
        2. Обновляем каждый тип заказов, в котором есть хотя бы один заказ.
        """
        ad_orders = []
        bg_orders = []
        # 1
        for order in order_list:
            if isinstance(order.model, AdOrder):
                ad_orders.append(str(order.id))
            else:
                bg_orders.append(str(order.id))
        # 2
        if ad_orders:
            update_ad_order_task(ad_orders, files, action_type)
        if bg_orders:
            update_bg_order_task(bg_orders, files, action_type)

    @staticmethod
    def _validate_request_data_format(files: list) -> None:
        """
        Проверка формата полученных данных.

        1. Файлы должны быть переданы списком.
        2. Каждый файл должен быть валидным UUID.
        """
        # 1
        if not isinstance(files, list):
            raise ValidationError(
                'Файлы должны приходить списком, было получено: '
                f'{type(files)}'
            )
        # 2
        for file in files:
            if not isinstance(file, str):
                raise ValidationError(
                    'Айди фалов должен быть в формате строки, было получено: '
                    f'{type(files)}'
                )
            try:
                UUID(file)
            except ValueError:
                raise ValidationError(
                    f'Значение {file} не является верным UUID-ом.'
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

        def _validate_no_duplicates(files, pls_files) -> None:
            """Проверяем, что файлы не будут дублироваться."""
            already_in_playlist = []
            for file in files:
                if file in pls_files:
                    already_in_playlist.append(file)
            if already_in_playlist:
                raise ValidationError(
                    'Плейлист уже содержит данные файлы: '
                    f'{already_in_playlist}'
                )

        def _validate_file_types(files, pls_type) -> list[dict[str, str]]:
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
                    f'Тип файлов в плейлисте: {playlist_type}.\n'
                    f'Среди ваших файлов есть: {bad_types}'
                )
            files_list = [
                {
                    'id': str(file.id),
                    'hash': file.hash
                } for file in file_objs
            ]
            return files_list
        # 0
        new_files: list = request.data.get('files')
        self._validate_request_data_format(new_files)
        # 1
        playlist = get_instance_or_404(Playlist, pk)
        playlist_files = [
            str(file_id)
            for file_id
            in playlist.files.values_list('id', flat=True)
        ]
        playlist_type = TYPES[playlist.files.first().type]
        # 2
        _validate_no_duplicates(new_files, playlist_files)
        # 3
        files_list = _validate_file_types(new_files, playlist_type)
        # 4
        playlist.files.add(*new_files)
        playlist.save()
        # 5
        orders = PlaylistViewSet.check_for_orders(playlist)
        # 6
        if orders:
            self.perform_update_orders(
                orders,
                files_list,
                action_type='add_files'
            )

        return Response(data='Файлы успешно добавлены в плейлист.')

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
        remove_files: list = request.data.get('files')
        self._validate_request_data_format(remove_files)
        # 1
        playlist = get_instance_or_404(Playlist, pk)
        # 2
        self.perform_remove_files(playlist, remove_files)
        return Response(data='Файлы успешно убраны из плейлиста.')


class UploadFilesViewSet(viewsets.ModelViewSet):
    """Для загрузки файлов из старой админки."""

    queryset = File.objects.all().select_related(
        'owner'
    )
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
