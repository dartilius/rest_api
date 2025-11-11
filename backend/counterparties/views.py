from uuid import UUID

from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from counterparties.models import Counterparties
from counterparties.serializers import CounterpartiesShortSerializer, CounterpartiesCreateSerializer, \
    CounterpartiesSerializer


# Create your views here.
class CounterpartiesViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Counterparties.active.all()

    def get_serializer_class(self):
        if self.action == "create":
            return CounterpartiesCreateSerializer
        return CounterpartiesSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        counterparties = serializer.save()
        short = CounterpartiesShortSerializer(counterparties)
        return Response(short.data, status=HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):

        counterparties = self.get_object()
        counterparties.delete()
        return Response(status=HTTP_204_NO_CONTENT)

    def get_object(self):

        identifier = self.kwargs.get(self.lookup_field)
        if not identifier:
            raise NotFound("Не указан идентификатор контрагента.")

        # пробуем UUID
        try:
            uuid_obj = UUID(str(identifier))
            counterparty = Counterparties.objects.get(id=uuid_obj)
            if not counterparty.is_active:
                raise NotFound("Контрагент не найден.")
            return counterparty
        except (ValueError, Counterparties.DoesNotExist):
            pass

        # пробуем code1c
        try:
            counterparty = Counterparties.objects.get(code1c=identifier)
            if not counterparty.is_active:
                raise NotFound("Контрагент не найден.")
            return counterparty
        except Counterparties.DoesNotExist:
            raise NotFound("Контрагент не найден.")
