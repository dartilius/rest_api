"""
Модуль представлений (views) для статистики номенклатур.

Этот модуль предоставляет API эндпоинты для получения статистики
различных типов контента (реклама, музыка, видео, изображения, бегущие строки)
а также истории статусов номенклатур.

Все эндпоинты используют единую логику:
- Проверка существования номенклатуры (404 если не найдена)
- Фильтрация по дате через параметр 'date'
- Сортировка от старых к новым
- Отсутствие пагинации (возвращаются все записи)

Author: Development Team
Date: 2026-05-20
"""

from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from api.constants import get_instance_or_404
from ch_statistic.models import (
    ADStat,
    MusicStat,
    VideoStat,
    ImageStat,
    TickerStat,
)
from ch_statistic.serializers import (
    NomenclatureAdStatSerializer,
    NomenclatureMusicStatSerializer,
    NomenclatureVideoStatSerializer,
    NomenclatureImageStatSerializer,
    NomenclatureTickerStatSerializer,
)
from nomenclatures.models import Nomenclature
from nomenclatures.serializers import StatusHistorySerializer
from users.permissions import StaffCUDallRead


# ============================================================================
# ЕДИНЫЙ VIEWSET ДЛЯ ВСЕЙ СТАТИСТИКИ
# ============================================================================

