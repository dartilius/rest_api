"""Creation and rotation of opaque credentials for Player v2 stations."""

from __future__ import annotations

import hashlib
import secrets

from nomenclatures.models import StationCredential, StationInstallation


def hash_station_token(token: str) -> str:
    """Return the stable lookup hash; callers must never persist ``token``."""

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_station_token() -> str:
    """Create an opaque high-entropy secret for one station installation."""

    return secrets.token_urlsafe(32)


def issue_station_token(credential: StationCredential | StationInstallation) -> str:
    """Replace a credential secret and return its plaintext exactly once."""

    token = generate_station_token()
    credential.token_hash = hash_station_token(token)
    credential.is_active = True
    credential.save(update_fields=["token_hash", "is_active", "rotated_at"])
    return token
