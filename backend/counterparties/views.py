"""
ViewSet для управления контрагентами.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Использование Prefetch с only() для минимизации данных
2. Использование select_related для FK связей
3. Добавление атрибута _prefetched_brands для оптимизации сериализаторов
"""

from uuid import UUID

from django.db import transaction
from django.db.models import Prefetch, Q
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiResponse,
    OpenApiExample,
)
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_200_OK

from brands.models import Brand
from counterparties.models import (
    Counterparty,
    TYPE_FL,
    TYPE_OPF_DICT,
    TYPE_ORG,
)
from counterparties.serializers import (
    CounterpartiesSerializer,
    CounterpartiesListSerializer,
    CreateCounterpartySerializer,
    CounterpartiesShortSerializer,
)
from users.models import CustomUser


@extend_schema_view(
    list=extend_schema(
        summary="Пагинированный список Контрагентов",
        description="Возвращает постраничный список КА.",
        responses={200: OpenApiResponse(response=CounterpartiesListSerializer)},
    ),
    retrieve=extend_schema(
        summary="Расшифровка КА",
        description="Возвращает полный перечень данных КА по коду 1с или id (UUID)",
        responses={200: OpenApiResponse(response=CounterpartiesSerializer)},
    ),
    create=extend_schema(
        summary="Создание КА",
        description="Создает контрагента. В зависимости от ОПФ требуется различный набор полей.",
        request=CreateCounterpartySerializer,
        responses={201: OpenApiResponse(response=CounterpartiesShortSerializer)},
        examples=[
            OpenApiExample(
                name="Пример ФизЛицо (FL)",
                value={
                    "opf": "FL",
                    "first_name": "Иван",
                    "middle_name": "Иванович",
                    "last_name": "Петров",
                    "contact_persons": ["uuid"],
                    "brands": ["uuid", "uuid"],
                    "description": "Поставщик овощей",
                },
            ),
            OpenApiExample(
                name="Пример ЮрЛицо (OOO)",
                value={
                    "opf": "OOO",
                    "keyword": "ООО Ромашка",
                    "contact_persons": ["uuid"],
                    "brands": ["uuid"],
                    "inn": "7734567890",
                    "description": "Официальный дилер",
                },
            ),
        ],
    ),
)
@extend_schema(tags=["Контрагенты"])
class CounterpartiesViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления контрагентами.

    ОПТИМИЗАЦИЯ ЗАПРОСОВ:
    ────────────────────────────────────────────────────────────────────────────
    1. Предзагрузка связей через select_related и prefetch_related
    2. Использование Prefetch с only() для минимизации данных
    3. Добавление атрибута _prefetched_brands для оптимизации сериализаторов
    """

    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        """
        Оптимизированный запрос с предзагрузкой связей.

        Добавляет атрибут _prefetched_brands для каждого объекта,
        чтобы сериализаторы могли использовать предзагруженные данные.
        """
        queryset = Counterparty.objects.prefetch_related(
            Prefetch(
                "brands",
                queryset=Brand.objects.only("id", "name", "logotype"),
                to_attr="_prefetched_brands",
            ),
            Prefetch(
                "contact_persons",
                queryset=CustomUser.objects.only(
                    "id", "first_name", "last_name", "email"
                ),
                to_attr="_prefetched_contact_persons",
            ),
        ).only(
            "id",
            "first_name",
            "middle_name",
            "last_name",
            "keyword",
            "opf",
            "code1c",
            "inn",
            "is_active",
            "description",
            "broadcast",
            "additional_name",
        )

        user = self.request.user

        if user.is_employee:
            return queryset
        if user.is_contact_person:
            return queryset.filter(contact_persons=user)

        raise NotFound("Страница не найдена!")

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return CreateCounterpartySerializer
        elif self.action == "list":
            return CounterpartiesListSerializer
        else:
            return CounterpartiesSerializer

    @action(
        detail=False,
        methods=["get"],
        url_path="filter-options",
        permission_classes=[IsAuthenticated],
    )
    def filter_options(self, request, *args, **kwargs):
        """Опции фильтра контрагентов доступны только сотрудникам."""
        if request.user.role not in {"manager", "admin", "superuser"}:
            raise PermissionDenied(
                "Фильтр по контрагентам доступен только сотрудникам."
            )

        queryset = self.get_queryset()
        search = request.query_params.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(keyword__icontains=search)
                | Q(first_name__icontains=search)
                | Q(middle_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(inn__icontains=search)
                | Q(code1c__icontains=search)
            )

        page = self.paginate_queryset(queryset)
        serializer = CounterpartiesListSerializer(
            page if page is not None else queryset,
            many=True,
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.is_employee:
            counterparty = serializer.save()
        else:
            counterparty = serializer.save(owner=request.user)
        short = CounterpartiesShortSerializer(counterparty)
        return Response(short.data, status=HTTP_201_CREATED)

    def get_object(self):
        identifier = self.kwargs.get("pk")
        if not identifier:
            raise NotFound("Не указан идентификатор КА.")

        is_uuid = False
        try:
            UUID(str(identifier))
            is_uuid = True
        except ValueError:
            is_uuid = False

        if is_uuid:
            try:
                return self.get_queryset().get(id=identifier)
            except Counterparty.DoesNotExist:
                raise NotFound("КА не найден.")

        try:
            return self.get_queryset().get(code1c=identifier)
        except Counterparty.DoesNotExist:
            raise NotFound("КА не найден.")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)

        instance = self.get_object()
        old_opf = instance.opf
        new_opf = request.data.get("opf", old_opf)
        data = request.data

        if old_opf != new_opf:
            errors = {}

            if new_opf not in TYPE_OPF_DICT:
                return Response(
                    {"errors": {"opf": "Укажите допустимую ОПФ."}},
                    status=400,
                )

            if new_opf in TYPE_ORG:
                keyword = self._text_value(data, "keyword")
                inn = self._text_value(data, "inn")

                if not keyword:
                    errors["keyword"] = "Поле обязательно для юридических лиц."
                if len(inn) != 10:
                    errors["inn"] = "ИНН юридического лица должен содержать 10 цифр."

            elif new_opf in TYPE_FL:
                first = self._text_value(data, "first_name")
                last = self._text_value(data, "last_name")
                inn = self._text_value(data, "inn")

                if not first:
                    errors["first_name"] = "Имя обязательно для физического лица."
                if not last:
                    errors["last_name"] = "Фамилия обязательна для физического лица."
                if len(inn) != 12:
                    errors["inn"] = "ИНН физического лица должен содержать 12 цифр."

            if errors:
                return Response(
                    {"errors": errors, "detail": "Заполните обязательные поля."},
                    status=400,
                )

        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            if old_opf != new_opf:
                instance.inn = ""
                if old_opf in TYPE_FL and new_opf in TYPE_ORG:
                    instance.first_name = ""
                    instance.middle_name = ""
                    instance.last_name = ""
                elif old_opf in TYPE_ORG and new_opf in TYPE_FL:
                    instance.keyword = ""
                instance.opf = new_opf
                instance.save()

            counterparty = serializer.save()
        short = CounterpartiesShortSerializer(counterparty)

        return Response(short.data, status=HTTP_200_OK)

    @staticmethod
    def _text_value(data, field_name):
        value = data.get(field_name, "")
        return value.strip() if isinstance(value, str) else ""
