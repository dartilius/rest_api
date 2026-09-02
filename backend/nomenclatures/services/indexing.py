"""Context used while replacing all tenant relations of a nomenclature."""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Iterator
from uuid import UUID


_suppressed_tenant_indexing_ids: ContextVar[frozenset[UUID]] = ContextVar(
    "suppressed_tenant_indexing_ids",
    default=frozenset(),
)


@contextmanager
def suppress_tenant_indexing(nomenclature_id: UUID) -> Iterator[None]:
    """Suppress per-row indexing signals during a full tenant replacement."""
    suppressed_ids = _suppressed_tenant_indexing_ids.get()
    token = _suppressed_tenant_indexing_ids.set(suppressed_ids | {nomenclature_id})
    try:
        yield
    finally:
        _suppressed_tenant_indexing_ids.reset(token)


def is_tenant_indexing_suppressed(nomenclature_id: UUID) -> bool:
    """Return whether indexing is currently suppressed for this nomenclature."""
    return nomenclature_id in _suppressed_tenant_indexing_ids.get()
