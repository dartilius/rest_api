from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from uuid import UUID

from rest_framework.permissions import AllowAny

from api.pagination import CustomLimitOffsetPagination
from nomenclatures.models import NomenclatureTenant
from nomenclatures.serializers import TenantWriteSerializer, NomenclatureTenantResponseSerializer

@extend_schema(tags=["Номенклатура - Арендаторы"])
class NomenclatureTenantViewSet(viewsets.ModelViewSet):
    """
    Кастомный viewset для работы с арендаторами места.
    Доступные действия:
        - List: получить список арендаторов по pk/code1c номенклатуры
          (просмотреть может каждый пользователь)
        - Create: добавить арендатора к номенклатуре (is_super_user)
        - Update: обновить данные (is_super_user)
        - Delete: удалить арендатора из ноиенклатуры (is_super_user)

    Урлы:
    GET    /api/nomenclatures/{id_or_code1c}/tenant/        # list
    POST   /api/nomenclatures/{id_or_code1c}/tenant/        # create
    GET    /api/nomenclatures/{id_or_code1c}/tenant/{id}/   # retrieve
    PATCH  /api/nomenclatures/{id_or_code1c}/tenant/{id}/   # partial_update
    DELETE /api/nomenclatures/{id_or_code1c}/tenant/{id}/   # destroy
    """

    queryset = NomenclatureTenant.objects.all()
    http_method_names = ["get", "post", "patch", "delete"]
    permission_classes = [AllowAny]
    pagination_class = CustomLimitOffsetPagination
    lookup_field = "id_or_code1c"

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TenantWriteSerializer
        return NomenclatureTenantResponseSerializer

    def get_queryset(self):
        id_or_code1c = self.kwargs.get('nomenclature_pk')

        try:
            UUID(id_or_code1c)
            filter_field = "nomenclature__id"
        except (ValueError, AttributeError):
            filter_field = "nomenclature__code1c"

        return (
            NomenclatureTenant.objects
            .filter(**{filter_field: id_or_code1c})
            .select_related("tenant", "brand")
        )

    def get_object(self):
        obj = get_object_or_404(NomenclatureTenant, id=self.kwargs.get('id'))
        self.check_object_permissions(self.request, obj)
        return obj

