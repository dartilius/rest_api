from api.mixins import SignedMediaNoCacheMixin
from brands.models import Brand
from brands.serializers import BrandCardSerializer
from brands.views import BrandViewSet


def test_brand_logo_serializer_requests_url_from_storage_each_time(monkeypatch):
    storage = Brand._meta.get_field("logotype").storage
    generated_urls = iter(
        (
            "https://files.example/logo.png?X-Amz-Date=20260830T010000Z",
            "https://files.example/logo.png?X-Amz-Date=20260831T010000Z",
        )
    )
    monkeypatch.setattr(storage, "url", lambda name: next(generated_urls))
    brand = Brand(name="Test", logotype="brand_logo/logo.png")

    first = BrandCardSerializer(brand).data["logotype"]
    second = BrandCardSerializer(brand).data["logotype"]

    assert first != second
    assert "X-Amz-Date=20260831" in second


def test_brand_storage_does_not_cache_presigned_urls():
    storage = Brand._meta.get_field("logotype").storage

    assert storage.url_caching_enabled is False


def test_brand_responses_use_signed_media_no_cache_mixin():
    assert issubclass(BrandViewSet, SignedMediaNoCacheMixin)
