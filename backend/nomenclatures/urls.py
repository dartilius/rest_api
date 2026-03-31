from django.urls import path, include
from rest_framework.routers import DefaultRouter

from nomenclatures.views import NomenclatureViewSet, NomenclatureOrderViewSet, NomenclatureStatisticViewSet, \
    NomenclatureTaskViewSet, NomenclaturePhotoViewSet, TypeOfPlaceViewSet, NomenclatureTenantViewSet

router = DefaultRouter()
router.register('nomenclatures', NomenclatureViewSet, basename='nomenclature')
router.register('orders', NomenclatureOrderViewSet, basename='order')
router.register('statistics', NomenclatureStatisticViewSet, basename='statistic')
router.register('tasks', NomenclatureTaskViewSet, basename='task')
router.register('photos', NomenclaturePhotoViewSet, basename='photo')
router.register('place', TypeOfPlaceViewSet, basename='place')
router.register('tenant', NomenclatureTenantViewSet, basename='tenant')

urlpatterns = [
    path('', include(router.urls)),
]

