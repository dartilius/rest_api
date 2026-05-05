from django.db.models import base, fields

from api.base_objects import APIBaseObjectModel, Article, UUIDPKField, ContactInformation
from api.mixins import APIServiceMixin

fields.UUIDPKField = UUIDPKField
fields.Article = Article
base.APIBaseModel = APIBaseObjectModel
base.ContactInformation = ContactInformation
base.APIServiceMixin = APIServiceMixin