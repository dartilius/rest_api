from typing import Type, TypeVar, Dict, Set
from functools import lru_cache
from django.db.models import Model
from drf_spectacular.utils import OpenApiExample
from rest_framework import serializers
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)

ModelType = TypeVar("ModelType", bound=Model)


class Constants:
    """Константы для повторного использования."""
    empty_values = ("", [], (), {}, None)


# Кэшируем результаты для часто используемых функций
@lru_cache(maxsize=128)
def get_bg_task_type(order_type: int, action: str) -> int:
    """
    Возвращает соответствующий заказу и действию тип репликации.
    
    Args:
        order_type: Тип заказа (0-3)
        action: Действие ('cancel' или 'update')
        
    Returns:
        int: Тип задачи репликации
        
    Raises:
        ValueError: Если действие не предусмотрено
    """
    # Константы
    ORDER_MUSIC, ORDER_IMAGE, ORDER_VIDEO, ORDER_TICKER = 0, 1, 2, 3
    CANCEL_MUSIC_TASK, CANCEL_IMAGE_TASK, CANCEL_VIDEO_TASK, CANCEL_TICKER_TASK = 5, 6, 7, 8
    UPDATE_MUSIC_TASK, UPDATE_IMAGE_TASK, UPDATE_VIDEO_TASK, UPDATE_TICKER_TASK = 10, 11, 12, 13
    
    # Используем словарь вместо match для обратной совместимости
    task_mapping = {
        "cancel": {
            ORDER_MUSIC: CANCEL_MUSIC_TASK,
            ORDER_IMAGE: CANCEL_IMAGE_TASK,
            ORDER_VIDEO: CANCEL_VIDEO_TASK,
            ORDER_TICKER: CANCEL_TICKER_TASK,
        },
        "update": {
            ORDER_MUSIC: UPDATE_MUSIC_TASK,
            ORDER_IMAGE: UPDATE_IMAGE_TASK,
            ORDER_VIDEO: UPDATE_VIDEO_TASK,
            ORDER_TICKER: UPDATE_TICKER_TASK,
        }
    }
    
    if action not in task_mapping:
        raise ValueError("Такое действие не предусмотрено")
    
    return task_mapping[action].get(order_type)


@lru_cache(maxsize=1)
def get_list_of_file_types() -> Dict[str, Set[str]]:
    """
    Возвращает словарь с типами файлов и соответствующими расширениями.
    
    Returns:
        Dict[str, Set[str]]: Словарь в формате {тип_файла: множество_расширений}
    """
    MUSIC = {"mp3"}
    IMAGE = {"jpg", "jpeg", "png"}
    VIDEO = {"mp4", "avi", "mpg"}
    TICKER = {"txt"}
    AD = MUSIC | VIDEO
    
    return {
        "ad": AD,
        "music": MUSIC,
        "image": IMAGE,
        "video": VIDEO,
        "ticker": TICKER,
    }


@lru_cache(maxsize=2)
def get_minio_client(external=False):
    """
    Создает и возвращает клиент MinIO с кэшированием.
    
    Args:
        external: Флаг для использования внешнего endpoint
        
    Returns:
        Minio: Клиент MinIO
    """
    from minio import Minio
    from django.conf import settings

    endpoint = settings.MINIO_EXTERNAL_ENDPOINT if external else settings.MINIO_ENDPOINT
    secure = settings.MINIO_EXTERNAL_ENDPOINT_USE_HTTPS if external else settings.MINIO_USE_HTTPS
    
    return Minio(
        endpoint,
        region=settings.MINIO_REGION,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=secure,
        cert_check=secure,
    )


def get_instance_or_404(model: Type[ModelType], pk: str) -> ModelType:
    """
    Получает объект модели по UUID или возвращает 404.
    
    Args:
        model: Класс модели Django
        pk: UUID строкой
        
    Returns:
        ModelType: Найденный объект
        
    Raises:
        ValidationError: Если UUID невалидный
        Http404: Если объект не найден
    """
    from django.shortcuts import get_object_or_404
    from rest_framework.exceptions import ValidationError
    from uuid import UUID

    try:
        UUID(pk)
    except ValueError:
        raise ValidationError(f"Значение {pk} не является верным UUID.")
    
    return get_object_or_404(model, id=pk)