class NomenclatureStatisticViewSet(viewsets.GenericViewSet):
    """
    ViewSet для получения статистики по номенклатуре.

    Этот ViewSet объединяет все методы статистики в одном классе.
    Такой подход выбран для сохранения обратной совместимости с API:
    - /api/statistics/{uuid}/ad_stat/         - статистика рекламы
    - /api/statistics/{uuid}/music_stat/      - статистика музыки
    - /api/statistics/{uuid}/video_stat/      - статистика видео
    - /api/statistics/{uuid}/image_stat/      - статистика изображений
    - /api/statistics/{uuid}/ticker_stat/     - статистика бегущих строк
    - /api/statistics/{uuid}/status_history/  - история статусов

    Особенности:
        - Все методы используют GET запросы
        - Поддерживается фильтрация по дате через параметр 'date'
        - Нет пагинации (возвращаются ВСЕ записи)
        - Сортировка по полю 'played' (от старых к новым)
        - Требуется авторизация (StaffCUDallRead)

    Параметры фильтрации по дате (для всех методов статистики):
        date (str, optional) - фильтр по дате в формате:
            - YYYY-MM-DD (конкретный день)
            - YYYY-MM (весь месяц)
            - YYYY (весь год)
            - Пример: ?date=2026-05-20
    """

    # Права доступа: персонал может читать, создавать, обновлять, удалять
    # Обычные пользователи - только чтение
    permission_classes = [StaffCUDallRead]

    # =========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # =========================================================================

    def _get_filtered_stats(self, model, request, pk):
        """
        Универсальный метод для получения отфильтрованной статистики.

        Этот метод инкапсулирует общую логику для всех типов статистики:
        1. Проверка существования номенклатуры (иначе 404)
        2. Фильтрация по client = pk
        3. Фильтрация по дате (если передан параметр 'date')
        4. Сортировка от старых к новым

        Args:
            model (class): Модель статистики (ADStat, MusicStat, VideoStat и т.д.)
            request (Request): HTTP запрос для получения параметра 'date'
            pk (str): UUID номенклатуры (client)

        Returns:
            QuerySet: Отфильтрованный и отсортированный QuerySet

        Example:
            stats = self._get_filtered_stats(MusicStat, request, '123e4567...')
        """
        # Шаг 1: Проверяем существование номенклатуры
        # Если номенклатура не найдена, функция выбрасывает HTTP 404
        get_instance_or_404(Nomenclature, pk)

        # Шаг 2: Получаем параметр 'date' из query string
        # request.query_params - это аналог request.GET в DRF
        date = request.query_params.get("date")

        # Шаг 3: Базовый запрос - все записи для данного клиента
        statistics = model.objects.filter(client=pk)

        # Шаг 4: Фильтрация по дате (если указана)
        # Используем __contains (LIKE) для поиска подстроки
        # Это позволяет фильтровать по:
        # - YYYY-MM-DD (конкретный день)
        # - YYYY-MM (весь месяц)
        # - YYYY (весь год)
        if date:
            statistics = statistics.filter(played__contains=date)

        # Шаг 5: Сортировка от старых к новым по времени проигрывания
        statistics = statistics.order_by("played")

        return statistics

    # =========================================================================
    # СТАТИСТИКА РЕКЛАМЫ
    # =========================================================================

    @extend_schema(
        summary="Получить статистику рекламы по номенклатуре",
        description="""
        Возвращает полный список показов рекламных роликов на указанной номенклатуре.

        Особенности:
            - БЕЗ пагинации (возвращаются все записи)
            - Поддерживается фильтрация по дате через параметр 'date'
            - Сортировка по времени проигрывания (от старых к новым)

        Параметры запроса:
            date (str, optional) - фильтр по дате в формате:
                - YYYY-MM-DD (конкретный день)
                - YYYY-MM (весь месяц)
                - YYYY (весь год)

        Примеры:
            GET /api/statistics/123e4567/ad_stat/
            GET /api/statistics/123e4567/ad_stat/?date=2026-05-20
            GET /api/statistics/123e4567/ad_stat/?date=2026-05

        Ответ:
            Массив объектов с полями:
            - client: UUID номенклатуры
            - file: идентификатор файла
            - played: дата/время проигрывания (формат: YYYY-MM-DD HH:MM:SS)
            - length: хронометраж (секунды)
            - ad_block: время начала рекламного блока (HH:MM:SS)
        """,
        responses={
            HTTP_200_OK: NomenclatureAdStatSerializer(many=True),
        },
        tags=["Номенклатуры - Статистика"]
    )
    @action(detail=True, methods=["GET"], url_path="ad_stat")
    def get_ad_stat(self, request, pk=None):
        """
        Получение статистики рекламы.

        Args:
            request (Request): HTTP GET запрос
            pk (str): UUID номенклатуры

        Returns:
            Response: JSON со списком записей статистики рекламы
        """
        statistics = self._get_filtered_stats(ADStat, request, pk)
        serializer = NomenclatureAdStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    # =========================================================================
    # СТАТИСТИКА МУЗЫКИ
    # =========================================================================

    @extend_schema(
        summary="Получить статистику музыки по номенклатуре",
        description="""
        Возвращает полный список проигрываний музыки на указанной номенклатуре.

        Особенности:
            - БЕЗ пагинации (возвращаются все записи)
            - Поддерживается фильтрация по дате через параметр 'date'
            - Сортировка по времени проигрывания (от старых к новым)

        Параметры запроса:
            date (str, optional) - фильтр по дате в формате:
                - YYYY-MM-DD (конкретный день)
                - YYYY-MM (весь месяц)
                - YYYY (весь год)

        Примеры:
            GET /api/statistics/123e4567/music_stat/
            GET /api/statistics/123e4567/music_stat/?date=2026-05-20
            GET /api/statistics/123e4567/music_stat/?date=2026-05

        Ответ:
            Массив объектов с полями:
            - client: UUID номенклатуры
            - file: идентификатор файла
            - played: дата/время проигрывания (формат: YYYY-MM-DD HH:MM:SS)
            - length: хронометраж (секунды)

        Примечание:
            В отличие от рекламы, у музыки НЕТ поля ad_block.
        """,
        responses={
            HTTP_200_OK: NomenclatureMusicStatSerializer(many=True),
        },
        tags=["Номенклатуры - Статистика"]
    )
    @action(detail=True, methods=["GET"], url_path="music_stat")
    def get_music_stat(self, request, pk=None):
        """
        Получение статистики музыки.

        Args:
            request (Request): HTTP GET запрос
            pk (str): UUID номенклатуры

        Returns:
            Response: JSON со списком записей статистики музыки
        """
        statistics = self._get_filtered_stats(MusicStat, request, pk)
        serializer = NomenclatureMusicStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    # =========================================================================
    # СТАТИСТИКА ВИДЕО
    # =========================================================================

    @extend_schema(
        summary="Получить статистику фоновых видео по номенклатуре",
        description="""
        Возвращает полный список воспроизведений видео на указанной номенклатуре.

        Особенности:
            - БЕЗ пагинации (возвращаются все записи)
            - Поддерживается фильтрация по дате через параметр 'date'
            - Сортировка по времени проигрывания (от старых к новым)

        Параметры запроса:
            date (str, optional) - фильтр по дате в формате:
                - YYYY-MM-DD (конкретный день)
                - YYYY-MM (весь месяц)
                - YYYY (весь год)

        Примеры:
            GET /api/statistics/123e4567/video_stat/
            GET /api/statistics/123e4567/video_stat/?date=2026-05-20
            GET /api/statistics/123e4567/video_stat/?date=2026-05

        Ответ:
            Массив объектов с полями:
            - client: UUID номенклатуры
            - file: идентификатор файла
            - played: дата/время проигрывания (формат: YYYY-MM-DD HH:MM:SS)
            - length: хронометраж (секунды)
        """,
        responses={
            HTTP_200_OK: NomenclatureVideoStatSerializer(many=True),
        },
        tags=["Номенклатуры - Статистика"]
    )
    @action(detail=True, methods=["GET"], url_path="video_stat")
    def get_video_stat(self, request, pk=None):
        """
        Получение статистики видео.

        Args:
            request (Request): HTTP GET запрос
            pk (str): UUID номенклатуры

        Returns:
            Response: JSON со списком записей статистики видео
        """
        statistics = self._get_filtered_stats(VideoStat, request, pk)
        serializer = NomenclatureVideoStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    # =========================================================================
    # СТАТИСТИКА ИЗОБРАЖЕНИЙ
    # =========================================================================

    @extend_schema(
        summary="Получить статистику фоновых изображений по номенклатуре",
        description="""
        Возвращает полный список отображений изображений на указанной номенклатуре.

        Особенности:
            - БЕЗ пагинации (возвращаются все записи)
            - Поддерживается фильтрация по дате через параметр 'date'
            - Сортировка по времени отображения (от старых к новым)

        Параметры запроса:
            date (str, optional) - фильтр по дате в формате:
                - YYYY-MM-DD (конкретный день)
                - YYYY-MM (весь месяц)
                - YYYY (весь год)

        Примеры:
            GET /api/statistics/123e4567/image_stat/
            GET /api/statistics/123e4567/image_stat/?date=2026-05-20
            GET /api/statistics/123e4567/image_stat/?date=2026-05

        Ответ:
            Массив объектов с полями:
            - client: UUID номенклатуры
            - file: идентификатор файла
            - played: дата/время отображения (формат: YYYY-MM-DD HH:MM:SS)
            - length: длительность показа (секунды)
        """,
        responses={
            HTTP_200_OK: NomenclatureImageStatSerializer(many=True),
        },
        tags=["Номенклатуры - Статистика"]
    )
    @action(detail=True, methods=["GET"], url_path="image_stat")
    def get_image_stat(self, request, pk=None):
        """
        Получение статистики изображений.

        Args:
            request (Request): HTTP GET запрос
            pk (str): UUID номенклатуры

        Returns:
            Response: JSON со списком записей статистики изображений
        """
        statistics = self._get_filtered_stats(ImageStat, request, pk)
        serializer = NomenclatureImageStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    # =========================================================================
    # СТАТИСТИКА БЕГУЩИХ СТРОК
    # =========================================================================

    @extend_schema(
        summary="Получить статистику бегущих строк по номенклатуре",
        description="""
        Возвращает полный список отображений бегущих строк на указанной номенклатуре.

        Бегущие строки - это динамический текстовый контент, который 
        прокручивается по экрану (новости, объявления, акции).

        Особенности:
            - БЕЗ пагинации (возвращаются все записи)
            - Поддерживается фильтрация по дате через параметр 'date'
            - Сортировка по времени отображения (от старых к новым)

        Параметры запроса:
            date (str, optional) - фильтр по дате в формате:
                - YYYY-MM-DD (конкретный день)
                - YYYY-MM (весь месяц)
                - YYYY (весь год)

        Примеры:
            GET /api/statistics/123e4567/ticker_stat/
            GET /api/statistics/123e4567/ticker_stat/?date=2026-05-20
            GET /api/statistics/123e4567/ticker_stat/?date=2026-05

        Ответ:
            Массив объектов с полями:
            - client: UUID номенклатуры
            - file: идентификатор файла
            - played: дата/время отображения (формат: YYYY-MM-DD HH:MM:SS)
            - length: длительность показа (секунды)
        """,
        responses={
            HTTP_200_OK: NomenclatureTickerStatSerializer(many=True),
        },
        tags=["Номенклатуры - Статистика"]
    )
    @action(detail=True, methods=["GET"], url_path="ticker_stat")
    def get_ticker_stat(self, request, pk=None):
        """
        Получение статистики бегущих строк.

        Args:
            request (Request): HTTP GET запрос
            pk (str): UUID номенклатуры

        Returns:
            Response: JSON со списком записей статистики бегущих строк
        """
        statistics = self._get_filtered_stats(TickerStat, request, pk)
        serializer = NomenclatureTickerStatSerializer(statistics, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    # =========================================================================
    # ИСТОРИЯ СТАТУСОВ
    # =========================================================================

    @extend_schema(
        summary="Получить историю доступности номенклатуры",
        description="""
        Возвращает полный журнал всех изменений статуса номенклатуры:
        - Подключение и отключение устройства
        - Переходы онлайн/офлайн
        - Ошибки и восстановление работы
        - Обновления версий программного обеспечения
        - Изменения конфигурации
        - События синхронизации

        История используется для:
        - Анализа надежности оборудования
        - Выявления проблем с сетевыми соединениями
        - Проверки графика обслуживания
        - Диагностики проблем с доставкой контента
        - Составления отчетов об uptime/downtime
        - SLA мониторинга

        Возвращает все события в обратном хронологическом порядке
        (новые события первыми).

        Обратите внимание:
        - Фильтрация по дате НЕ поддерживается (возвращается вся история)
        - Для долгоживущих систем история может быть очень большой
        - Рекомендуется добавить пагинацию или фильтрацию при необходимости

        Пример:
            GET /api/statistics/123e4567/status_history/

        Ответ:
            Массив объектов с полями:
            - change_time: дата и время изменения статуса
            - status: новый статус (online, offline, error, updating)
        """,
        responses={
            HTTP_200_OK: StatusHistorySerializer(many=True),
        },
        tags=["Номенклатуры - Статистика"]
    )
    @action(detail=True, methods=["GET"], url_path="status_history")
    def status_history(self, request, pk=None):
        """
        Получение истории статусов номенклатуры.

        Этот метод отличается от других, так как:
        1. Работает с моделью StatusHistory, а не со статистикой контента
        2. Данные получаются через связанное поле .history
        3. Не поддерживает фильтрацию по дате

        Args:
            request (Request): HTTP GET запрос
            pk (str): UUID номенклатуры

        Returns:
            Response: JSON со списком исторических событий
        """
        # Получаем объект номенклатуры (404 если не найдена)
        nomenclature = get_instance_or_404(Nomenclature, pk)

        # Получаем всю историю изменений (обратная связь OneToMany)
        # django-simple-history автоматически создает поле .history
        history = nomenclature.history.all()

        # Сериализуем историю в JSON
        # many=True - т.к. это список объектов
        serializer = StatusHistorySerializer(history, many=True)

        # Возвращаем ответ с кодом 200 OK
        return Response(serializer.data, status=HTTP_200_OK)


# from rest_framework import viewsets
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from drf_spectacular.utils import extend_schema

# from rest_framework.status import HTTP_200_OK

# from api.constants import get_instance_or_404
# from ch_statistic.models import ADStat, MusicStat, VideoStat, ImageStat, TickerStat
# from ch_statistic.serializers import NomenclatureAdStatSerializer, NomenclatureMusicStatSerializer, \
#     NomenclatureVideoStatSerializer, NomenclatureImageStatSerializer, NomenclatureTickerStatSerializer
# from nomenclatures.models import Nomenclature
# from nomenclatures.serializers import StatusHistorySerializer, NomenclatureSerializer
# from users.permissions import StaffCUDallRead


# @extend_schema(tags=["Номенклатуры - Статистика"])
# class NomenclatureStatisticViewSet(viewsets.ModelViewSet):
#     """
#     ViewSet для получения аналитической статистики по номенклатурам.

#     Предоставляет методы для получения подробной статистики использования
#     различных типов контента (реклама, музыка, видео, изображения, бегущие строки)
#     на конкретных номенклатурах. Также включает методы для просмотра истории
#     изменения статуса доступности.

#     Endpoints:
#         GET /api/statistics/{nomenclature_id}/ad_stat/ - Статистика рекламы
#         GET /api/statistics/{nomenclature_id}/music_stat/ - Статистика музыки
#         GET /api/statistics/{nomenclature_id}/video_stat/ - Статистика видео
#         GET /api/statistics/{nomenclature_id}/image_stat/ - Статистика изображений
#         GET /api/statistics/{nomenclature_id}/ticker_stat/ - Статистика бегущих строк
#         GET /api/statistics/{nomenclature_id}/status_history/ - История доступности

#     Permissions:
#         - Все методы: StaffCUDallRead (чтение для всех, изменение для staff)

#     Features:
#         - Пагинация для больших выборок (кроме ad_stat)
#         - Фильтрация по датам (для ad_stat)
#         - Оптимизированные SQL запросы
#     """
#     queryset = Nomenclature.objects.all()
#     serializer_class = NomenclatureSerializer
#     permission_classes = [StaffCUDallRead]

#     @extend_schema(summary="Получить статистику рекламы по номенклатуре")
#     @action(detail=True, methods=["GET"], url_path="ad_stat")
#     def get_ad_stat(self, request, pk):
#         """
#         Получить статистику показов рекламных роликов на номенклатуре.

#         Метод возвращает полный список событий воспроизведения рекламного контента,
#         включая информацию о времени показа, продолжительности, составе аудитории
#         и других метриках. Может быть отфильтрована по дате для получения данных
#         за конкретный день.

#         Данные используются для:
#         - Анализа эффективности рекламных кампаний
#         - Проверки соответствия графику вещания
#         - Выставления счетов клиентам
#         - Аудита показов

#         Args:
#             request: HTTP GET запрос с опциональным параметром фильтрации.
#             pk: UUID номенклатуры.

#         Query Parameters:
#             date (str, optional): Фильтр по дате воспроизведения.
#                                  Формат: YYYY-MM-DD или YYYY-MM для диапазона
#                                  Пример: ?date=2026-02-09

#         Returns:
#             Response: Список объектов статистики рекламы.
#                      Структура каждого элемента:
#                      {
#                          'id': 'uuid',
#                          'client': 'uuid',
#                          'ad_id': 'uuid',
#                          'ad_name': 'Реклама Coca-Cola',
#                          'played': '2026-02-09T14:30:00Z',
#                          'duration': 30,  # секунды
#                          'viewers_count': 150,
#                          ...
#                      }

#         Status Codes:
#             200 OK: Статистика успешно получена
#             404 NOT FOUND: Номенклатура не найдена
#             403 FORBIDDEN: Пользователь не имеет прав доступа

#         Data Structure (Array of ADStat):
#             [
#                 {
#                     'id': '123e4567-e89b-12d3-a456-426614174000',
#                     'client': '456f7890-a1b2-34cd-ef01-234567890abc',
#                     'spot_id': '789f0123-b4c5-67de-f012-345678901234',
#                     'played': '2026-02-09T14:30:00Z',
#                     'duration': 30,
#                     'viewers': 150
#                 },
#                 ...
#             ]

#         Examples:
#             >>> # Получить все статистику рекламы за день
#             >>> response = client.get(
#             ...     '/api/statistics/123e4567/ad_stat/?date=2026-02-09'
#             ... )
#             >>> response.status_code
#             200
#             >>> len(response.data)
#             45  # 45 записей о показах рекламы

#             >>> # Получить всю статистику за месяц
#             >>> response = client.get(
#             ...     '/api/statistics/123e4567/ad_stat/?date=2026-02'
#             ... )
#             >>> response.status_code
#             200

#             >>> # Получить всю статистику без фильтра
#             >>> response = client.get('/api/statistics/123e4567/ad_stat/')
#             >>> response.status_code
#             200

#         Performance Notes:
#             - Не пагинирована, нужно учитывать при большом объеме данных
#             - Фильтрация выполняется на уровне БД
#             - Результаты сортируются по времени показа (возрастание)
#             - При запросе большого диапазона дат, может быть медленным

#         Use Cases:
#             - Детальный анализ рекламных кампаний
#             - Верификация исполнения договоров
#             - Финансовая отчетность
#             - Выявление проблем с трансляцией

#         Warning:
#             Фильтр date использует LIKE оператор, обеспечивая префиксный поиск.
#             Например, ?date=2026 вернет все записи за 2026 год.
#         """
#         get_instance_or_404(Nomenclature, pk)
#         date = request.query_params.get("date")

#         statistics = ADStat.objects.filter(client=pk)
#         if date:
#             statistics = statistics.filter(played__contains=date)

#         statistics = statistics.order_by("played")
#         serializer = NomenclatureAdStatSerializer(statistics, many=True)
#         return Response(serializer.data, status=HTTP_200_OK)

#     @extend_schema(summary="Получить статистику музыки по номенклатуре")
#     @action(detail=True, methods=["GET"], url_path="music_stat")
#     def get_music_stat(self, request, pk):
#         """
#         Получить пагинированную статистику воспроизведения музыки.

#         Метод возвращает данные о всех музыкальных композициях, которые
#         были воспроизведены на номенклатуре. Включает информацию о времени
#         проигрывания, названии трека, исполнителе, жанре и продолжительности.

#         Статистика используется для:
#         - Анализа предпочтений аудитории
#         - Расчета ротации музыки
#         - Соблюдения лицензионных требований (раскрытие информации об авторах)
#         - Оценки популярности жанров и исполнителей в точке

#         Args:
#             request: HTTP GET запрос с опциональной пагинацией.
#             pk: UUID номенклатуры.

#         Query Parameters:
#             page (int, optional): Номер страницы для пагинации.
#                                  По умолчанию: 1
#                                  Пример: ?page=2

#         Returns:
#             Response: Пагинированный список объектов статистики музыки.
#                      Структура:
#                      {
#                          'count': 1250,
#                          'next': 'http://api.example.com/statistics/123/music_stat/?page=2',
#                          'previous': None,
#                          'results': [
#                              {
#                                  'id': 'uuid',
#                                  'track_name': 'Bohemian Rhapsody',
#                                  'artist': 'Queen',
#                                  'played': '2026-02-09T14:30:00Z',
#                                  'duration': 354,
#                                  ...
#                              },
#                              ...
#                          ]
#                      }

#         Status Codes:
#             200 OK: Статистика успешно получена
#             404 NOT FOUND: Номенклатура не найдена
#             403 FORBIDDEN: Пользователь не имеет прав доступа

#         Pagination:
#             - Размер страницы: зависит от настроек DRF (обычно 20-100)
#             - Стиль: PageNumberPagination
#             - Ссылки навигации включены в response

#         Examples:
#             >>> # Получить первую страницу статистики музыки
#             >>> response = client.get('/api/statistics/123e4567/music_stat/')
#             >>> response.status_code
#             200
#             >>> response.data['count']
#             1250  # всего записей
#             >>> len(response.data['results'])
#             20    # на странице

#             >>> # Получить вторую страницу
#             >>> response = client.get('/api/statistics/123e4567/music_stat/?page=2')
#             >>> response.status_code
#             200

#         Performance Notes:
#             - Пагинирована, эффективна для больших наборов данных
#             - Каждая страница содержит до N записей (настраивается)
#             - Быстро даже при наличии сотен тысяч записей
#             - Рекомендуется использовать для больших выборок

#         Use Cases:
#             - Анализ аудиторных предпочтений
#             - Исследования рынка музыки
#             - Отчеты по ротации плейлистов
#             - Выплаты авторских вознаграждений

#         Related Methods:
#             - get_ad_stat: статистика рекламы
#             - get_video_stat: статистика видео
#             - get_image_stat: статистика изображений
#         """
#         get_instance_or_404(Nomenclature, pk)
#         statistics = MusicStat.objects.filter(client=pk)
#         page = self.paginate_queryset(statistics)
#         if page is not None:
#             serializer = NomenclatureMusicStatSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#         serializer = NomenclatureMusicStatSerializer(statistics, many=True)
#         return Response(serializer.data, status=HTTP_200_OK)

#     @extend_schema(summary="Получить статистику фоновых видео по номенклатуре")
#     @action(detail=True, methods=["GET"], url_path="video_stat")
#     def get_video_stat(self, request, pk):
#         """
#         Получить пагинированную статистику воспроизведения фоновых видео.

#         Метод возвращает информацию о всех видеоматериалах, которые были
#         воспроизведены в качестве фона на номенклатуре. Фоновые видео - это
#         контент, который проигрывается непрерывно или между основными программами.

#         Статистика включает:
#         - Название и описание видео
#         - Время начала и завершения воспроизведения
#         - Продолжительность показа
#         - Количество просмотров/циклов
#         - Информацию о качестве и формате

#         Используется для:
#         - Мониторинга работоспособности видеоплеера
#         - Аналитики контента
#         - Проверки соответствия расписания
#         - Отладки проблем с трансляцией

#         Args:
#             request: HTTP GET запрос с опциональной пагинацией.
#             pk: UUID номенклатуры.

#         Query Parameters:
#             page (int, optional): Номер страницы для пагинации.
#                                  По умолчанию: 1

#         Returns:
#             Response: Пагинированный список статистики видео.
#                      Структура:
#                      {
#                          'count': 450,
#                          'next': 'http://api.example.com/statistics/123/video_stat/?page=2',
#                          'previous': None,
#                          'results': [
#                              {
#                                  'id': 'uuid',
#                                  'video_name': 'Sunset Background',
#                                  'started': '2026-02-09T00:00:00Z',
#                                  'ended': '2026-02-09T23:59:59Z',
#                                  'duration': 3600,
#                                  'cycles': 24,
#                                  ...
#                              },
#                              ...
#                          ]
#                      }

#         Status Codes:
#             200 OK: Статистика успешно получена
#             404 NOT FOUND: Номенклатура не найдена
#             403 FORBIDDEN: Пользователь не имеет прав доступа

#         Pagination:
#             - Пагинирована для эффективности
#             - Размер страницы: обычно 20-100 записей
#             - Полная поддержка навигации между страницами

#         Examples:
#             >>> response = client.get('/api/statistics/123e4567/video_stat/')
#             >>> response.status_code
#             200
#             >>> response.data['count']
#             450  # всего видеозаписей

#         Performance Notes:
#             - Пагинирована, эффективна для больших наборов
#             - Рекомендуется для频繁ого анализа видеоконтента

#         Use Cases:
#             - Контроль качества видеотрансляции
#             - Аналитика видеоконтента
#             - Диагностика проблем с воспроизведением
#             - Отчеты об использовании фонового контента
#         """
#         get_instance_or_404(Nomenclature, pk)
#         statistics = VideoStat.objects.filter(client=pk)
#         page = self.paginate_queryset(statistics)
#         if page is not None:
#             serializer = NomenclatureVideoStatSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#         serializer = NomenclatureVideoStatSerializer(statistics, many=True)
#         return Response(serializer.data, status=HTTP_200_OK)

#     @extend_schema(summary="Получить статистику фоновых изображений по номенклатуре")
#     @action(detail=True, methods=["GET"], url_path="image_stat")
#     def get_image_stat(self, request, pk):
#         """
#         Получить пагинированную статистику отображения фоновых изображений.

#         Метод возвращает информацию о всех фоновых изображениях (слайдах,
#         картинках, фотографиях), которые были отображены на номенклатуре.

#         Фоновые изображения - это статический или с малой анимацией контент,
#         отображаемый между активными развлекательными программами.

#         Статистика включает:
#         - Название и описание изображения
#         - Время отображения
#         - Длительность показа каждого слайда
#         - Количество циклов ротации
#         - Информацию о размерности и разрешении

#         Используется для:
#         - Анализа использования фоновых слайдов
#         - Оптимизации ротации контента
#         - Проверки работоспособности системы отображения
#         - Аналитики привлекательности изображений

#         Args:
#             request: HTTP GET запрос с опциональной пагинацией.
#             pk: UUID номенклатуры.

#         Query Parameters:
#             page (int, optional): Номер страницы.

#         Returns:
#             Response: Пагинированный список статистики изображений.
#                      Структура каждого элемента:
#                      {
#                          'id': 'uuid',
#                          'image_name': 'Welcome Screen',
#                          'displayed': '2026-02-09T10:30:00Z',
#                          'duration': 10,
#                          'cycles': 96,
#                          'resolution': '1920x1080',
#                          ...
#                      }

#         Status Codes:
#             200 OK: Статистика успешно получена
#             404 NOT FOUND: Номенклатура не найдена
#             403 FORBIDDEN: Пользователь не имеет прав доступа

#         Examples:
#             >>> response = client.get('/api/statistics/123e4567/image_stat/')
#             >>> response.status_code
#             200
#             >>> response.data['count']
#             280  # количество фоновых изображений

#         Use Cases:
#             - Аналитика визуального контента
#             - Оптимизация слайд-шоу
#             - Исследование эффективности изображений
#             - Мониторинг работоспособности дисплея
#         """
#         get_instance_or_404(Nomenclature, pk)
#         statistics = ImageStat.objects.filter(client=pk)
#         page = self.paginate_queryset(statistics)
#         if page is not None:
#             serializer = NomenclatureImageStatSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#         serializer = NomenclatureImageStatSerializer(statistics, many=True)
#         return Response(serializer.data, status=HTTP_200_OK)

#     @extend_schema(summary="Получить статистику бегущих строк по номенклатуре")
#     @action(detail=True, methods=["GET"], url_path="ticker_stat")
#     def get_ticker_stat(self, request, pk):
#         """
#         Получить пагинированную статистику отображения бегущих строк (тикеров).

#         Методовозвращает информацию об всех сообщениях, которые были отображены
#         в виде бегущей строки на номенклатуре.

#         Бегущие строки - это динамический текстовый контент, который прокручивается
#         по экрану, часто используется для новостей, объявлений, скидок и другой
#         важной информации.

#         Статистика включает:
#         - Текст сообщения
#         - Время начала и завершения отображения
#         - Скорость прокрутки
#         - Цвет и шрифт текста
#         - Тип (новость, объявление, скидка и т.д.)

#         Используется для:
#         - Анализа эффективности объявлений
#         - Проверки доставки срочных сообщений
#         - Аудита содержания тикеров
#         - Оптимизации информационного потока

#         Args:
#             request: HTTP GET запрос с опциональной пагинацией.
#             pk: UUID номенклатуры.

#         Query Parameters:
#             page (int, optional): Номер страницы.

#         Returns:
#             Response: Пагинированный список статистики бегущих строк.
#                      Структура:
#                      {
#                          'count': 1890,
#                          'next': 'http://api/statistics/123/ticker_stat/?page=2',
#                          'previous': None,
#                          'results': [
#                              {
#                                  'id': 'uuid',
#                                  'message': 'Скидка 50% на кофе!',
#                                  'displayed': '2026-02-09T12:00:00Z',
#                                  'duration': 10,
#                                  'type': 'announcement',
#                                  'color': '#FF0000',
#                                  ...
#                              },
#                              ...
#                          ]
#                      }

#         Status Codes:
#             200 OK: Статистика успешно получена
#             404 NOT FOUND: Номенклатура не найдена
#             403 FORBIDDEN: Пользователь не имеет прав доступа

#         Pagination:
#             - Пагинирована для производительности
#             - Особенно важна, т.к. бегущих строк может быть много

#         Examples:
#             >>> response = client.get('/api/statistics/123e4567/ticker_stat/')
#             >>> response.status_code
#             200
#             >>> response.data['count']
#             1890  # сообщений за период

#         Use Cases:
#             - Аналитика объявлений и новостей
#             - Контроль доставки критичной информации
#             - Аудит сообщений в тикерах
#             - Оптимизация информационного потока
#             - Анализ частоты и времени сообщений

#         Note:
#             Бегущие строки - наиболее часто обновляемый контент, поэтому
#             пагинация обязательна для производительности.
#         """
#         get_instance_or_404(Nomenclature, pk)
#         statistics = TickerStat.objects.filter(client=pk)
#         page = self.paginate_queryset(statistics)
#         if page is not None:
#             serializer = NomenclatureTickerStatSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
#         serializer = NomenclatureTickerStatSerializer(statistics, many=True)
#         return Response(serializer.data, status=HTTP_200_OK)

#     @extend_schema(
#         summary="Получить историю доступности номенклатуры",
#         request=None,
#         responses={HTTP_200_OK: StatusHistorySerializer},
#     )
#     @action(detail=True, methods=["GET"])
#     def status_history(self, request, pk):
#         """
#         Получить историю всех изменений статуса доступности номенклатуры.

#         Метод возвращает полный журнал всех событий, связанных с доступностью
#         и состоянии номенклатуры (дисплея, рабочей станции и т.д.).

#         История отслеживает:
#         - Подключение и отключение устройства
#         - Переходы онлайн/офлайн
#         - Ошибки и восстановление
#         - Обновления версии ПО
#         - Изменения конфигурации
#         - События синхронизации

#         Используется для:
#         - Анализа надежности оборудования
#         - Выявления проблем с сетевыми соединениями
#         - Проверки графика обслуживания
#         - Диагностики проблем с доставкой контента
#         - Составления отчетов об uptime
#         - SLA монитрирования

#         Args:
#             request: HTTP GET запрос.
#             pk: UUID номенклатуры.

#         Returns:
#             Response: Список объектов истории со статусом и временем.
#                      Структура:
#                      [
#                          {
#                              'id': 'uuid',
#                              'client': 'uuid',
#                              'status': 'online',  # online, offline, error, updating
#                              'changed_at': '2026-02-09T14:30:00Z',
#                              'reason': 'Network connection lost',
#                              'duration': 120,  # секунды
#                              ...
#                          },
#                          ...
#                      ]

#         Status Codes:
#             200 OK: История успешно получена
#             404 NOT FOUND: Номенклатура не найдена
#             403 FORBIDDEN: Пользователь не имеет прав доступа

#         Data Structure (Array of StatusHistory):
#             [
#                 {
#                     'id': '123e4567-e89b-12d3-a456-426614174000',
#                     'status': 'offline',
#                     'timestamp': '2026-02-09T08:00:00Z',
#                     'reason': 'Device powered off',
#                     'duration_seconds': 3600
#                 },
#                 {
#                     'id': '456f7890-a1b2-34cd-ef01-234567890abc',
#                     'status': 'online',
#                     'timestamp': '2026-02-09T09:00:00Z',
#                     'reason': 'Device powered on',
#                     'duration_seconds': 28800
#                 },
#                 ...
#             ]

#         Examples:
#             >>> response = client.get('/api/statistics/123e4567/status_history/')
#             >>> response.status_code
#             200
#             >>> len(response.data)
#             156  # 156 событий в истории
#             >>> response.data[0]['status']
#             'offline'
#             >>> response.data[0]['timestamp']
#             '2026-02-09T08:00:00Z'

#         Performance Notes:
#             - Возвращает всю историю (не пагинирована)
#             - История может быть очень длинной для долгоживущих устройств
#             - Рекомендуется добавить пагинацию при необходимости
#             - Сортируется в обратном хронологическом порядке (новые события первыми)

#         Use Cases:
#             - Анализ надежности системы
#             - Исследование сбоев и простоев
#             - Составление отчетов об uptime/downtime
#             - Диагностика проблем с сетямисвязи
#             - Планирование обслуживания
#             - Выявление закономерностей в отказах

#         Warning:
#             Для долгоживущих систем история может быть очень большой.
#             Рекомендуется добавить фильтрацию по дате или пагинацию.
#         """
#         nomenclature = get_instance_or_404(Nomenclature, pk)
#         history = nomenclature.history.all()
#         serializer = StatusHistorySerializer(history, many=True)
#         return Response(serializer.data, status=HTTP_200_OK)