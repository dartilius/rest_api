from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from nomenclatures.filters import NomenclatureFilter
from nomenclatures.serializers import (
    NomenclatureSerializer,
    NomenclatureGroupSerializer,
    NomenclatureListSerializer
)
from nomenclatures.models import (
    Nomenclature,
    NomenclatureGroup
)
from users.models import User
from users.permissions import AuthAndOnlySuperUserDelete


class NomenclatureViewSet(viewsets.ModelViewSet):
    """Работа с номенклатурами."""

    queryset = Nomenclature.objects.filter(
        is_active=True
    ).select_related('owner', 'availability').order_by('name')
    filter_backends = (DjangoFilterBackend,)
    filterset_class = NomenclatureFilter
    # permission_classes = [AuthAndOnlySuperUserDelete, ]

    def get_serializer(self, *args, **kwargs):
        if self.action == 'list':
            serializer = NomenclatureListSerializer
        else:
            serializer = NomenclatureSerializer
        if 'data' in kwargs:
            data = kwargs['data']

            if isinstance(data, list):
                kwargs['many'] = True

        return serializer(*args, **kwargs)

    def perform_create(self, serializer):
        nomenclature = serializer.save(owner=self.request.user)
        group = NomenclatureGroup.objects.create(
            owner=self.request.user,
            name=nomenclature.name,
        )
        group.clients.add(nomenclature)
        group.save()

    def perform_update(self, serializer):
        nomenclature = serializer.instance
        new_name = serializer.validated_data['name']
        group = NomenclatureGroup.objects.exclude(~Q(clients=nomenclature.id)).first()
        group.name = new_name
        group.save()
        serializer.save()


class NomenclatureGroupViewSet(viewsets.ModelViewSet):
    """Работа с группами номенклатур."""

    serializer_class = NomenclatureGroupSerializer
    queryset = NomenclatureGroup.objects.all().prefetch_related(
        'clients',
    ).select_related('owner').order_by('name')
