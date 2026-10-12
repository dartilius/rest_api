from datetime import datetime

import pytest
from rest_framework.exceptions import ValidationError

from nomenclatures.views.statistic import NomenclatureStatisticViewSet


@pytest.mark.parametrize(
    ("value", "expected_start", "expected_end"),
    [
        ("2026-09-02", datetime(2026, 9, 1, 17), datetime(2026, 9, 2, 17)),
        ("2026-09", datetime(2026, 8, 31, 17), datetime(2026, 9, 30, 17)),
        ("2026", datetime(2025, 12, 31, 17), datetime(2026, 12, 31, 17)),
    ],
)
def test_statistic_date_range_preserves_krasnoyarsk_calendar_day(
    value, expected_start, expected_end
):
    assert NomenclatureStatisticViewSet._date_range_to_utc(value) == (
        expected_start,
        expected_end,
    )


@pytest.mark.parametrize("value", ["2026-9", "02-09-2026", "2026-02-30", "today"])
def test_statistic_date_range_rejects_ambiguous_values(value):
    with pytest.raises(ValidationError):
        NomenclatureStatisticViewSet._date_range_to_utc(value)
