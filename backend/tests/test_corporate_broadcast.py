from datetime import time
from types import SimpleNamespace
from unittest.mock import PropertyMock, patch
from uuid import uuid4

import pytest
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory

from corporate_broadcast.constants import FORMAT_CONTENT
from corporate_broadcast.models import BroadcastDemo, BroadcastDemoAsset
from corporate_broadcast.serializers import BroadcastDemoSerializer
from corporate_broadcast.views import BroadcastDemoViewSet
from feedback.models import Feedback
from feedback.serializers import CONSENT_VERSION, FeedbackSerializer
from feedback.signals import _enqueue
from feedback.tasks import send_feedback_email, send_feedback_mail
from feedback.views import FeedbackViewSet
from files.models import File


PAYLOAD = {
    "request_type": "corporate_broadcast", "name": "Иван", "company": "Компания",
    "phone": "+7 (999) 123-45-67", "pathname": "/corporate-broadcast", "consent": True,
    "request_data": {"business_type": "store", "object_count": 12, "area_per_object": 250,
                     "format": "audio-screens", "screens": "existing", "video_content": "consultation",
                     "content": {"music": True, "announcements": True, "slides": True, "promotions": False}},
}


def test_legacy_payload_remains_valid():
    serializer = FeedbackSerializer(data={"name": "Legacy", "brandId": "brand", "nomenclaturesIds": ["place"]})
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["brand_id"] == "brand"
    assert serializer.validated_data["nomenclatures_ids"] == ["place"]
    assert Feedback(**serializer.validated_data).request_type == "general"


@pytest.mark.parametrize("change,field", [
    ({"name": " "}, "name"), ({"phone": "bad"}, "phone"),
    ({"phone": "", "email": "bad"}, "email"),
    ({"phone": "", "email": ""}, "phone"),
    ({"consent": False}, "consent"), ({"consent": "true"}, "consent"),
    ({"consent_version": "spoofed"}, "consent_version"), ({"consent_at": "2020-01-01"}, "consent_at"),
    ({"pathname": "/corporate-broadcast?email=user@example.com"}, "pathname"),
    ({"pathname": "https://example.com/corporate-broadcast"}, "pathname"),
    ({"pathname": "//[invalid"}, "pathname"),
    ({"unexpected": "value"}, "unexpected"), ({"message": "x" * 5001}, "message"),
    ({"request_type": "unknown"}, "request_type"), ({"company": "x" * 251}, "company"),
])
def test_feedback_rejects_invalid_payload(change, field):
    serializer = FeedbackSerializer(data={**PAYLOAD, **change})
    assert not serializer.is_valid()
    assert field in serializer.errors


@pytest.mark.parametrize("config,field", [
    ({"object_count": 0}, "object_count"), ({"object_count": 1.5}, "object_count"),
    ({"object_count": True}, "object_count"), ({"object_count": "1"}, "object_count"),
    ({"area_per_object": 0}, "area_per_object"), ({"area_per_object": float("nan")}, "area_per_object"),
    ({"area_per_object": True}, "area_per_object"), ({"format": "corporate-network"}, "format"),
    ({"format": "audio", "screens": "existing"}, "screens"),
    ({"screens": "existing"}, "format"),
    ({"format": "audio", "content": {"slides": True}}, "content"),
    ({"format": "audio", "content": {"music": "yes"}}, "content"),
    ({"format": "audio", "content": {"unknown": False}}, "content"),
    ({"unknown": "value"}, "unknown"),
])
def test_config_errors_are_nested(config, field):
    serializer = FeedbackSerializer(data={**PAYLOAD, "request_data": config})
    assert not serializer.is_valid()
    assert field in serializer.errors["request_data"]


@pytest.mark.parametrize("selected", FORMAT_CONTENT)
def test_all_five_constructor_formats(selected):
    config = {"format": selected, "content": {key: True for key in FORMAT_CONTENT[selected]}}
    serializer = FeedbackSerializer(data={**PAYLOAD, "request_data": config})
    assert serializer.is_valid(), serializer.errors


@pytest.mark.parametrize("config", [{}, {"object_count": 3}])
def test_general_corporate_request_does_not_require_constructor(config):
    serializer = FeedbackSerializer(data={**PAYLOAD, "phone": "", "email": "user@example.com", "request_data": config})
    assert serializer.is_valid(), serializer.errors


def test_consent_timestamp_and_version_are_server_generated():
    serializer = FeedbackSerializer(data=PAYLOAD)
    assert serializer.is_valid(), serializer.errors
    with patch.object(Feedback.objects, "create", side_effect=lambda **kwargs: Feedback(**kwargs)) as create:
        instance = serializer.save()
    assert instance.consent_version == CONSENT_VERSION
    assert instance.consent_at is not None
    assert create.call_args.kwargs["request_data"] == PAYLOAD["request_data"]


