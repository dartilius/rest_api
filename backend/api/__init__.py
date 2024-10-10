from django.db import models
from api.custom_models import UUIDPKField, APIBaseModel

models.fields.UUIDPKField = UUIDPKField
models.base.APIBaseModel = APIBaseModel
