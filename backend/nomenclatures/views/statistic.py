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
        tags=["Номенклатуры - Статистика"],
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
        tags=["Номенклатуры - Статистика"],
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
        tags=["Номенклатуры - Статистика"],
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
        tags=["Номенклатуры - Статистика"],
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
        tags=["Номенклатуры - Статистика"],
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
        tags=["Номенклатуры - Статистика"],
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