def test_create_endpoint_returns_201_without_claiming_email_delivery():
    cache.clear()
    request = APIRequestFactory().post("/api/feedback/", PAYLOAD, format="json")
    with patch.object(Feedback.objects, "create", side_effect=lambda **kwargs: Feedback(created=timezone.now(), **kwargs)):
        response = FeedbackViewSet.as_view({"post": "create"})(request)
    assert response.status_code == 201
    assert response.data["id"]
    assert response.data["created"]
    assert response.data["request_type"] == "corporate_broadcast"


def test_feedback_throttle_rejects_eleventh_attempt():
    cache.clear()
    view = FeedbackViewSet.as_view({"post": "create"})
    factory = APIRequestFactory()
    statuses = [view(factory.post("/api/feedback/", {"request_type": "invalid"}, format="json")).status_code for _ in range(11)]
    assert statuses == [400] * 10 + [429]
    cache.clear()


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_feedback_has_no_public_read_or_edit(method):
    request = getattr(APIRequestFactory(), method)("/api/feedback/")
    assert FeedbackViewSet.as_view({"post": "create"})(request).status_code == 405


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
def test_demo_api_is_read_only(method):
    request = getattr(APIRequestFactory(), method)("/api/broadcast-demos/")
    assert BroadcastDemoViewSet.as_view({"get": "list"})(request).status_code == 405


def test_unknown_demo_filter_is_400_without_querying_database():
    response = BroadcastDemoViewSet.as_view({"get": "list"})(APIRequestFactory().get("/api/broadcast-demos/", {"format": "invalid"}))
    assert response.status_code == 400
    assert "format" in response.data


