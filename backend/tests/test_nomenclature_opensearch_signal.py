from types import SimpleNamespace
from unittest.mock import patch

from nomenclatures.signals import delete_from_opensearch


def test_delete_from_opensearch_deletes_document_by_its_id():
    instance = SimpleNamespace(id="station-id")

    with patch("nomenclatures.documents.NomenclatureDocument") as document_class:
        delete_from_opensearch(sender=None, instance=instance)

    document_class.assert_called_once_with(meta={"id": "station-id"})
    document_class.return_value.delete.assert_called_once_with(ignore=404)