def get_instance_list_or_404(model: Type[ModelType], pk_list: list[str]) -> list[ModelType]:
    """
    Получает список объектов по списку UUID.
    
    Args:
        model: Класс модели Django
        pk_list: Список UUID строк
        
    Returns:
        List[ModelType]: Список найденных объектов
        
    Raises:
        ValidationError: Если есть невалидные UUID
        Http404: Если ни один объект не найден
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
        raise ValidationError(f"Значения {bad_pks} не являются верными UUID.")
    
    return get_list_or_404(model, id__in=pk_list)


def restricted_update(viewset, request, *args, **kwargs):
    """
    Ограниченное обновление только разрешенных полей.
    
    Отличия от стандартного update():
    1. Только PATCH запросы
    2. Только поля из updatable_fields
    3. Кастомные сообщения об ошибках
    """
    from rest_framework.response import Response
    from rest_framework.status import HTTP_405_METHOD_NOT_ALLOWED, HTTP_400_BAD_REQUEST

    updatable_fields = kwargs.pop("updatable_fields", [])
    error_message = kwargs.pop(
        "error_message", {"detail": "Нельзя обновить поля: {keys}"}
    )
    partial = kwargs.pop("partial", False)
    
    if not partial:
        return Response(
            data={"detail": 'Метод "PUT" запрещён, используйте "PATCH".'},
            status=HTTP_405_METHOD_NOT_ALLOWED,
        )
    
    instance = viewset.get_object()
    serializer = viewset.get_serializer(
        instance, data=request.data, partial=partial
    )
    
    # Проверка полей до валидации для экономии ресурсов
    bad_keys = {key for key in serializer.initial_data if key not in updatable_fields}
    if bad_keys:
        return Response(
            data={"detail": error_message.format(keys=bad_keys)},
            status=HTTP_400_BAD_REQUEST,
        )
    
    serializer.is_valid(raise_exception=True)
    viewset.perform_update(serializer)
    
    # Очистка prefetch cache
    if getattr(instance, "_prefetched_objects_cache", None):
        instance._prefetched_objects_cache = {}
    
    return Response(serializer.data)


def filter_by_owner_name(queryset, name, value):
    """
    Фильтрация по имени и фамилии создателя.
    
    Поддерживает поиск по комбинации имени и фамилии
    в любом порядке или отдельно.
    """
    from django.db.models import Q

    arg_list = value.strip().split()
    
    if len(arg_list) == 2:
        first_name, last_name = arg_list
        return queryset.filter(
            (Q(owner__last_name__icontains=last_name) & Q(owner__first_name__icontains=first_name)) |
            (Q(owner__last_name__icontains=first_name) & Q(owner__first_name__icontains=last_name))
        )
    elif len(arg_list) == 1:
        return queryset.filter(
            Q(owner__last_name__icontains=value) |
            Q(owner__first_name__icontains=value)
        )
    
    return queryset.none()


class DetailSerializer(serializers.Serializer):
    """Стандартный сериализатор для детальных ответов."""
    detail = serializers.CharField()


class VersionsSerializer(serializers.Serializer):
    """Сериализатор для списка версий."""
    versions = serializers.ListField()


# Кэшируем создание схем ответов
DEFAULT_SCHEMA_RESPONSES = {
    HTTP_400_BAD_REQUEST: DetailSerializer,
    HTTP_401_UNAUTHORIZED: DetailSerializer,
    HTTP_403_FORBIDDEN: DetailSerializer,
    HTTP_404_NOT_FOUND: DetailSerializer,
}

DEFAULT_SCHEMA_EXAMPLES = [
    OpenApiExample(
        "Пользователь неавторизован",
        value={"detail": "Учетные данные не были предоставлены."},
        status_codes=[HTTP_401_UNAUTHORIZED],
        response_only=True,
    )
]
