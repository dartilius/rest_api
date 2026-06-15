from .nomenclature import NomenclatureViewSet
from .order import NomenclatureOrderViewSet
from .place import TypeOfPlaceViewSet
from .statistic import NomenclatureStatisticViewSet
from .task import NomenclatureTaskViewSet
from .photo import NomenclaturePhotoViewSet
from .tenant import NomenclatureTenantViewSet
from .discount import DiscountRuleViewSet
from .nomenclature_web import NomenclatureWebViewSet

__all__ = [
    'NomenclatureViewSet',
    'NomenclatureOrderViewSet',
    'NomenclatureStatisticViewSet',
    'NomenclatureTaskViewSet',
    'NomenclaturePhotoViewSet',
    'TypeOfPlaceViewSet',
    'NomenclatureTenantViewSet',
    'DiscountRuleViewSet',
    'NomenclatureWebViewSet'
]