from rest_framework import viewsets
from uuid import UUID
from api.pagination import CustomLimitOffsetPagination
from nomenclatures.models import NomenclatureTenant
from nomenclatures.serializers import TenantWriteSerializer, NomenclatureTenantResponseSerializer
from users.permissions import SuperuserCUDAuthRetrieve


class NomenclatureTenantViewSet(viewsets.ModelViewSet):
    """
    Кастомный viewset для работы с арендаторами места.
    Доступные действия:
        - List: получить список арендаторов по pk/code1c номенклатуры
          (просмотреть может каждый пользователь)
        - Create: добавить арендатора к номенклатуре (is_super_user)
        - Update: обновить данные (is_super_user)
        - Delete: удалить арендатора из ноиенклатуры (is_super_user)
    """

    queryset = NomenclatureTenant.objects.all()
    permission_classes = [SuperuserCUDAuthRetrieve]
    pagination_class = CustomLimitOffsetPagination
    lookup_field = "id_or_code1c"

    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия."""
        if self.action in ["create", "update", "partial_update"]:
            return TenantWriteSerializer
        return NomenclatureTenantResponseSerializer
    def get_queryset(self):
        if self.action != "list":
            return super().get_queryset()

        id_or_code1c = self.kwargs.get('id_or_code1c')

        try:
            UUID(id_or_code1c)
            filter_field = "nomenclature__id"
        except (ValueError, AttributeError):
            filter_field = "nomenclature__code1c"

        return (
            NomenclatureTenant.objects.filter(
                **{filter_field: id_or_code1c}
            ).select_related("tenant", "brand")
        )

