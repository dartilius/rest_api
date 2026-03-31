from django.urls import path, include
from rest_framework_nested import routers
from nomenclatures.views import (
    NomenclatureViewSet, NomenclatureOrderViewSet, NomenclatureStatisticViewSet,
    NomenclatureTaskViewSet, NomenclaturePhotoViewSet, TypeOfPlaceViewSet, NomenclatureTenantViewSet
)

router = routers.DefaultRouter()
router.register('nomenclatures', NomenclatureViewSet, basename='nomenclature')
router.register('orders', NomenclatureOrderViewSet, basename='order')
router.register('statistics', NomenclatureStatisticViewSet, basename='statistic')
router.register('tasks', NomenclatureTaskViewSet, basename='task')
router.register('photos', NomenclaturePhotoViewSet, basename='photo')
router.register('place', TypeOfPlaceViewSet, basename='place')

nomenclature_router = routers.NestedDefaultRouter(router, 'nomenclatures', lookup='nomenclature')
nomenclature_router.register('tenant', NomenclatureTenantViewSet, basename='nomenclature-tenant')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(nomenclature_router.urls)),
]