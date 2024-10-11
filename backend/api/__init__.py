from django.db.models import base, fields

from api.base_objects import APIBaseObjectModel, UUIDPKField

fields.UUIDPKField = UUIDPKField
base.APIBaseModel = APIBaseObjectModel
