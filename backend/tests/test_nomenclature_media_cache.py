import pytest
from rest_framework.response import Response

from api.mixins import SignedMediaNoCacheMixin
from nomenclatures.models import NomenclatureImage
from nomenclatures.serializers import InNomenclaturePhotoSerializer
from nomenclatures.views.video import NomenclatureVideoViewSet


class _FinalizeResponseParent:
    def finalize_response(self, request, response, *args, **kwargs):
        return response


class _SignedMediaView(SignedMediaNoCacheMixin, _FinalizeResponseParent):
    pass


def test_photo_serializer_requests_url_from_storage_each_time(monkeypatch):
    storage = NomenclatureImage._meta.get_field("source").storage
    generated_urls = iter(
        (
            "https://files.example/photo.jpg?X-Amz-Date=20260830T010000Z",
            "https://files.example/photo.jpg?X-Amz-Date=20260831T010000Z",
        )
    )
    monkeypatch.setattr(storage, "url", lambda name: next(generated_urls))
    image = NomenclatureImage(source="Интерьер/photo.jpg")

    first = InNomenclaturePhotoSerializer(image).data["source"]
    second = InNomenclaturePhotoSerializer(image).data["source"]

    assert first != second
    assert "X-Amz-Date=20260831" in second


def test_signed_media_mixin_disables_http_caching():
    response = _SignedMediaView().finalize_response(None, Response())

    assert response["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response["Pragma"] == "no-cache"
    assert response["Expires"] == "0"


def test_video_viewset_disables_http_caching():
    assert issubclass(NomenclatureVideoViewSet, SignedMediaNoCacheMixin)


@pytest.mark.django_db
def test_nomenclature_response_with_presigned_urls_is_not_http_cached(
    anon_client,
    nomenclature,
):
    response = anon_client.get(f"/api/nomenclatures/{nomenclature.id}/")

    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response["Pragma"] == "no-cache"
    assert response["Expires"] == "0"


@pytest.mark.django_db
def test_photo_response_with_presigned_urls_is_not_http_cached(anon_client):
    response = anon_client.get("/api/photos/get_photos/")

    assert response.status_code == 200
    assert response["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
