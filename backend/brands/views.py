from uuid import UUID

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiExample, OpenApiParameter
from rest_framework import status
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK, HTTP_204_NO_CONTENT,
)
from rest_framework.decorators import action

from api.constants import (
    DEFAULT_SCHEMA_EXAMPLES, DEFAULT_SCHEMA_RESPONSES,
)
from api.pagination import CustomLimitOffsetPagination
from brands.filters import BrandFilter
from brands.models import Brand
from brands.serializers import BrandCreateSerializer, BrandShortSerializer, BrandDetailSerializer, BrandListSerializer
from nomenclatures.serializers import NomenclatureShortSerializer
from services.api_1c_client import api_1c, logger


@extend_schema_view(
    list=extend_schema(
        summary="Получить пагинированный список брендов",
        examples=[
                     OpenApiExample(
                         "Список брендов",
                         response_only=True,
                         value={
                             "id": "db2f3774-9d0a-4340-8183-b5130e0d073d",
                             "name": "django drf test",
                             "logotype": "http://192.168.0.90/local-media/brand_logo/example.png",
                             "created": "2025-10-17T10:42:15.434767",
                             "description": "django drf test",
                             "code1c": "0001"
                         },
                         status_codes=[HTTP_200_OK],
                     )
                 ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_200_OK: BrandListSerializer(many=True)} | DEFAULT_SCHEMA_RESPONSES,
    ),
    retrieve=extend_schema(
        summary="Получить расшифровку бренда",
        parameters=[
            OpenApiParameter(
                name='id_or_code1c',
                description='UUID бренда или код 1С',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ],
        examples=[
                     OpenApiExample(
                         "Пример бренда",
                         status_codes=[HTTP_200_OK],
                         response_only=True,
                         value={
                             "id": "db2f3774-9d0a-4340-8183-b5130e0d073d",
                             "name": "django drf test",
                             "logotype": "http://192.168.0.90/local-media/brand_logo/example.png",
                             "created": "2025-10-17T10:42:15.434767",
                             "description": "django drf test",
                             "code1c": "0001"
                         },
                     )
                 ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_200_OK: BrandListSerializer} | DEFAULT_SCHEMA_RESPONSES,
    ),
    destroy=extend_schema(
        summary="Удалить бренд",
        parameters=[
            OpenApiParameter(
                name='id_or_code1c',
                description='UUID бренда или код 1С',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ],
        examples=[
                     OpenApiExample(
                         "Бренд успешно удален",
                         status_codes=[HTTP_204_NO_CONTENT],
                         response_only=True,
                     )
                 ] + DEFAULT_SCHEMA_EXAMPLES,
        responses={HTTP_204_NO_CONTENT: {}} | DEFAULT_SCHEMA_RESPONSES,
    ),
    create=extend_schema(
        summary="Создать новый бренд",
        description="Создает бренд. Если бренд с таким code1c уже существует, вернется ошибка. Поле code1c можно не отправлять.",
        request=BrandCreateSerializer,
        responses={
            201: BrandShortSerializer,
            400: {
                "description": "Бренд с таким code1c уже существует",
                "content": {
                    "application/json": {
                        "example": {
                            "error": "Brand with this code1c already exists",
                            "existing_brand_id": "db2f3774-9d0a-4340-8183-b5130e0d073d",
                            "existing_brand_name": "django drf test",
                            "existing_brand_code1c": "0001",
                            "message": "Бренд с кодом '0001' уже существует"
                        }
                    }
                }
            }
        },
        examples=[
            OpenApiExample(
                "Успешно создан с code1c",
                value={
                    "name": "django drf test",
                    "code1c": "0002",
                    "id": "db2f3774-9d0a-4340-8183-b5130e0d073d"
                },
                status_codes=[201],
            ),
            OpenApiExample(
                "Успешно создан без code1c",
                value={
                    "name": "django drf test without code1c",
                    "id": "db2f3774-9d0a-4340-8183-b5130e0d073d",
                    "code1c": "null"
                },
                status_codes=[201],
            ),
            OpenApiExample(
                "Бренд с code1c уже существует",
                value={
                    "error": "Brand with this code1c already exists",
                    "existing_brand_id": "db2f3774-9d0a-4340-8183-b5130e0d073d",
                    "existing_brand_name": "django drf test",
                    "existing_brand_code1c": "0001",
                    "message": "Бренд с кодом '0001' уже существует"
                },
                status_codes=[400],
            ),
        ]
    ),
    partial_update=extend_schema(
        summary="Частичное обновление бренда",
        parameters=[
            OpenApiParameter(
                name='id_or_code1c',
                description='UUID бренда или код 1С',
                required=True,
                type=str,
                location=OpenApiParameter.PATH
            )
        ],
        request=BrandListSerializer,
        responses={HTTP_200_OK: BrandListSerializer} | DEFAULT_SCHEMA_RESPONSES,
        examples=[
                     OpenApiExample(
                         "Поля для обновления бренда",
                         value={"name": "django drf test 2"},
                         request_only=True,
                     )
                 ] + DEFAULT_SCHEMA_EXAMPLES,
    ),
)
@extend_schema(tags=["Бренды"])
class BrandViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "id_or_code1c"
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Brand.objects.all().distinct()
    filter_backends = [DjangoFilterBackend]
    filterset_class = BrandFilter

    def get_serializer_class(self):
        if self.action == "create":
            return BrandCreateSerializer
        elif self.action == "retrieve":
            return BrandDetailSerializer
        return BrandListSerializer

    def create(self, request, *args, **kwargs):
        name = request.data.get("name")
        if Brand.all_objects.filter(name=name, is_deleted=False).exists():
            return Response(
                {"detail": f"Бренд с названием '{name}' уже существует"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        brand = serializer.save()

        try:
            response = api_1c.post("/CreateBrand", {
                "brandName": brand.name,
                "brandDescription": brand.description or '',
            })
            response.raise_for_status()
            code1c = response.json().get("brandCode")
            if code1c:
                if Brand.objects.filter(code1c=code1c).exclude(id=brand.id).exists():
                    logger.warning("code1c %s уже занят другим брендом", code1c)
                else:
                    brand.code1c = code1c
                    brand.save(update_fields=["code1c"])
        except Exception as e:
            logger.warning("Не удалось создать бренд в 1С: %s", e)

        short = BrandShortSerializer(brand)
        return Response(short.data, status=status.HTTP_201_CREATED)
    # def partial_update(self, request, *args, **kwargs):


    def destroy(self, request, *args, **kwargs):
        """Мягкое удаление бренда."""

        brand = self.get_object()
        brand.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self):
        identifier = self.kwargs.get(self.lookup_field)
        if not identifier:
            raise NotFound("Не указан идентификатор бренда.")

        # пробуем UUID
        try:
            uuid_obj = UUID(str(identifier))
            brand = Brand.all_objects.get(id=uuid_obj)
            if brand.is_deleted:
                raise NotFound("Бренд не найден.")
            return brand
        except (ValueError, Brand.DoesNotExist):
            pass

        # пробуем code1c
        try:
            brand = Brand.all_objects.get(code1c=identifier)
            if brand.is_deleted:
                raise NotFound("Бренд не найден.")
            return brand
        except Brand.DoesNotExist:
            pass

        # пробуем slug
        try:
            brand = Brand.all_objects.get(slug=identifier)
            if brand.is_deleted:
                raise NotFound("Бренд не найден.")
            return self._validate_brand_has_active_nomenclatures(brand)
        except Brand.DoesNotExist:
            raise NotFound("Бренд не найден.")

    def _validate_brand_has_active_nomenclatures(self, brand: Brand) -> Brand:
        has_active = brand.nomenclatures.filter(
            for_web=True,
            typeOfPlace__name="Торговый центр"
        ).exists()
        if not has_active:
            raise NotFound("Бренд не найден.")
        return brand

    @action(
        methods=["POST"],
        detail=True,
        url_path="unpin_logo",
    )
    def unpin_logo(self, request, pk=None, *args, **kwargs):
        """
        Открепить логотип от бренда. Логотип будет удален из системы, если не прикреплен ни к одному бренду.
        """
        identifier = self.kwargs.get(self.lookup_field)
        uuid_obj = UUID(str(identifier))
        brand = Brand.all_objects.get(id=uuid_obj)
        brand.logotype.delete(save=False)
        brand.logotype = None
        brand.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=["GET"],
        detail=False,
        url_path="assigned",
        url_name="assigned",
    )
    def assigned(self, request, *args, **kwargs):
        """Бренды, у которых есть хотя бы одна номенклатура."""
        queryset = Brand.objects.filter(
            nomenclatures__for_web=True,
            nomenclatures__typeOfPlace__name="Торговый центр",
        ).distinct()
        paginator = CustomLimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = BrandListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(
        methods=["GET"],
        detail=True,
        url_path="nomenclatures",
        url_name="nomenclatures",
    )
    def nomenclatures(self, request, *args, **kwargs):
        """Номенклатуры прикреплённые к бренду."""
        brand = self.get_object()
        queryset = brand.nomenclatures.filter(is_active=True, for_web=True)

        paginator = CustomLimitOffsetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = NomenclatureShortSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
