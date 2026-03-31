from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets
from uuid import UUID

from rest_framework.filters import SearchFilter
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
    filter_backends = [DjangoFilterBackend, SearchFilter]
    pagination_class = CustomLimitOffsetPagination
    search_fields = [
        "tenant__first_name",
        "tenant__middle_name",
        "tenant__last_name",
        "tenant__keyword",
        "tenant__additional_name",
        "tenant__brands__name",
        "brand__name",
    ]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return TenantWriteSerializer
        return NomenclatureTenantResponseSerializer

    @staticmethod
    def _resolve_filter(value, id_field, code1c_field):
        try:
            UUID(hex=value)
            return id_field
        except (ValueError, AttributeError, TypeError):
            return code1c_field

    def get_queryset(self):
        nomenclature_pk = self.kwargs.get('nomenclature_pk')
        filter_field = self._resolve_filter(
            nomenclature_pk,
            "nomenclature__id",
            "nomenclature__code1c"
        )
        qs = (
            NomenclatureTenant.objects
            .filter(**{filter_field: nomenclature_pk})
            .select_related("tenant", "brand")
        )
        print("QS count before search:", qs.count())
        print("Search param:", self.request.query_params.get('search'))
        return qs

    def get_object(self):
        nomenclature_pk = self.kwargs.get('nomenclature_pk')
        tenant_pk = self.kwargs.get('pk')

        nomenclature_filter = self._resolve_filter(
            nomenclature_pk,
            "nomenclature__id",
            "nomenclature__code1c"
        )
        tenant_filter = self._resolve_filter(
            tenant_pk,
            "tenant__id",
            "tenant__code1c"
        )
        print("kwarg:", self.kwargs)
        print("nomenclature_filter:", nomenclature_filter, "=", nomenclature_pk)
        print("tenant_filter:", tenant_filter, "=", tenant_pk)
        print("query:", NomenclatureTenant.objects.filter(
            **{nomenclature_filter: nomenclature_pk, tenant_filter: tenant_pk}
        ).query)

        obj = get_object_or_404(
            NomenclatureTenant,
            **{nomenclature_filter: nomenclature_pk, tenant_filter: tenant_pk}
        )
        self.check_object_permissions(self.request, obj)
        return obj