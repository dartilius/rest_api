from django.urls import path, include
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers
from nomenclatures.views import (
    NomenclatureViewSet, NomenclatureOrderViewSet, NomenclatureStatisticViewSet,
    NomenclatureTaskViewSet, NomenclaturePhotoViewSet, NomenclatureVideoViewSet, TypeOfPlaceViewSet, NomenclatureTenantViewSet,
    NomenclatureWebViewSet, Nomenclature1CViewSet
)
from nomenclatures.views.discount import DiscountRuleViewSet  # добавить
from nomenclatures.views.tenant import grouped_tenants_global, tenant_detail
from nomenclatures.views.station_v2 import StationV2SyncView
from nomenclatures.views.station_binding import StationV2BindingView
from addresses.views_1c import Address1CViewSet
from brands.views_1c import Brand1CViewSet
from counterparties.views_1c import Counterparty1CViewSet
from nomenclatures.views.components_1c import (
    DiscountRule1CViewSet,
    NomenclatureMedia1CViewSet,
    NomenclatureTenant1CViewSet,
    TypeOfPlace1CViewSet,
)
router = routers.DefaultRouter()
router.register('nomenclatures', NomenclatureViewSet, basename='nomenclature')
router.register('orders', NomenclatureOrderViewSet, basename='order')
router.register('statistics', NomenclatureStatisticViewSet, basename='statistic')
router.register('tasks', NomenclatureTaskViewSet, basename='task')
router.register('photos', NomenclaturePhotoViewSet, basename='photo')
router.register('videos', NomenclatureVideoViewSet, basename='video')
router.register('place', TypeOfPlaceViewSet, basename='place')
web_router = SimpleRouter()
web_router.register('', NomenclatureWebViewSet, basename='web')
one_c_router = SimpleRouter()
one_c_router.register('nomenclatures', Nomenclature1CViewSet, basename='1c-nomenclature')
one_c_router.register('brands', Brand1CViewSet, basename='1c-brand')
one_c_router.register('counterparties', Counterparty1CViewSet, basename='1c-counterparty')
one_c_router.register('addresses', Address1CViewSet, basename='1c-address')
one_c_router.register('places', TypeOfPlace1CViewSet, basename='1c-place')
one_c_nomenclature_router = routers.NestedSimpleRouter(
    one_c_router, 'nomenclatures', lookup='nomenclature'
)
one_c_nomenclature_router.register('tenants', NomenclatureTenant1CViewSet, basename='1c-nomenclature-tenant')
one_c_nomenclature_router.register('discounts', DiscountRule1CViewSet, basename='1c-nomenclature-discount')
one_c_nomenclature_router.register('media', NomenclatureMedia1CViewSet, basename='1c-nomenclature-media')

nomenclature_router = routers.NestedDefaultRouter(router, 'nomenclatures', lookup='nomenclature')
nomenclature_router.register('tenant', NomenclatureTenantViewSet, basename='nomenclature-tenant')
nomenclature_router.register('discounts', DiscountRuleViewSet, basename='nomenclature-discounts')  # добавить

urlpatterns = [
    path('station/v2/bind/', StationV2BindingView.as_view(), name='station-v2-bind'),
    path('station/v2/sync/', StationV2SyncView.as_view(), name='station-v2-sync'),
    path('1c/', include(one_c_router.urls)),
    path('1c/', include(one_c_nomenclature_router.urls)),
    path('', include(router.urls)),
    path('nomenclatures/web/', include(web_router.urls)),
    path('tenants/grouped/', grouped_tenants_global, name='grouped-tenants-global'),
    path('tenants/<str:tenant_pk>/', tenant_detail, name='tenant-detail'),
    path('', include(nomenclature_router.urls)),
]
