"""Run with the offline test_settings and unittest, using only an in-memory DB."""
import unittest
from unittest.mock import patch
from uuid import uuid4

from django.apps import apps
from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.storage.fallback import FallbackStorage
from django.db import connection
from django_minio_backend import MinioBackend
from rest_framework.test import APIRequestFactory

from brands.models import Brand
from nomenclatures.models import TypeOfPlace
from corporate_broadcast.models import BroadcastDemo, BroadcastLanding, TypesOfPlaceBroadcast
from corporate_broadcast.views import BroadcastLandingViewSet


class LandingAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.factory = APIRequestFactory()
        # Only the relevant tables are needed, no PostgreSQL/ClickHouse migrations.
        user_table = apps.get_model("users", "CustomUser")._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f'CREATE TABLE {connection.ops.quote_name(user_table)} (id char(32) PRIMARY KEY)')
        with connection.schema_editor() as editor:
            editor.create_model(ContentType)
            editor.create_model(admin.models.LogEntry)
            for model in (Brand, TypeOfPlace, BroadcastDemo, TypesOfPlaceBroadcast, BroadcastLanding):
                editor.create_model(model)

    def setUp(self):
        BroadcastLanding.objects.all().delete()

    def list(self):
        request = self.factory.get("/api/broadcast-landings/", HTTP_AUTHORIZATION="Bearer expired")
        return BroadcastLandingViewSet.as_view({"get": "list"})(request)

    def test_public_blocks_include_only_selected_visible_brands_and_no_signed_urls(self):
        landing = BroadcastLanding.objects.create(title="Блок", description="Описание")
        brand = Brand.objects.create(name="Выбранный", logotype="brand_logo/test.png")
        hidden = Brand.objects.create(name="Удалённый", logotype="brand_logo/hidden.png", is_deleted=True)
        empty = Brand.objects.create(name="Без логотипа")
        landing.logo_brands.add(brand, hidden, empty)
        with patch.object(MinioBackend, "url", side_effect=AssertionError("No signing in cached JSON")):
            response = self.list()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Блок")
        self.assertEqual(response.data[0]["logo_brands"], [{
            "id": str(brand.pk), "name": "Выбранный",
            "logotype": f"http://testserver/api/broadcast-landings/{landing.pk}/brands/{brand.pk}/logo/",
        }])
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_optional_links_and_inactive_format_and_unpublished_demo(self):
        demo = BroadcastDemo.objects.create(title="Черновик", format="audio")
        format_type = TypesOfPlaceBroadcast.objects.create(name="Формат", title="Аудио", format_type="audio", is_active=False)
        BroadcastLanding.objects.create(title="Блок", demo=demo, format_type=format_type)
        data = self.list().data[0]
        self.assertIsNone(data["demo"])
        self.assertIsNone(data["format_type"])
        demo.is_published = True
        demo.save()
        format_type.is_active = True
        format_type.save()
        data = self.list().data[0]
        self.assertEqual(str(data["demo"]), str(demo.pk))
        self.assertEqual(data["format_type"]["format_label"], "Аудиовещание")

    def test_logo_redirect_is_fresh_and_does_not_expose_unselected_brands(self):
        landing = BroadcastLanding.objects.create(title="Блок")
        brand = Brand.objects.create(name="Логотип", logotype="brand_logo/logo.png")
        view = BroadcastLandingViewSet.as_view({"get": "brand_logo"})
        request = self.factory.get("/logo/")
        response = view(request, pk=landing.pk, brand_id=str(brand.pk))
        self.assertEqual(response.status_code, 404)
        landing.logo_brands.add(brand)
        with patch.object(MinioBackend, "url", return_value="https://files.example.test/fresh-signature"):
            response = view(request, pk=landing.pk, brand_id=str(brand.pk))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "https://files.example.test/fresh-signature")
        self.assertEqual(response["Cache-Control"], "no-store")

    def test_empty_list_and_write_methods(self):
        self.assertEqual(self.list().data, [])
        response = BroadcastLandingViewSet.as_view({"get": "list"})(self.factory.post("/api/broadcast-landings/", {"title": "Не создавать"}))
        self.assertEqual(response.status_code, 405)

    def admin_request(self, path, data):
        user = apps.get_model("users", "CustomUser")(
            pk=uuid4(), is_active=True, is_staff=True, is_superuser=True,
        )
        with connection.cursor() as cursor:
            cursor.execute(
                f'INSERT INTO {connection.ops.quote_name(user._meta.db_table)} (id) VALUES (%s)',
                [user.pk.hex],
            )
        request = self.factory.post(path, data)
        request.user = user
        request.session = {}
        request._messages = FallbackStorage(request)
        request._dont_enforce_csrf_checks = True
        return request

    def test_popup_creates_format_then_main_editor_saves_and_updates_block(self):
        format_admin = admin.site.get_model_admin(TypesOfPlaceBroadcast)
        request = self.admin_request("/admin/corporate_broadcast/typesofplacebroadcast/add/", {
            "title": "Новый формат менеджера", "format_type": "audio",
            "description": "Описание", "is_active": "on", "_popup": "1",
        })
        response = format_admin.add_view(request)
        self.assertEqual(response.status_code, 200)
        format_type = TypesOfPlaceBroadcast.objects.get(title="Новый формат менеджера")
        self.assertEqual(format_type.name, format_type.title)
        self.assertEqual(format_type.owner_id, request.user.pk)
        response.render()
        self.assertIn(b'popup_response', response.content)

        brand = Brand.objects.create(name="Бренд редактора")
        landing_admin = admin.site.get_model_admin(BroadcastLanding)
        payload = {
            "title": "Новый блок", "description": "Текст", "format_type": str(format_type.pk),
            "logo_brands": [str(brand.pk)], "_continue": "1",
        }
        response = landing_admin.add_view(self.admin_request("/admin/corporate_broadcast/broadcastlanding/add/", payload))
        self.assertEqual(response.status_code, 302)
        landing = BroadcastLanding.objects.get(title="Новый блок")
        self.assertEqual(landing.format_type_id, format_type.pk)
        self.assertEqual(list(landing.logo_brands.values_list("pk", flat=True)), [brand.pk])
        payload["title"] = "Изменённый блок"
        response = landing_admin.change_view(
            self.admin_request(f"/admin/corporate_broadcast/broadcastlanding/{landing.pk}/change/", payload),
            str(landing.pk),
        )
        self.assertEqual(response.status_code, 302)
        landing.refresh_from_db()
        self.assertEqual(landing.title, "Изменённый блок")
