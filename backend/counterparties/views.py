from drf_spectacular.utils import extend_schema_view, extend_schema
from rest_framework import viewsets
from uuid import UUID

from rest_framework.exceptions import NotFound
from counterparties.models import Counterparty
from counterparties.serializers import CounterpartiesSerializer, CounterpartiesListSerializer, \
    CreateCounterpartySerializer


# @extend_schema_view(
#     list=extend_schema(
#         summary="Пагинированный список Контрагентов",
#         description="",
#         parameters=[],
#         responses={},
#         examples=[],
#     )
# )
class CounterpartiesViewSet(viewsets.ModelViewSet):
    queryset = Counterparty.objects.all()
    lookup_field = "id_or_code1c"
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateCounterpartySerializer
        elif self.action == 'list':
            return CounterpartiesListSerializer
        else:
            return CounterpartiesSerializer

    def get_object(self):
        identifier = self.kwargs.get(self.lookup_field)
        if not identifier:
            raise NotFound("Не указан идентификатор КА.")

        # пробуем UUID
        try:
            uuid_obj = UUID(str(identifier))
            counterparty = Counterparty.active.get(id=uuid_obj)
            if counterparty.is_deleted:
                raise NotFound("КА не найден.")
            return counterparty
        except (ValueError, Counterparty.DoesNotExist):
            pass

        # пробуем code1c
        try:
            counterparty = Counterparty.active.get(code1c=identifier)
            if counterparty.is_deleted:
                raise NotFound("КА не найден.")
            return counterparty
        except Counterparty.DoesNotExist:
            raise NotFound("КА не найден.")

# class CounterpartiesViewSet(viewsets.ModelViewSet):
#     permission_classes = [IsAuthenticatedOrReadOnly]
#     http_method_names = ["get", "post", "patch", "delete"]
#     queryset = Counterparty.active.all()
#     lookup_field = "id_or_code1c"
#
#     def get_queryset(self):
#         user = self.request.user
#
#         if not user.is_authenticated:
#             return Counterparty.objects.none()
#
#         is_broadcast = user.is_contact_person_broadcast
#         is_ad = user.is_contact_person_ad
#         is_admin = (
#                 user.is_admin
#                 or user.is_superuser
#                 or user.is_ordinary
#                 or user.is_manager
#         )
#
#         qs = Counterparty.objects.all().order_by('id')
#
#         if is_broadcast or is_ad:
#             user_counterparties = Counterparty.objects.filter(contact_persons=user)
#
#             qs = qs.filter(
#                 Q(id__in=user_counterparties.values_list('id', flat=True))
#             ).distinct()
#
#         elif is_admin:
#             pass  # админы видят всех
#
#         else:
#             qs = Counterparty.objects.none()
#
#         return qs
#
#     def get_serializer_class(self):
#         if self.action == "create":
#             return CounterpartiesCreateSerializer
#         return CounterpartiesSerializer
#
#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         counterparties = serializer.save()
#         short = CounterpartiesShortSerializer(counterparties)
#         return Response(short.data, status=HTTP_201_CREATED)
#
#     def destroy(self, request, *args, **kwargs):
#
#         counterparties = self.get_object()
#         counterparties.delete()
#         return Response(status=HTTP_204_NO_CONTENT)
#
#     def get_object(self):
#
#         identifier = self.kwargs.get(self.lookup_field)
#         if not identifier:
#             raise NotFound("Не указан идентификатор контрагента.")
#
#         # пробуем UUID
#         try:
#             uuid_obj = UUID(str(identifier))
#             counterparty = Counterparty.objects.get(id=uuid_obj)
#             if not counterparty.is_active:
#                 raise NotFound("Контрагент не найден.")
#             return counterparty
#         except (ValueError, Counterparty.DoesNotExist):
#             pass
#
#         # пробуем code1c
#         try:
#             counterparty = Counterparty.objects.get(code1c=identifier)
#             if not counterparty.is_active:
#                 raise NotFound("Контрагент не найден.")
#             return counterparty
#         except Counterparty.DoesNotExist:
#             raise NotFound("Контрагент не найден.")
#
#     @action(detail=True, methods=["delete"], url_path="cp/remove/(?P<user_id>[^/.]+)")
#     def remove_contact_person(self, request, id_or_code1c=None, user_id=None):
#         counterparty = self.get_object()
#
#         try:
#             user = CustomUser.objects.get(id=user_id)
#         except CustomUser.DoesNotExist:
#             return Response({"detail": "User not found"}, status=404)
#
#         counterparty.contact_persons.remove(user)
#         return Response({"detail": "removed"}, status=200)
