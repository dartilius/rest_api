from datetime import date

from django.test import override_settings

from placement_order.dates import current_business_date


@override_settings(USE_TZ=False)
def test_current_business_date_supports_naive_django_now():
    assert isinstance(current_business_date(), date)
