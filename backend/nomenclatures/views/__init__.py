from .nomenclature import NomenclatureViewSet
from .order import NomenclatureOrderViewSet
from .place import TypeOfPlaceViewSet
# from .statistic import NomenclatureStatisticViewSet  ← УДАЛИТЬ (старое)

# ← ИМПОРТИРУЕМ ТО, ЧТО НУЖНО (новые классы)
from ch_statistic.views import (
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
    
    # ← ДОБАВИТЬ новые
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
# ]