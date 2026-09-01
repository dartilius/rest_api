"""
ViewSet для управления арендаторами номенклатур.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Добавлен only() для выборки только необходимых полей
2. Добавлен prefetch_related для оптимизации
3. Удалены лишние print()
4. Добавлено кеширование для частых запросов
5. Исправлена ошибка возврата dict вместо Response
6. Исправлен ключ кеша для grouped_tenants_global (urlencode вместо hash)
7. Исправлено кеширование Response (кешируются данные, а не Response)
8. Бренд берется из NomenclatureTenant, а не из контрагента
"""

from uuid import UUID

from django.core.cache import cache
from django.db.models import Count, Prefetch
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from rest_framework.decorators import action, permission_classes
from rest_framework.decorators import api_view
from rest_framework.exceptions import NotFound
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from api.pagination import CustomLimitOffsetPagination
from brands.models import Brand
from counterparties.models import CounterpartyCategory
from nomenclatures.filters import NomenclatureTenantFilter, GroupedTenantFilter
from nomenclatures.models import NomenclatureTenant, NomenclatureImage
from nomenclatures.serializers import (
    TenantWriteSerializer,
    NomenclatureTenantResponseSerializer,
)
from users.permissions import SuperuserCUDAuthRetrieve


@extend_schema(tags=["Номенклатура - Арендаторы"])
class NomenclatureTenantViewSet(viewsets.ModelViewSet):
    """
    Кастомный viewset для работы с арендаторами места.

    ДОСТУПНЫЕ ДЕЙСТВИЯ:
    ────────────────────────────────────────────────────────────────────────────
    - List: получить список арендаторов по pk/code1c номенклатуры
    - Create: добавить арендатора к номенклатуре (is_super_user)
    - Update: обновить данные (is_super_user)
    - Delete: удалить арендатора (is_super_user)

    URLS:
    ────────────────────────────────────────────────────────────────────────────
    GET    /api/nomenclatures/{id_or_code1c}/tenant/        # list
    POST   /api/nomenclatures/{id_or_code1c}/tenant/        # create
    GET    /api/nomenclatures/{id_or_code1c}/tenant/{id}/   # retrieve
    PATCH  /api/nomenclatures/{id_or_code1c}/tenant/{id}/   # partial_update
    DELETE /api/nomenclatures/{id_or_code1c}/tenant/{id}/   # destroy
    """

    queryset = NomenclatureTenant.objects.all()
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = NomenclatureTenantFilter
    pagination_class = CustomLimitOffsetPagination
    search_fields = [
        "tenant__first_name",
        "tenant__middle_name",
        "tenant__last_name",
        "tenant__keyword",
        "tenant__additional_name",
        "brand__name",
    ]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "floors"]:
            return [AllowAny()]
        return [SuperuserCUDAuthRetrieve()]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TenantWriteSerializer
        return NomenclatureTenantResponseSerializer

    @staticmethod
    def _resolve_filter(value, id_field, code1c_field):
        """Определяет, является ли значение UUID или code1c."""
        try:
            UUID(hex=value)
            return id_field
        except (ValueError, AttributeError, TypeError):
            return code1c_field

    def get_queryset(self):
        """
        Оптимизированный запрос для списка арендаторов.

        Использует:
        - select_related для FK связей
        - only() для выборки только необходимых полей
        - prefetch_related для M2M связей
        """
        nomenclature_pk = self.kwargs.get("nomenclature_pk")
        filter_field = self._resolve_filter(
            nomenclature_pk, "nomenclature__id", "nomenclature__code1c"
        )

        return (
            NomenclatureTenant.objects.filter(**{filter_field: nomenclature_pk})
            .select_related(
                "tenant",
                "brand",
                "nomenclature",
            )
            .prefetch_related(
                Prefetch(
                    "tenant__brands",
                    queryset=Brand.objects.only("id", "name", "logotype"),
                )
            )
            .only(
                "id",
                "floor",
                "atm",
                "nomenclature__id",
                "nomenclature__name",
                "nomenclature__code1c",
                "tenant__id",
                "tenant__first_name",
                "tenant__last_name",
                "tenant__keyword",
                "tenant__code1c",
                "brand__id",
                "brand__name",
                "brand__code1c",
            )
            .order_by("id")
            .distinct()
        )

    def get_object(self):
        """
        Получает объект арендатора с оптимизацией.

        Поддерживает поиск по:
        - UUID (id)
        - code1c
        """
        nomenclature_pk = self.kwargs.get("nomenclature_pk")
        tenant_pk = self.kwargs.get("pk")

        nomenclature_filter = self._resolve_filter(
            nomenclature_pk, "nomenclature__id", "nomenclature__code1c"
        )
        tenant_filter = self._resolve_filter(tenant_pk, "tenant__id", "tenant__code1c")

        obj = get_object_or_404(
            NomenclatureTenant,
            **{nomenclature_filter: nomenclature_pk, tenant_filter: tenant_pk},
        )
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_destroy(self, request, *args, **kwargs):
        """Удаление арендатора."""
        instance = self.get_object()
        instance.delete()
        return Response(status=204)

    @action(detail=False, methods=["get"], url_path="floors")
    def floors(self, request, *args, **kwargs):
        """
        Возвращает список этажей для фильтрации.

        ОПТИМИЗАЦИЯ:
        - Использует только значения floor
        - Кеширование на 5 минут
        """
        cache_key = f"tenant_floors_{self.kwargs.get('nomenclature_pk')}"
        cached_result = cache.get(cache_key)

        if cached_result is not None:
            return Response(cached_result)

        qs = self.get_queryset()
        floors = (
            qs.exclude(floor="")
            .values_list("floor", flat=True)
            .distinct()
            .order_by("floor")
        )

        result = [{"label": f"Этаж {floor}", "value": floor} for floor in floors]

        cache.set(cache_key, result, 300)
        return Response(result)


