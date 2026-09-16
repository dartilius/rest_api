from django.utils import timezone


def current_business_date():
    """Return today's configured business date with or without timezone support."""
    now = timezone.now()
    if timezone.is_naive(now):
        return now.date()
    return timezone.localdate(now)
