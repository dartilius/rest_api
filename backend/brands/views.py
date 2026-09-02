"""ViewSet для управления брендами."""

from uuid import UUID

from django.db.models import Min, Prefetch, Q as DjangoQ
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from opensearchpy.helpers.search import Q as OpenSearchQ

from api.mixins import SignedMediaNoCacheMixin
from api.pagination import CustomLimitOffsetPagination
from brands.documents import BrandDocument
from brands.filters import BrandFilter
from brands.models import Brand
from brands.serializers import (
    BrandCreateSerializer,
    BrandDetailSerializer,
    BrandListSerializer,
    BrandShortSerializer,
)
from nomenclatures.models import Nomenclature, NomenclatureImage
from nomenclatures.serializers import NomenclatureShortSerializer
from services.api_1c_client import logger

OPENSEARCH_MAX_RESULTS = 1000


def get_brand_min_price_qs(queryset):
    """Добавляет цену из опубликованных активных номенклатур бренда."""
    return queryset.annotate(
        min_price=Min(
            "nomenclatures__pricePerMonth",
            filter=DjangoQ(
                nomenclatures__for_web=True,
                nomenclatures__is_active=True,
            ),
        ),
    )


@extend_schema_view(
    list=extend_schema(
        summary="Получить пагинированный список брендов",
        responses={200: BrandListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Получить бренд",
        parameters=[
            OpenApiParameter(
                name="id_or_code1c",
                description="UUID бренда, код 1С или slug",
                required=True,
                type=str,
                location=OpenApiParameter.PATH,
            ),
        ],
        responses={200: BrandDetailSerializer},
    ),
    create=extend_schema(
        summary="Создать новый бренд",
        request=BrandCreateSerializer,
        responses={201: BrandShortSerializer},
    ),
    partial_update=extend_schema(
        summary="Частично обновить бренд",
        request=BrandCreateSerializer,
        responses={200: BrandListSerializer},
    ),
)
@extend_schema(tags=["Бренды"])
class BrandViewSet(SignedMediaNoCacheMixin, viewsets.ModelViewSet):
    """Публичное чтение и аутентифицированное управление брендами."""

    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "id_or_code1c"
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Brand.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = BrandFilter
    pagination_class = CustomLimitOffsetPagination

    def get_serializer_class(self):
        if self.action in ("create", "partial_update"):
            return BrandCreateSerializer
        if self.action == "retrieve":
            return BrandDetailSerializer
        return BrandListSerializer

    def list(self, request, *args, **kwargs):
        """Возвращает бренды, у которых есть опубликованные активные точки."""
        search_query = request.query_params.get("search", "").strip()
        active_brand_ids = Nomenclature.web.values("brand_id").distinct()
        queryset = self.filter_queryset(self.get_queryset().filter(id__in=active_brand_ids))

        if search_query:
            queryset = queryset.filter(id__in=self._opensearch_brand_ids(search_query))

        queryset = get_brand_min_price_qs(queryset)
        page = self.paginate_queryset(queryset)
        serializer = BrandListSerializer(page, many=True)
        response = self.get_paginated_response(serializer.data)
        response.data["min_price"] = queryset.aggregate(min_price=Min("min_price"))["min_price"]
        return response

    def _opensearch_brand_ids(self, query: str) -> list:
        """Ищет идентификаторы брендов в OpenSearch, с fallback на PostgreSQL."""
        try:
            search = BrandDocument.search().filter("term", is_deleted=False)
            search = search.query(
                OpenSearchQ(
                    "multi_match",
                    query=query,
                    fields=[
                        "name^3",
                        "name.autocomplete^2",
                        "description",
                        "description.autocomplete",
                    ],
                    fuzziness="AUTO",
                    type="best_fields",
                )
                | OpenSearchQ("prefix", code1c={"value": query.lower()})
                | OpenSearchQ("prefix", slug={"value": query.lower()})
            )
            return [hit.meta.id for hit in search.extra(size=OPENSEARCH_MAX_RESULTS).execute()]
        except Exception as error:
            logger.warning("OpenSearch недоступен, fallback на БД: %s", error)
            return list(
                Brand.objects.filter(
                    name__icontains=query,
                    id__in=Nomenclature.web.values("brand_id").distinct(),
                ).values_list("id", flat=True)
            )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        brand = serializer.save()
        return Response(BrandShortSerializer(brand).data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        """Ищет бренд по UUID, коду 1С или slug и добавляет минимальную цену."""
        identifier = self.kwargs.get(self.lookup_field)
        if not identifier:
            raise NotFound("Не указан идентификатор бренда.")

        queryset = get_brand_min_price_qs(Brand.all_objects)

        try:
            brand = queryset.get(id=UUID(str(identifier)))
        except (ValueError, Brand.DoesNotExist):
            pass
        else:
            if brand.is_deleted:
                raise NotFound("Бренд не найден.")
            return brand

        try:
            brand = queryset.get(code1c=identifier)
        except Brand.DoesNotExist:
            pass
        else:
            if brand.is_deleted:
                raise NotFound("Бренд не найден.")
            return brand

        try:
            brand = queryset.get(slug=identifier)
        except Brand.DoesNotExist:
            raise NotFound("Бренд не найден.")

        if brand.is_deleted:
            raise NotFound("Бренд не найден.")
        return self._validate_brand_has_active_nomenclatures(brand)

    def _validate_brand_has_active_nomenclatures(self, brand: Brand) -> Brand:
        if not Nomenclature.web.filter(brand=brand).exists():
            raise NotFound("Бренд не найден.")
        return brand

    @extend_schema(summary="Удалить логотип бренда", responses={204: None})
    @action(methods=["POST"], detail=True, url_path="unpin_logo")
    def unpin_logo(self, request, *args, **kwargs):
        """Отвязывает логотип; пустое поле считается уже очищенным."""
        brand = self.get_object()
        if brand.logotype:
            brand.logotype.delete(save=False)
        brand.logotype = None
        brand.save(update_fields=["logotype"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(summary="Получить бренды с опубликованными активными точками")
    @action(methods=["GET"], detail=False, url_path="assigned", url_name="assigned")
    def assigned(self, request, *args, **kwargs):
        active_brand_ids = Nomenclature.web.values("brand_id").distinct()
        queryset = Brand.objects.filter(id__in=active_brand_ids)

        search_query = request.query_params.get("search", "").strip()
        if search_query:
            queryset = queryset.filter(id__in=self._opensearch_brand_ids(search_query))

        page = self.paginate_queryset(get_brand_min_price_qs(queryset))
        return self.get_paginated_response(BrandListSerializer(page, many=True).data)

    @extend_schema(summary="Получить номенклатуры бренда", responses={200: NomenclatureShortSerializer(many=True)})
    @action(methods=["GET"], detail=True, url_path="nomenclatures", url_name="nomenclatures")
    def nomenclatures(self, request, *args, **kwargs):
        """Возвращает номенклатуры бренда без N+1 запросов сериализатора."""
        brand = self.get_object()
        queryset = (
            Nomenclature.web.filter(brand=brand)
            .select_related(
                "address__address__city",
                "address__address__street",
                "address__address__house",
                "address__address__building",
                "typeOfPlace",
            )
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=NomenclatureImage.objects.filter(type="exterior").only(
                        "id", "source", "type", "nomenclature_id",
                    ),
                    to_attr="prefetched_exterior",
                ),
            )
        )
        return Response(NomenclatureShortSerializer(queryset, many=True).data)
