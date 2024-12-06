from typing import Type, TypeVar
from django.db.models import Model

ModelType = TypeVar('ModelType', bound=Model)


class Constants:
    """DRY."""

    empty_values = ('', [], (), {}, None)


def get_bg_task_type(order_type: int, action: str) -> int:
    """Возвращает соответствующий заказу и действию тип репликации."""
    ORDER_MUSIC = 0
    ORDER_IMAGE = 1
    ORDER_VIDEO = 2
    ORDER_TICKER = 3
    CANCEL_MUSIC_TASK = 5
    CANCEL_IMAGE_TASK = 6
    CANCEL_VIDEO_TASK = 7
    CANCEL_TICKER_TASK = 8
    UPDATE_MUSIC_TASK = 10
    UPDATE_IMAGE_TASK = 11
    UPDATE_VIDEO_TASK = 12
    UPDATE_TICKER_TASK = 13
    match action:
        case 'cancel':
            order_types_to_task_types = {
                ORDER_MUSIC: CANCEL_MUSIC_TASK,
                ORDER_IMAGE: CANCEL_IMAGE_TASK,
                ORDER_VIDEO: CANCEL_VIDEO_TASK,
                ORDER_TICKER: CANCEL_TICKER_TASK,
            }
        case 'update':
            order_types_to_task_types = {
                ORDER_MUSIC: UPDATE_MUSIC_TASK,
                ORDER_IMAGE: UPDATE_IMAGE_TASK,
                ORDER_VIDEO: UPDATE_VIDEO_TASK,
                ORDER_TICKER: UPDATE_TICKER_TASK,
            }
        case _:
            raise ValueError('Такое действие не предусмотрено')
    return order_types_to_task_types[order_type]


def get_list_of_file_types() -> dict[str, set[str]]:
    """
    Возвращает словарь с типами файлов и соответствующими расширениями,
    в формате:
    {
        тип_файла: список расширений,
        ...
    }
    """
    MUSIC = {'mp3'}
    IMAGE = {'jpg', 'jpeg', 'png'}
    VIDEO = {'mp4', 'avi', 'mpg'}
    TICKER = {'txt'}
    AD = MUSIC | VIDEO
    return {
        'ad': AD,
        'music': MUSIC,
        'image': IMAGE,
        'video': VIDEO,
        'ticker': TICKER
    }


def get_minio_client(external=False):
    """Авторизует запрос для обращений к облаку."""
    from minio import Minio
    from django.conf import settings

    if external:
        endpoint = settings.MINIO_EXTERNAL_ENDPOINT
    else:
        endpoint = settings.MINIO_ENDPOINT
    minio_client = Minio(
        endpoint,
        region=settings.MINIO_REGION,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=settings.MINIO_USE_HTTPS,
        cert_check=settings.MINIO_USE_HTTPS
    )
    return minio_client


def get_instance_or_404(model: Type[ModelType],
                        pk: str) -> ModelType:
    """
    Если в базе существует объект модели {model} с заданным {pk},
    возвращаем его, иначе возвращаем 404_NOT_FOUND.
    Если {pk} не является UUID, возвращаем 400_BAD_REQUEST.
    """
    from django.shortcuts import get_object_or_404
    from rest_framework.exceptions import ValidationError
    from uuid import UUID
    try:
        UUID(pk)
    except ValueError:
        raise ValidationError(f'Значение {pk} не является верным UUID-ом.')
    instance = get_object_or_404(model, id=pk)
    return instance


def get_instance_list_or_404(model: Type[ModelType],
                             pk_list: list[str]) -> list[ModelType]:
    """
    Возвращаем список объектов модели {model} с pk из списка {pk_list},
    если такие существуют. Если не нашлось ни одного объекта,
    возвращаем 404_NOT_FOUND.
    Если хотя бы одного pk не нашлось, дополнительно возвращаем список,
    в котором будут все не найденные объекты.
    Если хотя бы один pk не является UUID, возвращаем 400_BAD_REQUEST.
    """
    from django.shortcuts import get_list_or_404
    from rest_framework.exceptions import ValidationError
    from uuid import UUID
    bad_pks = []
    for pk in pk_list:
        try:
            UUID(pk)
        except ValueError:
            bad_pks.append(pk)
    if bad_pks:
        raise ValidationError(f'Значения {bad_pks} не являются верным UUID-ом.')
    instance_list = get_list_or_404(model, id__in=pk_list)
    return instance_list


def restricted_update(viewset, request, *args, **kwargs):
    """
    Можно изменить только поля, заданные параметром updatable_fields,
    а также разрешено только частичное обновление (метод PATCH).
    Можно задать кастомное сообщение об ошибке параметром error_message.

    Отличия от стандартного метода update():
    1. Проверяем, что получен запрос именно на частичное обновление.
    2. Проверяем, что в запросе есть только ключи из списка updatable_fields.
    2.1 Иначе возвращаем ошибку с сообщением error_message
    """
    from rest_framework.response import Response
    from rest_framework.status import (
        HTTP_405_METHOD_NOT_ALLOWED,
        HTTP_400_BAD_REQUEST
    )

    updatable_fields = kwargs.pop('updatable_fields', [])
    error_message = kwargs.pop('error_message', 'Нельзя обновить поля: {keys}')
    partial = kwargs.pop('partial', False)
    # 1
    if not partial:
        return Response(data='Метод "PUT" запрещён, '
                             'используйте метод "PATCH".',
                        status=HTTP_405_METHOD_NOT_ALLOWED)
    instance = viewset.get_object()
    serializer = viewset.get_serializer(
        instance,
        data=request.data,
        partial=partial
    )
    initial_data = serializer.initial_data
    # 2
    bad_keys = {key for key in initial_data if key not in updatable_fields}
    if bad_keys:
        return Response(
            data=error_message.format(keys=bad_keys),
            status=HTTP_400_BAD_REQUEST
        )
    serializer.is_valid(raise_exception=True)
    viewset.perform_update(serializer)
    if getattr(instance, '_prefetched_objects_cache', None):
        instance._prefetched_objects_cache = {}
    return Response(serializer.data)


def filter_by_owner_name(queryset, name, value):
    """
    Специальный метод для фильтрации по имени и фамилии создателя.

    Поддерживает поиск по фамилии и имени, указанным
    вместе в любом порядке либо отдельно по фамилии или имени.
    При не совпадении или указании более двух аргументов
    ничего не возвращает.
    """
    from django.db.models import Q
    if len(value.split()) == 2:
        first_name, last_name = value.split()
        return queryset.filter(
            (Q(owner__last_name__icontains=last_name) &
             Q(owner__first_name__icontains=first_name)) |
            (Q(owner__last_name__icontains=first_name) &
             Q(owner__first_name__icontains=last_name))
        )
    elif len(value.split()) == 1:
        return queryset.filter(
            Q(owner__last_name__icontains=value) |
            Q(owner__first_name__icontains=value)
        )

