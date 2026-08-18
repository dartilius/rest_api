"""
ViewSet для веб-интерфейса номенклатур.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Добавлен select_related('owner') для предзагрузки владельца
2. Добавлен only() для выборки только необходимых полей
3. Добавлен prefetch_related для изображений
4. Исправлена ошибка с Nomenclature.web.DoesNotExist
"""

from django.db.models import Count, Prefetch, Q
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from nomenclatures.models import Nomenclature, NomenclatureImage
from nomenclatures.serializers import (
    NomenclatureCardSerializer,
    NomenclatureWebMapPlaceSerializer,
    NomenclatureWebMapResponseSerializer,
    NomenclatureWebSearchRequestSerializer,
    NomenclatureWebSearchResponseSerializer,
    NomenclatureWebSerializer,
)
from rest_framework import viewsets
from uuid import UUID
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny


@extend_schema(tags=["Номенклатуры WEB"])
class NomenclatureWebViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для веб-интерфейса номенклатур.

    ОПТИМИЗАЦИЯ ЗАПРОСОВ:
    ────────────────────────────────────────────────────────────────────────────
    1. Предзагрузка всех связей через select_related и prefetch_related
    2. only() для выборки только необходимых полей
    """

    serializer_class = NomenclatureWebSerializer
    permission_classes = [AllowAny]

    def get_catalog_queryset(self, *, for_map=False):
        """Базовый запрос публичного каталога без N+1 запросов."""
        queryset = Nomenclature.web.select_related(
            "brand",
            "typeOfPlace",
            "availability",
            "address__address__coordinates",
        )
        return queryset.prefetch_related(
            Prefetch(
                "images",
                queryset=NomenclatureImage.objects.filter(type="exterior")
                .order_by("-created", "id")
                .only("id", "source", "nomenclature_id", "created"),
                to_attr="prefetched_facades" if for_map else "prefetched_exterior",
            )
        )

    def apply_search_filters(self, queryset, filters):
        """Применяет набор фильтров, совместимый с текущим GET-списком."""
        search = filters.get("search", "").strip()
        if search:
            queryset = queryset.filter(
                Q(code1c__iexact=search)
                | Q(id_rasb__iexact=search)
                | Q(search_vector__icontains=search.lower())
                | Q(name__istartswith=search)
            )
        if name := filters.get("name"):
            queryset = queryset.filter(name__icontains=name)
        if nomenclature_id := filters.get("id"):
            queryset = queryset.filter(id=nomenclature_id)
        if code1c := filters.get("code1c"):
            queryset = queryset.filter(code1c__iexact=code1c)
        if versions := filters.get("versions"):
            queryset = queryset.filter(version__in=versions)
        if version := filters.get("version"):
            queryset = queryset.filter(version__icontains=version)
        if timezone := filters.get("timezone"):
            queryset = queryset.filter(timezone__iexact=timezone)
        if status := filters.get("status"):
            if status == "null":
                queryset = queryset.filter(availability__status__isnull=True)
            elif status != "3":
                queryset = queryset.filter(availability__status=status)
        counterparty_ids = filters.get("counterparty_ids", [])
        if counterparty_id := filters.get("counterparty_id"):
            counterparty_ids.append(counterparty_id)
        if counterparty_ids:
            queryset = queryset.filter(
                Q(legalEntity_id__in=counterparty_ids)
                | Q(tenants__id__in=counterparty_ids)
            )
        brand_ids = filters.get("brand_ids", [])
        if brand_id := filters.get("brand_id"):
            brand_ids.append(brand_id)
        if brand_ids:
            queryset = queryset.filter(brand_id__in=brand_ids)
        if type_of_place_ids := filters.get("type_of_place_ids"):
            queryset = queryset.filter(typeOfPlace_id__in=type_of_place_ids)
        city_slugs = filters.get("city_slugs", [])
        if city_slug := filters.get("city_slug"):
            city_slugs.append(city_slug)
        if city_slugs:
            queryset = queryset.filter(address__address__city__slug__in=city_slugs)
        if legal_entity_name := filters.get("legal_entity_name"):
            queryset = queryset.filter(legalEntity__name__icontains=legal_entity_name)
        if brand_name := filters.get("brand_name"):
            queryset = queryset.filter(brand__name__icontains=brand_name)
        if type_of_place := filters.get("type_of_place"):
            type_names = [
                value.strip()
                for value in type_of_place.split(",")
                if value.strip()
            ]
            queryset = queryset.filter(typeOfPlace__name__in=type_names)
        if content_types := filters.get("content_types"):
            queryset = queryset.filter(contentType__in=content_types)
        price_from = filters.get("price_from")
        if price_from is not None:
            queryset = queryset.filter(pricePerMonth__gte=price_from)
        price_to = filters.get("price_to")
        if price_to is not None:
            queryset = queryset.filter(pricePerMonth__lte=price_to)
        if filters.get("has_facade") is True:
            queryset = queryset.filter(images__type="exterior")
        elif filters.get("has_facade") is False:
            queryset = queryset.exclude(images__type="exterior")
        return queryset

    def order_search_queryset(self, queryset, filters):
        if filters["ordering"] == "default":
            return (
                queryset.annotate(tenants_count=Count("tenants", distinct=True))
                .order_by("-typeOfPlace__is_mall", "-tenants_count", "-created", "id")
                .distinct()
            )
        ordering = {
            "name": "name",
            "-name": "-name",
            "price_per_month": "pricePerMonth",
            "-price_per_month": "-pricePerMonth",
            "pricePerMonth": "pricePerMonth",
            "-pricePerMonth": "-pricePerMonth",
            "version": "version",
            "-version": "-version",
            "timezone": "timezone",
            "-timezone": "-timezone",
            "brand_name": "brand__name",
            "-brand_name": "-brand__name",
            "legal_entity_name": "legalEntity__name",
            "-legal_entity_name": "-legalEntity__name",
            "type_place": "typeOfPlace",
            "-type_place": "-typeOfPlace",
            "created": "created",
            "-created": "-created",
        }[filters["ordering"]]
        return queryset.order_by(ordering, "id").distinct()

    @extend_schema(
        summary="Поиск номенклатур публичного каталога",
        description=(
            "Read-only аналог текущего GET-списка: фильтры и пагинация "
            "передаются в JSON-теле."
        ),
        request=NomenclatureWebSearchRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="Страница результатов поиска",
                response=NomenclatureWebSearchResponseSerializer,
            )
        },
    )
    @action(detail=False, methods=["post"], url_path="search")
    def search(self, request):
        """Возвращает карточки каталога с фильтрами из JSON-тела."""
        request_serializer = NomenclatureWebSearchRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        filters = request_serializer.validated_data

        queryset = self.order_search_queryset(
            self.apply_search_filters(self.get_catalog_queryset(), filters), filters
        )

        page = filters["page"]
        limit = filters["limit"]
        count = queryset.count()
        start = (page - 1) * limit
        results = queryset[start:start + limit]

        return Response(
            {
                "count": count,
                "page": page,
                "limit": limit,
                "next_page": page + 1 if start + limit < count else None,
                "previous_page": page - 1 if page > 1 else None,
                "results": NomenclatureCardSerializer(results, many=True).data,
            }
        )

    @extend_schema(
        summary="Точки номенклатур для публичной карты",
        description="Возвращает все точки, соответствующие фильтрам из JSON-тела.",
        request=NomenclatureWebSearchRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="Точки карты",
                response=NomenclatureWebMapResponseSerializer,
            )
        },
    )
    @action(detail=False, methods=["post"], url_path="map")
    def map(self, request):
        """Возвращает компактный набор точек для карты без пагинации."""
        request_serializer = NomenclatureWebSearchRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        filters = request_serializer.validated_data
        queryset = self.order_search_queryset(
            self.apply_search_filters(
                self.get_catalog_queryset(for_map=True), filters
            ),
            filters,
        )
        results = NomenclatureWebMapPlaceSerializer(queryset, many=True).data
        return Response({"count": len(results), "results": results})

    def get_queryset(self):
        """
        Оптимизированный запрос для веб-интерфейса.

        Использует:
        - select_related для всех FK связей
        - prefetch_related для M2M связей
        - only() для выборки только необходимых полей
        """
        # Do not cache a QuerySet: Redis pickles it, which evaluates the whole
        # catalogue before the detail lookup is applied. Cache the response data
        # instead if needed.
        return (
            Nomenclature.web
            .select_related(
                "owner",
                "address",
                "address__address__country",
                "address__address__region",
                "address__address__city",
                "address__address__city__locality_type",
                "address__address__street",
                "address__address__street__street_type",
                "address__address__house",
                "address__address__building",
                "responsible_ad",
            )
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=NomenclatureImage.objects.order_by("-created")[:5],
                    to_attr="prefetched_images",
                )
            )
            .only(
                "id", "name", "code1c", "description", "old_catalog_slug",
                "pricePerMonth", "contentType", "for_web", "worktime_start",
                "worktime_end", "possibility", "square", "external_video_media",
                "external_audio_media", "internal_video_media", "internal_audio_media",
                "owner__id", "owner__first_name", "owner__last_name",
                "address__address__id", "address__address__country__name",
                "address__address__region__name", "address__address__city__name",
                "address__address__city__slug",
                "address__address__city__locality_type__name",
                "address__address__street__name",
                "address__address__street__street_type__name",
                "address__address__house__number", "address__address__building__number",
                "responsible_ad__id", "responsible_ad__first_name",
                "responsible_ad__last_name",
            )
        )

    def get_object(self):
        """
        Получает объект номенклатуры по идентификатору.

        Поддерживает поиск по:
        - UUID (id)
        - code1c (код из 1С)
        - old_catalog_slug (старый slug)

        Returns:
            Nomenclature: Объект номенклатуры

        Raises:
            NotFound: Если номенклатура не найдена
        """
        identifier = self.kwargs.get('pk')
        if not identifier:
            raise NotFound("Не указан идентификатор номенклатуры.")

        is_uuid = False
        try:
            UUID(str(identifier))
            is_uuid = True
        except ValueError:
            is_uuid = False

        queryset = self.get_queryset()

        if is_uuid:
            nomenclature = queryset.filter(id=identifier).first()
            if nomenclature:
                return nomenclature
            raise NotFound("Номенклатура не найдена.")

        nomenclature = queryset.filter(code1c=identifier).first()
        if nomenclature:
            return nomenclature

        # old_catalog_slug is a legacy value and existing data can contain
        # duplicates.  A stable ordering prevents a legacy URL from causing 500.
        nomenclature = (
            queryset.filter(old_catalog_slug=identifier)
            .order_by("-created", "id")
            .first()
        )
        if nomenclature:
            return nomenclature

        raise NotFound("Номенклатура не найдена.")

# from drf_spectacular.utils import extend_schema
# from nomenclatures.models import Nomenclature
# from nomenclatures.serializers import NomenclatureWebSerializer
# from rest_framework import viewsets
# from uuid import UUID
# from rest_framework.exceptions import NotFound
# from rest_framework.permissions import AllowAny


# @extend_schema(tags=["Номенклатуры WEB"])
# class NomenclatureWebViewSet(viewsets.ModelViewSet):
#     queryset = Nomenclature.web.select_related(
#         "address",
#         "address__country",
#         "address__region",
#         "address__city",
#         "address__city__locality_type",
#         "address__street",
#         "address__street__street_type",
#         "address__house",
#         "address__building",
#         "responsible_ad"
#     ).all()
#     serializer_class = NomenclatureWebSerializer
#     permission_classes = [AllowAny]

#     def get_object(self):
#         identifier = self.kwargs.get('pk')
#         if not identifier:
#             raise NotFound("Не указан идентификатор номенклатуры.")

#         # Проверяем, валидный ли UUID
#         is_uuid = False
#         try:
#             UUID(str(identifier))
#             is_uuid = True
#         except ValueError:
#             is_uuid = False

#         # Если UUID — ищем по id
#         if is_uuid:
#             try:
#                 nomenclature = Nomenclature.web.get(id=identifier)
#                 return nomenclature
#             except Nomenclature.web.DoesNotExist:
#                 raise NotFound("Номенклатура не найдена.")

#         # Если не UUID — ищем по old_catalog_slug
#         try:
#             nomenclature = Nomenclature.web.get(old_catalog_slug=identifier)
#             return nomenclature
#         except Nomenclature.web.DoesNotExist:
#             raise NotFound("Номенклатура не найдена.")