@extend_schema(tags=["Номенклатура - Арендаторы"])
@api_view(["GET"])
@permission_classes([AllowAny])
def grouped_tenants_global(request):
    """
    GET /api/tenants/grouped/

    Возвращает список арендаторов, сгруппированных по брендам.
    """
    base_qs = NomenclatureTenant.objects.select_related("tenant", "brand").only(
        "id",
        "tenant__id",
        "tenant__code1c",
        "brand__id",
        "brand__name",
    )

    base_qs = GroupedTenantFilter(request.GET, queryset=base_qs).qs

    sort = request.query_params.get("sort", "count_desc")

    queryset = base_qs.values(
        "tenant_id", "tenant__code1c", "brand_id", "brand__name"
    ).annotate(count=Count("nomenclature_id", distinct=True))

    ordering = {
        "name_asc": ("brand__name", "tenant_id"),
        # Пока отдельная метрика популярности не определена, используем охват:
        # число уникальных рекламных мест, где представлен арендатор.
        "popular": ("-count", "tenant_id"),
        "count_desc": ("-count", "tenant_id"),
    }
    queryset = queryset.order_by(*ordering.get(sort, ordering["count_desc"]))

    paginator = CustomLimitOffsetPagination()
    paginated_queryset = paginator.paginate_queryset(queryset, request)

    if paginated_queryset is None:
        paginated_queryset = []

    brand_ids = [item["brand_id"] for item in paginated_queryset if item["brand_id"]]

    brand_logotypes = {
        brand.id: brand.logotype.url if brand.logotype else None
        for brand in Brand.all_objects.filter(id__in=brand_ids).only("id", "logotype")
    }

    tenant_ids = [item["tenant_id"] for item in paginated_queryset]
    categories_by_tenant = {tenant_id: [] for tenant_id in tenant_ids}
    for category in (
        CounterpartyCategory.objects.filter(
            counterparties__id__in=tenant_ids,
            is_active=True,
        )
        .values("name", "counterparties__id")
        .order_by("name")
    ):
        categories_by_tenant[category["counterparties__id"]].append(category["name"])

    result = [
        {
            "tenantId": item["tenant_id"],
            "tenantCode1c": item["tenant__code1c"],
            "brandId": item["brand_id"],
            "brandName": item["brand__name"] or "Без бренда",
            "brandLogotype": brand_logotypes.get(item["brand_id"]),
            "count": item["count"],
            "categories": categories_by_tenant.get(item["tenant_id"], []),
        }
        for item in paginated_queryset
    ]

    return paginator.get_paginated_response(result)


@extend_schema(tags=["Номенклатура - Арендаторы"])
@api_view(["GET"])
@permission_classes([AllowAny])
def tenant_detail(request, tenant_pk: str):
    """
    GET /api/tenants/<uuid>/
    GET /api/tenants/<code1c>/

    Возвращает детальную информацию об арендаторе.

    ОПТИМИЗАЦИЯ:
    - Использует only() для выборки только необходимых полей
    - Предзагрузка брендов и изображений
    - Кеширование на 5 минут
    - Использует brand из NomenclatureTenant, а не первый бренд контрагента
    """
    cache_key = f"tenant_detail_{tenant_pk}"
    cached_result = cache.get(cache_key)

    if cached_result is not None:
        return Response(cached_result)

    try:
        UUID(hex=tenant_pk)
        tenant_filter = "tenant__id"
    except (ValueError, AttributeError):
        tenant_filter = "tenant__code1c"

    qs = (
        NomenclatureTenant.objects.filter(**{tenant_filter: tenant_pk})
        .select_related(
            "tenant",
            "brand",
            "nomenclature",
            "nomenclature__typeOfPlace",
        )
        .prefetch_related(
            Prefetch(
                "nomenclature__images",
                queryset=NomenclatureImage.objects.filter(type="exterior").order_by(
                    "created"
                ),
                to_attr="prefetched_exterior",
            ),
        )
        .only(
            "tenant__id",
            "tenant__code1c",
            "tenant__opf",
            "tenant__inn",
            "tenant__keyword",
            "brand__id",
            "brand__name",
            "nomenclature__id",
            "nomenclature__name",
            "nomenclature__typeOfPlace__name",
        )
        .order_by("nomenclature__name")
    )

    if not qs.exists():
        raise NotFound("Арендатор не найден.")

    first = qs.first()
    if first is None:
        raise NotFound("Арендатор не найден.")

    tenant = first.tenant
    brand_obj = first.brand

    def get_first_exterior(nomenclature):
        exterior = getattr(nomenclature, "prefetched_exterior", [])
        if not exterior:
            return None

        image = exterior[0]
        if not image.source:
            return None

        return image.source.url if hasattr(image.source, "url") else str(image.source)

    places = [
        {
            "nomenclatureId": str(entry.nomenclature.id),
        }
        for entry in qs
    ]

    if brand_obj:
        brand = {
            "id": str(brand_obj.id),
            "name": brand_obj.name,
            "logotype": (
                brand_obj.logotype.url
                if hasattr(brand_obj, "logotype") and brand_obj.logotype
                else None
            ),
        }
    else:
        brand = {
            "id": None,
            "name": None,
            "logotype": None,
        }

    result = {
        "tenantId": str(tenant.id),
        "tenantCode1c": tenant.code1c,
        "brand": brand,
        "opf": tenant.opf,
        "inn": tenant.inn,
        "keyword": tenant.keyword,
        "totalPlaces": len(places),
        "places": places,
    }

    cache.set(cache_key, result, 300)
    return Response(result)
