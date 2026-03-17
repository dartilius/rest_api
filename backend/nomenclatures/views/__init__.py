from .nomenclature import NomenclatureViewSet
from .order import NomenclatureOrderViewSet
from .place import TypeOfPlaceViewSet
from .statistic import NomenclatureStatisticViewSet
from .task import NomenclatureTaskViewSet
from .photo import NomenclaturePhotoViewSet

__all__ = [
    'NomenclatureViewSet',
    'NomenclatureOrderViewSet',
    'NomenclatureStatisticViewSet',
    'NomenclatureTaskViewSet',
    'NomenclaturePhotoViewSet',
    'TypeOfPlaceViewSet'
]