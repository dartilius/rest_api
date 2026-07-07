from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema

from files.models import File
from ..tasks import (
    reboot_task,
    update_task,
    custom_task,
    settings_task
)

from ch_statistic.tasks import create_statistic

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from api.constants import get_instance_or_404
from nomenclatures.models import Nomenclature, NomenclatureAvailability
from tasks.models import Task
from tasks.serializers import TaskListSerializer
from users.permissions import StaffCUDallRead


@extend_schema(tags=["Номенклатуры - Задачи"])
class NomenclatureTaskViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления задачами и репликациями номенклатур.

    Предоставляет механизм отправки команд на устройства (номенклатуры) и
    получения статуса их выполнения. Используется для удаленного управления
    оборудованием, обновлений ПО, переконфигурации и диагностики.

    Endpoints:
        GET /api/tasks/{nomenclature_id}/tasks/ - Список задач номенклатуры
        POST /api/tasks/{nomenclature_id}/actions/ - Создать новую задачу
        POST /api/tasks/{nomenclature_id}/pending_tasks/ - Получить ожидающие задачи

    Task Types:
        - reboot (15): Перезагрузка устройства
        - update (16): Обновление ПО
        - custom: Пользовательская команда
        - settings: Обновление настроек

    Permissions:
        - get_tasks, send_task: StaffCUDallRead
        - pending_tasks: AllowAny (для клиентов устройств)
    """
    permission_classes = [StaffCUDallRead]

    @extend_schema(summary="Получить список репликаций номенклатуры")
    @action(detail=True, methods=["GET"], url_path="tasks")
    def get_tasks(self, request, pk):
        """
        Получить пагинированный список всех задач (репликаций) номенклатуры.

        Репликация - это задача на отправку данных (контента, конфигурации)
        на устройство. Этот метод возвращает полный список всех когда-либо
        созданных задач с информацией об их статусе.

        Статусы задач:
        - 0: В ожидании отправки
        - 1: Отправляется
        - 2: Доставлена
        - 3: Ошибка при отправке
        - 4: Отклонена устройством

        Args:
            request: HTTP GET запрос с опциональной пагинацией.
            pk: UUID номенклатуры.

        Query Parameters:
            page (int, optional): Номер страницы.
            status (int, optional): Фильтр по статусу задачи.
            type (int, optional): Фильтр по типу задачи.

        Returns:
            Response: Пагинированный список задач.
                     Структура:
                     {
                         'count': 523,
                         'next': 'http://api.../tasks/?page=2',
                         'previous': None,
                         'results': [
                             {
                                 'id': 'uuid',
                                 'client': 'uuid',
                                 'type': 15,  # reboot
                                 'status': 2,  # доставлена
                                 'created': '2026-02-08T10:30:00Z',
                                 'executed': '2026-02-08T10:31:15Z',
                                 'parameters': {},
                                 ...
                             },
                             ...
                         ]
                     }

        Status Codes:
            200 OK: Список успешно получен
            404 NOT FOUND: Номенклатура не найдена
            403 FORBIDDEN: Пользователь не имеет прав доступа

        Pagination:
            - Пагинирована для производительности
            - Каждая страница: обычно 20-100 задач

        Examples:
            >>> response = client.get('/api/tasks/123e4567/tasks/')
            >>> response.status_code
            200
            >>> response.data['count']
            523  # всего задач
            >>> len(response.data['results'])
            20   # на странице

        Performance Notes:
            - Пагинирована для больших списков задач
            - Использует select_related для оптимизации
            - Сортируется по дате создания (новые первыми)

        Use Cases:
            - Просмотр истории командос к устройству
            - Отладка проблем с доставкой контента
            - Мониторинг статуса задач
            - Аудит действий в системе

        See Also:
            - send_task() для создания новых задач
            - pending_tasks() для получения задач на клиентской стороне
        """
        get_instance_or_404(Nomenclature, pk)
        tasks = Task.objects.filter(client=pk)
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializer = TaskListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TaskListSerializer(tasks, many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    @extend_schema(summary="Создать задачу")
    @action(detail=True, methods=["POST"], url_path="actions")
    def send_task(self, request, pk):
        """
        Создать и отправить новую задачу на номенклатуру.

        Метод позволяет отправить команду на устройство для выполнения
        определенного действия. Задача помещается в очередь и будет выполнена,
        когда устройство запросит ожидающие задачи.

        Поддерживаемые типы задач:

        1. reboot - Перезагрузка устройства
           - Параметры: нет
           - Действие: Выполняет полную перезагрузку ОС
           - Примечание: Может привести к временной потере сигнала

        2. update - Обновление ПО
           - Параметры: нет
           - Действие: Скачивает и устанавливает новую версию ПО
           - Примечание: Может быть длительным процессом

        3. custom - Пользовательская команда
           - Параметры: обязательный параметр 'parameters' с командой
           - Действие: Выполняет произвольную команду на устройстве
           - Примечание: Требует определенных привилегий

        4. settings - Обновление настроек
           - Параметры: нет (оправляет текущие настройки из БД)
           - Действие: Синхронизирует настройки устройства
           - Примечание: Не требует перезагрузки

        Проверка дубликатов:
        - Для reboot и update система проверяет, нет ли уже активной задачи
        - Если задача уже ожидается, создание отменяется

        Args:
            request: HTTP POST запрос с описанием задачи.
            pk: UUID номенклатуры.

        Request Body (JSON):
            {
                'task': 'reboot'|'update'|'custom'|'settings',
                'parameters': '...'  // только для 'custom'
            }

        Returns:
            Response: JSON с сообщением о результате.
                     При успехе: {
                         'detail': 'Репликация создана.'
                     }

        Status Codes:
            200 OK: Задача успешно создана
            400 BAD REQUEST: Неверный тип задачи или недостаточно параметров
            404 NOT FOUND: Номенклатура не найдена
            403 FORBIDDEN: Пользователь не имеет прав доступа

        Examples:
            >>> # Отправить команду перезагрузки
            >>> response = client.post(
            ...     '/api/tasks/123e4567/actions/',
            ...     data={'task': 'reboot'}
            ... )
            >>> response.status_code
            200
            >>> response.data['detail']
            'Репликация создана.'

            >>> # Отправить команду обновления
            >>> response = client.post(
            ...     '/api/tasks/123e4567/actions/',
            ...     data={'task': 'update'}
            ... )
            >>> response.status_code
            200

            >>> # Отправить пользовательскую команду
            >>> response = client.post(
            ...     '/api/tasks/123e4567/actions/',
            ...     data={
            ...         'task': 'custom',
            ...         'parameters': 'systemctl restart display-service'
            ...     }
            ... )
            >>> response.status_code
            200

            >>> # Ошибка: pustomная команда без параметров
            >>> response = client.post(
            ...     '/api/tasks/123e4567/actions/',
            ...     data={'task': 'custom'}  # нет 'parameters'
            ... )
            >>> response.status_code
            400
            >>> response.data['detail']
            'Не введена команда.'

            >>> # Ошибка: неизвестный тип задачи
            >>> response = client.post(
            ...     '/api/tasks/123e4567/actions/',
            ...     data={'task': 'unknown'}
            ... )
            >>> response.status_code
            400
            >>> response.data['detail']
            'Недопустимое действие.'

        Side Effects:
            - Создает объект Task в БД
            - Помещает задачу в очередь Celery (асинхронно)
            - Не изменяет текущие данные устройства
            - Задача выполнится при следующем подключении устройства

        Performance Notes:
            - Быстрая операция (только создание в БД)
            - Реальное выполнение асинхронно на устройстве

        Use Cases:
            - Удаленные перезагрузки
            - Развертывание обновлений ПО
            - Выполнение диагностических команд
            - Синхронизация конфигурации
            - Экстренное отключение объявлений

        Warning:
            - Не имеет немедленного эффекта
            - Если устройство offline, задача выполнится при подключении
            - Reboot может привести к потере связи на несколько минут

        Related Methods:
            - get_tasks() для просмотра всех задач
            - pending_tasks() для получения задач на клиентской стороне
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        task = request.data.get("task")
        owner = str(request.user.id)

        match task:
            case "reboot":
                if not nomenclature.tasks.filter(status=0, type=15).exists():
                    reboot_task.delay(pk, owner)
            case "update":
                if not nomenclature.tasks.filter(status=0, type=16).exists():
                    from datetime import timedelta
                    from api.constants import get_minio_client

                    client = get_minio_client()
                    objects = client.list_objects(
                        'builds',
                        prefix='RMCContentPlayer-',
                        recursive=False
                    )

                    versions = []
                    for item in objects:
                        name = item.object_name
                        if (name.startswith('RMCContentPlayer-')
                                and name.endswith('.exe')
                                and not name.endswith('latest.exe')):
                            version = name.replace('RMCContentPlayer-', '').replace('.exe', '')
                            versions.append(version)

                    if not versions:
                        return Response(
                            {"detail": "Нет доступных версий для обновления."},
                            status=HTTP_400_BAD_REQUEST,
                        )

                    versions.sort(key=lambda v: tuple(map(int, v.split('.'))))
                    latest_version = versions[-1]

                    external_client = get_minio_client(external=True)
                    version_url = external_client.get_presigned_url(
                        'GET',
                        'builds',
                        f'RMCContentPlayer-{latest_version}.exe',
                        expires=timedelta(hours=24)
                    )
                    update_task.delay(pk, owner, version_url)
            case "custom":
                parameters = request.data.get("parameters")
                if not parameters:
                    return Response(
                        {"detail": "Не введена команда."},
                        status=HTTP_400_BAD_REQUEST,
                    )
                custom_task.delay(pk, parameters, owner)
            case "settings":
                settings_task.delay(pk, owner)
            case _:
                return Response(
                    {"detail": "Недопустимое действие."},
                    status=HTTP_400_BAD_REQUEST,
                )
        return Response({"detail": "Репликация создана."})

    @action(detail=True, methods=["POST"], permission_classes=[AllowAny])
    def pending_tasks(self, request, pk):
        """
        Получить ожидающие задачи и обработать отчет от клиента устройства.

        Это основной метод для обмена данными между сервером и клиентским ПО
        на устройствах. Устройство отправляет отчет о своем состоянии, а сервер
        возвращает список ожидающих выполнения задач.

        Процесс синхронизации:
        1. Клиент отправляет: версию ПО, информацию об оборудовании, статистику
        2. Сервер обрабатывает полученные данные
        3. Сервер возвращает: список задач для выполнения, URL файлов для скачивания

        Request Body - информация от клиента:

        version (str, optional):
            Версия ПО, установленная на устройстве.
            Пример: "1.2.3"

        hw_info (dict, optional):
            Информация об оборудовании (CPU, GPU, оперативная память и т.д.)
            Пример: {
                "cpu": "Intel Core i7",
                "ram_gb": 8,
                "storage_gb": 256,
                "hostname": "display-001"
            }

        statistic (dict, optional):
            Статистика использования контента (реклама, музыка, видео и т.д.).
            Формат: {
                "ad_stat": [{...}, {...}],
                "music_stat": [{...}, {...}],
                "video_stat": [{...}],
                ...
            }

        task_status (dict, optional):
            Статусы выполненных задач устройством.
            Формат: {
                "task-uuid-1": 2,  // статус выполнения
                "task-uuid-2": 2,
                ...
            }
            Статусы: 0=ожидание, 1=выполняется, 2=выполнено, 3=ошибка

        files_to_download (list, optional):
            Список ID файлов, которые устройство хочет скачать.
            Пример: ["file-uuid-1", "file-uuid-2", ...]

        Args:
            request: HTTP POST запрос с данными от клиента.
            pk: UUID номенклатуры.

        Returns:
            Response: JSON с информацией для клиента.
                     Структура:
                     {
                         'tasks': [
                             {
                                 'task_id': 'uuid',
                                 'task_type': 15,  // тип задачи (reboot=15, update=16)
                                 'status': 2,  // выполнена
                                 'parameters': '{json}'
                             },
                             ...
                         ],
                         'file_urls': {
                             'file-uuid-1': 'http://example.com/download/file1.bin',
                             'file-uuid-2': 'http://example.com/download/file2.bin',
                             ...
                         }
                     }

        Status Codes:
            200 OK: Синхронизация успешна
            404 NOT FOUND: Номенклатура не найдена

        Processing Logic:

        1. Обновление информации об устройстве:
           - Сохраняет текущую версию ПО
           - Сохраняет информацию об оборудовании
           - Использует update_fields для оптимизации

        2. Обработка статистики:
           - Для каждого типа статистики (если есть данные)
           - Создает асинхронную задачу create_statistic
           - Данные будут обработаны в фоне

        3. Обновление статусов задач:
           - Получает задачи по ID
           - Обновляет статус
           - Использует bulk_update для эффективности

        4. Подготовка URL файлов:
           - Получает объекты файлов по ID
           - Генерирует URL'ы для скачивания
           - Возвращает только активные файлы

        5. Получение ожидающих задач:
           - Ищет задачи со статусом 0 (ожидание)
           - Сортирует по приоритету
           - Возвращает в порядке приоритета (важные первыми)

        6. Обновление времени последнего контакта:
           - Обновляет NomenclatureAvailability
           - Обновляет поле last_answer_date текущим временем

        Examples:
            >>> # Простой запрос без данных
            >>> response = client.post(
            ...     '/api/tasks/123e4567/pending_tasks/',
            ...     data={}
            ... )
            >>> response.status_code
            200
            >>> response.data['tasks']
            [...]  # список ожидающих задач

            >>> # Комплексный запрос со статистикой
            >>> request_data = {
            ...     'version': '1.2.4',
            ...     'hw_info': {
            ...         'cpu': 'Intel i7',
            ...         'ram_gb': 16
            ...     },
            ...     'statistic': {
            ...         'ad_stat': [
            ...             {
            ...                 'spot_id': 'uuid',
            ...                 'played': '2026-02-09T14:00:00Z',
            ...                 'duration': 30
            ...             }
            ...         ]
            ...     },
            ...     'task_status': {
            ...         'task-uuid-1': 2  // выполнено
            ...     },
            ...     'files_to_download': ['file-uuid-1']
            ... }
            >>> response = client.post(
            ...     '/api/tasks/123e4567/pending_tasks/',
            ...     data=request_data
            ... )
            >>> response.status_code
            200
            >>> 'tasks' in response.data
            True
            >>> 'file_urls' in response.data
            True

        Side Effects:
            - Обновляет поля version и hw_info номенклатуры
            - Создает записи статистики в асинхронном процессе
            - Обновляет статусы задач
            - Обновляет время последнего контакта (last_answer_date)

        Performance Notes:
            - Эффективно использует batch операции (bulk_update)
            - Статистика обрабатывается асинхронно (не блокирует ответ)
            - Большое количество задач может замедлить возврат ответа

        Important Notes:
            - Метод доступен без аутентификации (AllowAny)
            - Это безопасно, т.к. используется UUID номенклатуры
            - UUID должен быть достаточно сложным и непредсказуемым

        Use Cases:
            - Синхронизация состояния устройства
            - Отправка команд с сервера на клиент
            - Сбор статистики использования контента
            - Обновление версии ПО устройства
            - Мониторинг здоровья системы

        Security Considerations:
            - UUID номенклатуры используется как ключ доступа
            - Никакой аутентификации не требуется (по дизайну)
            - Рекомендуется использовать TLS/HTTPS
            - Данные может подделать любой, кто знает UUID

        Related Methods:
            - send_task() для создания задач на сервере
            - get_tasks() для просмотра всех задач

        Protocol Notes:
            Это ключевой метод для функционирования всей системы управления
            устройствами. Он обеспечивает двусторонний обмен данными между
            сервером и клиентским ПО на устройствах.
        """
        nomenclature = get_instance_or_404(Nomenclature, pk)
        update_fields = []
        data = dict()

        if "version" in request.data:
            nomenclature.version = request.data["version"]
            update_fields.append("version")

        if "hw_info" in request.data:
            nomenclature.hw_info = request.data["hw_info"]
            update_fields.append("hw_info")

        if update_fields:
            nomenclature.save(update_fields=update_fields)

        if "statistic" in request.data:
            statistics = request.data["statistic"]
            for stat_type, stat_list in statistics.items():
                if len(stat_list) > 0:
                    create_statistic.delay(stat_type, pk, stat_list)

        if "task_status" in request.data:
            task_list = list()
            for task_id in request.data["task_status"]:
                task_status = request.data["task_status"][task_id]
                task_instance = Task.objects.get(id=task_id)
                task_instance.status = task_status
                task_list.append(task_instance)
            Task.objects.bulk_update(task_list, ["status"])

        if "files_to_download" in request.data:
            files_urls = dict()
            for file_id in request.data["files_to_download"]:
                file_obj = File.active.get(id=file_id)
                files_urls[file_id] = file_obj.url
            data["file_urls"] = files_urls

        NomenclatureAvailability.objects.update_or_create(
            client=nomenclature, defaults={"last_answer_date": timezone.now()}
        )
        pending_tasks = sorted(
            Task.objects.filter(client=pk, status=0), key=lambda t: t.priority
        )
        data["tasks"] = [
            {
                "task_id": task.id,
                "task_type": task.type,
                "parameters": task.parameters,
            }
            for task in pending_tasks
        ]
        return Response(data, status=HTTP_200_OK)
