from django.db import connection
from django.test.utils import CaptureQueriesContext

import pytest
from celery import states

from counterparties.models import Counterparty
from nomenclatures.serializers import TenantWriteSerializer
from nomenclatures.tasks import update_task


@pytest.mark.django_db
def test_tenant_list_validation_uses_one_counterparty_query():
    """A tenant list is validated with one lookup regardless of its size."""
    tenants = [
        Counterparty.objects.create(first_name=f"Tenant {index}")
        for index in range(3)
    ]
    serializer = TenantWriteSerializer(data=[{"id": str(tenant.id)} for tenant in tenants], many=True)

    with CaptureQueriesContext(connection) as queries:
        assert serializer.is_valid(), serializer.errors

    counterparty_queries = [
        query for query in queries.captured_queries if '"counterparties"' in query["sql"]
    ]
    assert len(counterparty_queries) == 1


@pytest.mark.django_db(transaction=True)
def test_changing_legal_entity_clears_broadcast_for_unused_counterparty(
    nomenclature,
    monkeypatch,
):
    """The former legal entity stops broadcasting when no nomenclature uses it."""
    monkeypatch.setattr(
        "nomenclatures.signals.update_opensearch_for_instance.delay",
        lambda *_args, **_kwargs: None,
    )
    old_legal_entity = Counterparty.objects.create(first_name="Old legal entity")
    new_legal_entity = Counterparty.objects.create(first_name="New legal entity")

    nomenclature.legalEntity = old_legal_entity
    nomenclature.save(update_fields=["legalEntity"])
    old_legal_entity.refresh_from_db()
    assert old_legal_entity.broadcast is True

    nomenclature.legalEntity = new_legal_entity
    nomenclature.save(update_fields=["legalEntity"])

    old_legal_entity.refresh_from_db()
    new_legal_entity.refresh_from_db()
    assert old_legal_entity.broadcast is False
    assert new_legal_entity.broadcast is True


def test_update_task_marks_unexpected_minio_failure_as_failure(monkeypatch):
    """A failed software update is not reported to Celery as successful."""
    def raise_minio_error(*_args, **_kwargs):
        raise ConnectionError("MinIO is unavailable")

    monkeypatch.setattr("nomenclatures.tasks.get_nomenclature", raise_minio_error)

    result = update_task.apply(args=("nomenclature-id", "owner-id"))

    assert result.state == states.FAILURE
    assert isinstance(result.result, ConnectionError)
