from django.contrib.postgres.forms import BaseRangeField
from django.db import models
from django import forms
from django.contrib.postgres.fields import RangeField
from psycopg2._range import Range
from django.utils.translation import gettext_lazy as _


class TimeRange(Range):
    """Диапазон времени."""
    pass


class TimeRangeFieldForm(BaseRangeField):
    """Форма для диапазона времени."""

    default_error_messages = {'invalid': _('Enter two valid times.')}
    base_field = forms.TimeField
    range_type = TimeRange


class TimeRangeField(RangeField):
    """Поле диапазона времени."""

    base_field = models.TimeField
    range_type = TimeRange
    form_field = TimeRangeFieldForm

    def db_type(self, connection):
        return 'timerange'
