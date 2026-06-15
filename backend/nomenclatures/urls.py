from django.urls import path, include
from rest_framework_nested import routers
from nomenclatures.views import (
    NomenclatureViewSet, NomenclatureOrderViewSet, NomenclatureStatisticViewSet,
    NomenclatureTaskViewSet, NomenclaturePhotoViewSet, TypeOfPlaceViewSet, NomenclatureTenantViewSet,
    NomenclatureWebViewSet
)
from nomenclatures.views.discount import DiscountRuleViewSet  # добавить
from nomenclatures.views.tenant import grouped_tenants_global, tenant_detail
router = routers.DefaultRouter()
router.register('nomenclatures', NomenclatureViewSet, basename='nomenclature')
router.register('orders', NomenclatureOrderViewSet, basename='order')
router.register('statistics', NomenclatureStatisticViewSet, basename='statistic')
router.register('tasks', NomenclatureTaskViewSet, basename='task')
router.register('photos', NomenclaturePhotoViewSet, basename='photo')
router.register('place', TypeOfPlaceViewSet, basename='place')
router.register('web', NomenclatureWebViewSet, basename='web')

nomenclature_router = routers.NestedDefaultRouter(router, 'nomenclatures', lookup='nomenclature')
nomenclature_router.register('tenant', NomenclatureTenantViewSet, basename='nomenclature-tenant')
nomenclature_router.register('discounts', DiscountRuleViewSet, basename='nomenclature-discounts')  # добавить

urlpatterns = [
    path('', include(router.urls)),
    path('tenants/grouped/', grouped_tenants_global, name='grouped-tenants-global'),
    path('tenants/<str:tenant_pk>/', tenant_detail, name='tenant-detail'),
    path('', include(nomenclature_router.urls)),
]