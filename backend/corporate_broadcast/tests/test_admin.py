import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from django.contrib import admin
from django.test import RequestFactory

from corporate_broadcast.admin import BroadcastLandingAdmin
from corporate_broadcast.models import BroadcastDemo, BroadcastLanding, TypesOfPlaceBroadcast


class LandingAdminTests(unittest.TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/admin/corporate_broadcast/broadcastlanding/add/")
        self.request.user = SimpleNamespace(
            is_active=True, is_staff=True, is_superuser=True,
            has_perm=lambda permission: True,
        )
        self.model_admin = admin.site.get_model_admin(BroadcastLanding)

    def test_related_fields_support_creation_and_editing_popups(self):
        form = self.model_admin.get_form(self.request)()
        for field in ("format_type", "demo"):
            widget = form.fields[field].widget
            self.assertTrue(widget.can_add_related)
            self.assertTrue(widget.can_change_related)
        self.assertTrue(form.fields["logo_brands"].widget.can_add_related)

    def test_related_object_buttons_respect_permissions(self):
        self.request.user.has_perm = lambda permission: permission.startswith("corporate_broadcast.") and permission.endswith("broadcastlanding")
        form = self.model_admin.get_form(self.request)()
        for field in ("format_type", "demo", "logo_brands"):
            self.assertFalse(form.fields[field].widget.can_add_related)

    def test_helper_models_are_hidden_from_navigation_but_keep_popup_permissions(self):
        for model in (BroadcastDemo, TypesOfPlaceBroadcast):
            model_admin = admin.site.get_model_admin(model)
            self.assertEqual(model_admin.get_model_perms(self.request), {})
            self.assertTrue(model_admin.has_add_permission(self.request))
        self.assertTrue(self.model_admin.get_model_perms(self.request)["add"])

    def test_format_sets_internal_name_without_asking_the_manager(self):
        model_admin = admin.site.get_model_admin(TypesOfPlaceBroadcast)
        form = model_admin.get_form(self.request)
        self.assertNotIn("name", form.base_fields)
        self.assertNotIn("owner", form.base_fields)
        obj = TypesOfPlaceBroadcast(title="Название формата", owner_id="00000000-0000-4000-8000-000000000001")
        obj.save = Mock()
        model_admin.save_model(self.request, obj, None, False)
        self.assertEqual(obj.name, obj.title)
        obj.save.assert_called_once()

    def test_preview_escapes_editor_content(self):
        obj = BroadcastLanding(pk=1, title='<script>alert(1)</script>', description='<img src=x onerror=alert(1)>')
        preview = str(self.model_admin.content_preview(obj))
        self.assertNotIn('<script>', preview)
        self.assertNotIn('<img', preview)
        self.assertIn('&lt;script&gt;', preview)
