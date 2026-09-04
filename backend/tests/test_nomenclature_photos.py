import hashlib
from http import HTTPStatus
from unittest.mock import Mock

import pytest

from nomenclatures.models import NomenclatureImage


@pytest.fixture
def inactive_offweb_nomenclature(nomenclature):
    nomenclature.is_active = False
    nomenclature.for_web = False
    nomenclature.save(update_fields=("is_active", "for_web"))
    return nomenclature


@pytest.fixture
def inactive_nomenclature_photo(inactive_offweb_nomenclature):
    photo = NomenclatureImage(
        source="exterior/test.jpg",
        type=NomenclatureImage.PhotoType.EXTERIOR,
        nomenclature=inactive_offweb_nomenclature,
        hash=hashlib.md5(b"existing-photo").hexdigest(),
    )
    NomenclatureImage.objects.bulk_create([photo])
    return photo


@pytest.mark.django_db
class TestInactiveNomenclaturePhotos:
    def test_add_photo(self, admin_client, inactive_offweb_nomenclature, monkeypatch):
        storage = NomenclatureImage._meta.get_field("source").storage
        monkeypatch.setattr(
            storage,
            "save",
            Mock(side_effect=lambda name, *args, **kwargs: name),
        )
        monkeypatch.setattr(
            storage,
            "url",
            Mock(return_value="https://minio.test/photo.jpg"),
        )

        response = admin_client.post(
            f"/api/photos/{inactive_offweb_nomenclature.id}/add_photo/",
            data={
                "source": "data:test.jpg;base64,dGVzdA==",
                "type": NomenclatureImage.PhotoType.INTERIOR,
            },
            format="json",
        )

        assert response.status_code == HTTPStatus.CREATED
        photo = NomenclatureImage.objects.get(pk=response.json()["id"])
        assert photo.nomenclature_id == inactive_offweb_nomenclature.id
        assert photo.hash == hashlib.md5(b"test").hexdigest()

    def test_get_photos(self, admin_client, inactive_offweb_nomenclature):
        response = admin_client.get(
            f"/api/photos/{inactive_offweb_nomenclature.id}/get_nomenclature_photos/"
        )

        assert response.status_code == HTTPStatus.OK

    def test_patch_photo_type(
        self, admin_client, inactive_nomenclature_photo, monkeypatch
    ):
        storage = NomenclatureImage._meta.get_field("source").storage
        monkeypatch.setattr(
            storage,
            "url",
            Mock(return_value="https://minio.test/photo.jpg"),
        )
        old_hash = inactive_nomenclature_photo.hash

        response = admin_client.patch(
            f"/api/photos/{inactive_nomenclature_photo.id}/",
            data={"type": NomenclatureImage.PhotoType.INTERIOR},
            format="json",
        )

        assert response.status_code == HTTPStatus.OK
        inactive_nomenclature_photo.refresh_from_db()
        assert (
            inactive_nomenclature_photo.type
            == NomenclatureImage.PhotoType.INTERIOR
        )
        assert inactive_nomenclature_photo.source.name == "exterior/test.jpg"
        assert inactive_nomenclature_photo.hash == old_hash

    def test_patch_photo_source_removes_replaced_minio_object(
        self,
        admin_client,
        inactive_nomenclature_photo,
        monkeypatch,
        django_capture_on_commit_callbacks,
    ):
        storage = NomenclatureImage._meta.get_field("source").storage
        monkeypatch.setattr(
            storage,
            "save",
            Mock(side_effect=lambda name, *args, **kwargs: name),
        )
        monkeypatch.setattr(
            storage,
            "url",
            Mock(return_value="https://minio.test/photo.jpg"),
        )
        delete_mock = Mock()
        monkeypatch.setattr(storage, "delete", delete_mock)
        old_source_name = inactive_nomenclature_photo.source.name

        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.patch(
                f"/api/photos/{inactive_nomenclature_photo.id}/",
                data={"source": "data:new.jpg;base64,bmV3LXBob3Rv"},
                format="json",
            )

        assert response.status_code == HTTPStatus.OK
        inactive_nomenclature_photo.refresh_from_db()
        assert (
            inactive_nomenclature_photo.hash
            == hashlib.md5(b"new-photo").hexdigest()
        )
        delete_mock.assert_called_once_with(old_source_name)

    def test_delete_photo_removes_minio_object(
        self,
        admin_client,
        inactive_nomenclature_photo,
        monkeypatch,
        django_capture_on_commit_callbacks,
    ):
        storage = NomenclatureImage._meta.get_field("source").storage
        delete_mock = Mock()
        monkeypatch.setattr(storage, "delete", delete_mock)
        source_name = inactive_nomenclature_photo.source.name

        with django_capture_on_commit_callbacks(execute=True):
            response = admin_client.delete(
                f"/api/photos/{inactive_nomenclature_photo.id}/"
            )

        assert response.status_code == HTTPStatus.NO_CONTENT
        assert not NomenclatureImage.objects.filter(
            pk=inactive_nomenclature_photo.id
        ).exists()
        delete_mock.assert_called_once_with(source_name)