def test_queue_failure_is_isolated_from_saved_request():
    task = SimpleNamespace(name="notification", delay=lambda **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
    callbacks = []
    with patch("feedback.signals.transaction.on_commit", side_effect=callbacks.append):
        _enqueue(task, feedback_id=uuid4(), name="Иван")
    assert len(callbacks) == 1
    callbacks[0]()  # Must not propagate a broker error.


@pytest.mark.parametrize("task,extra", [(send_feedback_email, {"phone": "123"}), (send_feedback_mail, {})])
def test_corporate_notification_contains_configuration_and_company(task, extra):
    with patch("feedback.tasks._send") as send:
        task.run(name="Иван", email="user@example.com", message="Комментарий", created="06.10.2026", request_type="corporate_broadcast", company="Компания", request_data=PAYLOAD["request_data"], request_id="request-id", **extra)
    body = send.call_args.kwargs["body"]
    assert "Компания" in body and "12" in body and "250" in body
    assert "Аудио + экраны" in body and "Музыкальный фон" in body
    assert "request-id" in body and "Комментарий" in body


@pytest.mark.parametrize("role,file_type,source,active", [
    ("audio", 1, "media/demo.mp3", True), ("video", 4, "media/demo.mp3", True),
    ("poster", 2, "media/demo.svg", True), ("audio", 0, "media/demo.mp3", False),
])
def test_invalid_media_is_rejected(role, file_type, source, active):
    asset = BroadcastDemoAsset(file=File(type=file_type, source=source, is_active=active), role=role)
    assert not asset.is_playable
    with pytest.raises(ValidationError):
        asset.clean()


def test_demo_serializer_omits_inactive_asset_and_storage_metadata():
    active = BroadcastDemoAsset(file=File(type=0, source="media/demo.mp3", length=time(0, 1, 12)), role="audio")
    inactive = BroadcastDemoAsset(file=File(type=0, source="media/private.mp3", is_active=False), role="audio")
    demo = BroadcastDemo(title="Демо", format="audio")
    with patch.object(type(demo.assets), "all", return_value=[active, inactive]), patch.object(File, "url", new_callable=PropertyMock, return_value="https://media.example/demo.mp3") as url:
        result = BroadcastDemoSerializer(demo).data
    assert len(result["assets"]) == 1
    assert result["assets"][0]["duration_seconds"] == 72
    assert url.call_count == 1
    assert "source" not in result["assets"][0] and "file" not in result["assets"][0]


@pytest.mark.django_db
def test_saved_feedback_notifies_only_after_commit(django_capture_on_commit_callbacks):
    cache.clear()
    with patch("feedback.signals.send_feedback_email.delay") as manager, patch("feedback.signals.send_feedback_mail.delay") as user:
        with django_capture_on_commit_callbacks(execute=True):
            response = APIClient().post("/api/feedback/", {**PAYLOAD, "email": "user@example.com"}, format="json")
            assert response.status_code == 201
            assert Feedback.objects.filter(id=response.data["id"]).exists()
            manager.assert_not_called()
            user.assert_not_called()
        manager.assert_called_once()
        user.assert_called_once()
        assert manager.call_args.kwargs["request_data"] == PAYLOAD["request_data"]
    cache.clear()


@pytest.mark.django_db
def test_rollback_does_not_enqueue_notifications():
    with patch("feedback.signals.send_feedback_email.delay") as manager:
        with pytest.raises(RuntimeError), transaction.atomic():
            Feedback.objects.create(name="Иван", request_type="corporate_broadcast")
            raise RuntimeError("rollback")
        manager.assert_not_called()
    assert Feedback.objects.count() == 0


def stored_file(source="media/demo.mp3", file_type=0):
    # Test metadata only: no upload or File.save() storage/media probing.
    file = File(name="Demo", source=source, type=file_type, hash=str(uuid4()), md5hash="a" * 32, sha256hash="b" * 64)
    File.objects.bulk_create([file])
    return file


@pytest.mark.django_db
def test_demo_publication_filter_order_and_unpublished_access():
    file = stored_file()
    public = BroadcastDemo.objects.create(title="Published", format="audio", is_published=True, sort_order=2)
    network = BroadcastDemo.objects.create(title="Network", format="corporate-network", is_published=True, sort_order=1)
    private = BroadcastDemo.objects.create(title="Private", format="audio")
    empty = BroadcastDemo.objects.create(title="Empty", format="audio", is_published=True)
    for demo in (public, network, private):
        BroadcastDemoAsset.objects.create(demo=demo, file=file, role="audio")
    client = APIClient()
    with patch.object(File, "url", new_callable=PropertyMock, return_value="https://media.example/demo.mp3"):
        response = client.get("/api/broadcast-demos/")
        assert response.status_code == 200
        assert [row["title"] for row in response.data["results"]] == ["Network", "Published"]
        assert response["Cache-Control"] == "no-store"
        assert client.get("/api/broadcast-demos/", {"format": "corporate-network"}).data["count"] == 1
        assert client.get("/api/broadcast-demos/", {"format": "audio"}).data["count"] == 1
        assert client.get(f"/api/broadcast-demos/{private.id}/").status_code == 404
        assert client.get(f"/api/broadcast-demos/{empty.id}/").status_code == 404
        File.objects.filter(pk=file.pk).update(is_active=False)
        assert client.get("/api/broadcast-demos/").data["count"] == 0
        assert client.get(f"/api/broadcast-demos/{public.id}/").status_code == 404


def test_demo_publication_formset_requires_media_not_only_poster():
    from corporate_broadcast.admin import DemoAssetFormSet
    demo = BroadcastDemo(title="Preview", format="audio", is_published=True)
    formset = object.__new__(DemoAssetFormSet)
    formset.instance = demo
    formset.forms = []
    formset._errors = []
    with patch("django.forms.models.BaseInlineFormSet.clean"):
        with pytest.raises(ValidationError):
            formset.clean()
        asset = BroadcastDemoAsset(file=File(type=0, source="media/demo.mp3"), role="audio")
        formset.forms = [SimpleNamespace(cleaned_data={"role": "audio"}, instance=asset)]
        formset.clean()
        formset.forms = [SimpleNamespace(cleaned_data={"role": "poster"}, instance=asset)]
        with pytest.raises(ValidationError):
            formset.clean()


def test_demo_admin_does_not_grant_non_staff_publish_permission():
    from django.contrib.admin.sites import AdminSite
    from corporate_broadcast.admin import BroadcastDemoAdmin
    admin = BroadcastDemoAdmin(BroadcastDemo, AdminSite())
    request = SimpleNamespace(user=SimpleNamespace(has_perm=lambda permission: False))
    assert not admin.has_add_permission(request)
    assert not admin.has_change_permission(request)


def test_general_request_rejects_corporate_configuration():
    serializer = FeedbackSerializer(data={"name": "Legacy", "request_data": {"format": "audio"}})
    assert not serializer.is_valid()
    assert "request_data" in serializer.errors


def test_attribution_does_not_accept_contact_parameters():
    serializer = FeedbackSerializer(data={**PAYLOAD, "attribution": {"version": 1, "first_touch": {"landing_path": "/corporate-broadcast?email=user@example.com"}}})
    assert not serializer.is_valid()
    assert "attribution" in serializer.errors
