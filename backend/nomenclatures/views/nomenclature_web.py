"""
ViewSet для веб-интерфейса номенклатур.

ОПТИМИЗАЦИЯ:
───────────────────────────────────────────────────────────────────────────────
1. Добавлен select_related('owner') для предзагрузки владельца
2. Добавлен only() для выборки только необходимых полей
3. Добавлен prefetch_related для изображений
4. Исправлена ошибка с Nomenclature.web.DoesNotExist
"""

from drf_spectacular.utils import extend_schema
from nomenclatures.models import Nomenclature, NomenclatureImage
from nomenclatures.serializers import NomenclatureWebSerializer
from rest_framework import viewsets
from uuid import UUID
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from django.db.models import Prefetch


@extend_schema(tags=["Номенклатуры WEB"])
class NomenclatureWebViewSet(viewsets.ModelViewSet):
    """
    ViewSet для веб-интерфейса номенклатур.

    ОПТИМИЗАЦИЯ ЗАПРОСОВ:
    ────────────────────────────────────────────────────────────────────────────
    1. Предзагрузка всех связей через select_related и prefetch_related
    2. only() для выборки только необходимых полей
    """

    serializer_class = NomenclatureWebSerializer
    permission_classes = [AllowAny]

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
