# from django.urls import include, path
# from rest_framework.routers import SimpleRouter

# from nomenclatures.views import (
#     NomenclatureViewSet, NomenclaturePhotoViewSet,
#     NomenclatureStatisticViewSet, NomenclatureTaskViewSet
#     )

# router = SimpleRouter()

# router.register("nomenclatures", NomenclatureViewSet, basename="nomenclatures")
# router.register('photos', NomenclaturePhotoViewSet, basename='photo')
# router.register('statistics', NomenclatureStatisticViewSet, basename='statistic')
# router.register('tasks', NomenclatureTaskViewSet, basename='task')

# urlpatterns = [path("", include(router.urls))]


from django.urls import path, include
from rest_framework.routers import DefaultRouter

from nomenclatures.views import NomenclatureViewSet, NomenclatureOrderViewSet, NomenclatureStatisticViewSet, \
    NomenclatureTaskViewSet, NomenclaturePhotoViewSet, TypeOfPlaceViewSet, MediaStorageViewSet

router = DefaultRouter()
router.register('nomenclatures', NomenclatureViewSet, basename='nomenclature')
router.register('orders', NomenclatureOrderViewSet, basename='order')
router.register('statistics', NomenclatureStatisticViewSet, basename='statistic')
router.register('tasks', NomenclatureTaskViewSet, basename='task')
router.register('photos', NomenclaturePhotoViewSet, basename='photo')
router.register('place', TypeOfPlaceViewSet, basename='place')
router.register('media_storage', MediaStorageViewSet, basename='media_storage')

urlpatterns = [
    path('', include(router.urls)),
]

