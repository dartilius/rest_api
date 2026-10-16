"""Постоянное подписанное подтверждение для восстановления установки Player v2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from django.core import signing

from nomenclatures.models import StationInstallation


RECOVERY_TOKEN_SALT = "nomenclatures.player_v2.station-recovery:v1"
_CLAIM_FIELDS = {
    "version",
    "installation_id",
    "nomenclature_id",
    "created_by_id",
    "created_at",
}


class InvalidRecoveryToken(ValueError):
    """Ключ восстановления не подписан сервисом или имеет неверную структуру."""


@dataclass(frozen=True, slots=True)
class RecoveryClaims:
    installation_id: UUID
    nomenclature_id: UUID
    created_by_id: UUID
    created_at: str


def issue_recovery_token(installation: StationInstallation) -> str:
    """Вернуть стабильное подтверждение неизменной идентичности установки."""

    if installation.pk is None or installation.created_at is None:
        raise ValueError("Recovery proof requires a saved station installation.")
    payload = {
        "version": 1,
        "installation_id": str(installation.pk),
        "nomenclature_id": str(installation.nomenclature_id),
        "created_by_id": str(installation.created_by_id),
        "created_at": _canonical_datetime(installation.created_at),
    }
    return _signer().sign_object(payload)


def decode_recovery_token(token: str) -> RecoveryClaims:
    """Проверить подпись и строгую структуру утверждений первой версии."""

    if not isinstance(token, str) or not token or len(token) > 4096 or any(char.isspace() for char in token):
        raise InvalidRecoveryToken("Invalid recovery token.")
    try:
        payload = _signer().unsign_object(token)
    except (signing.BadSignature, TypeError, ValueError) as exc:
        raise InvalidRecoveryToken("Invalid recovery token.") from exc
    if not isinstance(payload, dict) or set(payload) != _CLAIM_FIELDS:
        raise InvalidRecoveryToken("Invalid recovery token claims.")
    try:
        if type(payload["version"]) is not int or payload["version"] != 1:
            raise ValueError
        installation_id = _canonical_uuid(payload["installation_id"])
        nomenclature_id = _canonical_uuid(payload["nomenclature_id"])
        created_by_id = _canonical_uuid(payload["created_by_id"])
        created_at = payload["created_at"]
        if not isinstance(created_at, str):
            raise ValueError
        parsed_created_at = datetime.fromisoformat(created_at)
        if _canonical_datetime(parsed_created_at) != created_at:
            raise ValueError
    except (KeyError, TypeError, ValueError) as exc:
        raise InvalidRecoveryToken("Invalid recovery token claims.") from exc
    return RecoveryClaims(
        installation_id=installation_id,
        nomenclature_id=nomenclature_id,
        created_by_id=created_by_id,
        created_at=created_at,
    )


def recovery_claims_match(installation: StationInstallation, claims: RecoveryClaims) -> bool:
    """Проверить, что подтверждение всё ещё описывает именно эту установку."""

    return (
        installation.pk == claims.installation_id
        and installation.nomenclature_id == claims.nomenclature_id
        and installation.created_by_id == claims.created_by_id
        and _canonical_datetime(installation.created_at) == claims.created_at
    )


def _signer() -> signing.Signer:
    # У Signer намеренно нет срока действия: восстановление должно переживать
    # долгий офлайн, а отзыв и перепривязка проверяются по актуальной БД.
    return signing.Signer(salt=RECOVERY_TOKEN_SALT)


def _canonical_uuid(value: object) -> UUID:
    if not isinstance(value, str):
        raise ValueError
    parsed = UUID(value)
    if str(parsed) != value:
        raise ValueError
    return parsed


def _canonical_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        # В проекте USE_TZ=False: не приписываем локальной дате пояс UTC.
        return value.isoformat(timespec="microseconds")
    return value.astimezone(UTC).isoformat(timespec="microseconds")
