from .nomenclature import NomenclatureViewSet
from .order import NomenclatureOrderViewSet
from .place import TypeOfPlaceViewSet
from .statistic import NomenclatureStatisticViewSet
from .task import NomenclatureTaskViewSet
from .photo import NomenclaturePhotoViewSet
from .video import NomenclatureVideoViewSet
from .tenant import NomenclatureTenantViewSet
from .discount import DiscountRuleViewSet
from .nomenclature_web import NomenclatureWebViewSet

__all__ = [
    'NomenclatureViewSet',
    'NomenclatureOrderViewSet',
    'NomenclatureStatisticViewSet',
    'NomenclatureTaskViewSet',
    'NomenclaturePhotoViewSet',
    'NomenclatureVideoViewSet',
    'TypeOfPlaceViewSet',
    'NomenclatureTenantViewSet',
    'DiscountRuleViewSet',
    'NomenclatureWebViewSet'
]
