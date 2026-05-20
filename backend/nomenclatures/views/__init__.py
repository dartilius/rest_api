from .nomenclature import NomenclatureViewSet
from .order import NomenclatureOrderViewSet
from .place import TypeOfPlaceViewSet
# from .statistic import NomenclatureStatisticViewSet  ← УДАЛИТЬ (агрегатор)

# ← ИМПОРТИРОВАТЬ КОНКРЕТНЫЕ VIEWSET
from .statistic import (
    ADStatisticViewSet,
    MusicStatisticViewSet,
    VideoStatisticViewSet,
    ImageStatisticViewSet,
    TickerStatisticViewSet,
    NomenclatureHistoryViewSet,
)

from .task import NomenclatureTaskViewSet
from .photo import NomenclaturePhotoViewSet
from .tenant import NomenclatureTenantViewSet

__all__ = [
    'NomenclatureViewSet',
    'NomenclatureOrderViewSet',
    # 'NomenclatureStatisticViewSet',  ← УДАЛИТЬ
    'ADStatisticViewSet',
    'MusicStatisticViewSet',
    'VideoStatisticViewSet',
    'ImageStatisticViewSet',
    'TickerStatisticViewSet',
    'NomenclatureHistoryViewSet',
    'NomenclatureTaskViewSet',
    'NomenclaturePhotoViewSet',
    'TypeOfPlaceViewSet',
    'NomenclatureTenantViewSet'
]

# from .nomenclature import NomenclatureViewSet
# from .order import NomenclatureOrderViewSet
# from .place import TypeOfPlaceViewSet
# from .statistic import NomenclatureStatisticViewSet
# from .task import NomenclatureTaskViewSet
# from .photo import NomenclaturePhotoViewSet
# from .tenant import NomenclatureTenantViewSet

# __all__ = [
#     'NomenclatureViewSet',
#     'NomenclatureOrderViewSet',
#     'NomenclatureStatisticViewSet',
#     'NomenclatureTaskViewSet',
#     'NomenclaturePhotoViewSet',
#     'TypeOfPlaceViewSet',
#     'NomenclatureTenantViewSet'
]