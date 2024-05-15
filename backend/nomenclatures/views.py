from django.db.models import Count
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from nomenclatures.filters import NomenclatureFilter
from nomenclatures.serializers import (
    NomenclatureSerializer,
    HardWareInfoSerializer,
    SettingsSerializer,
    NomenclatureGroupSerializer,
    NomenclatureListSerializer
)
from nomenclatures.models import (
    Nomenclature,
    HardWareInfo,
    NomenclatureGroup
)
from users.models import User
from users.permissions import AuthAndOnlySuperUserDelete


class NomenclatureViewSet(viewsets.ModelViewSet):
    """Работа с номенклатурами."""

    queryset = Nomenclature.objects.filter(
        is_active=True
    ).select_related('owner').prefetch_related(
        'settings'
    ).order_by('name')
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
        nomenclature = serializer.save(owner=User.objects.get(pk=1))  # owner=self.request.user
        group = NomenclatureGroup.objects.create(
            owner=self.request.user,
            name=nomenclature.name,
            description=nomenclature.name
        )
        group.clients.add(nomenclature)
        group.save()

    def perform_update(self, serializer):
        nomenclature = serializer.instance
        old_name = nomenclature.name
        new_name = serializer.validated_data['name']
        group = NomenclatureGroup.objects.get(name=old_name)
        group.name = new_name
        group.save()


class HardWareInfoViewSet(viewsets.ModelViewSet):
    """Работа с информацией о железе разбы."""

    serializer_class = HardWareInfoSerializer

    def get_queryset(self):
        nomenclature_id = self.kwargs.get('nomenclature_id')
        return HardWareInfo.objects.filter(
            client__id=nomenclature_id
        ).select_related(
            'client', 'client__owner'
        ).prefetch_related('client__settings')


class SettingsViewSet(viewsets.ModelViewSet):
    """Работа с настройками номенклатуры."""

    serializer_class = SettingsSerializer

    def get_queryset(self):
        nomenclature_id = self.kwargs.get('nomenclature_id')
        return get_object_or_404(
            Nomenclature.objects,
            id=nomenclature_id
        ).settings


class NomenclatureGroupViewSet(viewsets.ModelViewSet):
    """Работа с группами номенклатур."""

    serializer_class = NomenclatureGroupSerializer
    queryset = NomenclatureGroup.objects.all().prefetch_related(
        'clients', 'clients__settings'
    ).select_related('owner').order_by('name')
