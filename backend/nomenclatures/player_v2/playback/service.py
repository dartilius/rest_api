"""Durable event acceptance and factual completed counts without legacy duplication."""

from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef

from nomenclatures.models import Nomenclature, StationCommandV2, StationInstallation
from nomenclatures.player_v2.playback.models import PlaybackEvent


TERMINAL_TYPES = ("completed", "interrupted", "error")
IDENTITY_FIELDS = ("station_id", "playback_id", "media_type", "file_id", "order_id", "order_revision")


def _wire_payload(event):
    return {
        key: (value.strftime("%Y-%m-%d %H:%M:%S") if key == "occurred_at"
              else str(value) if key.endswith("_id") and value is not None else value)
        for key, value in event.items()
    }


def _order_matches(event, nomenclature_id):
    if event["order_id"] is None:
        return True
    # Check the immutable delivered revision, not a subsequently edited playlist.
    command = StationCommandV2.objects.filter(
        nomenclature_id=nomenclature_id, kind="apply_order_manifest",
        body__order_id=str(event["order_id"]), body__revision=event["order_revision"],
    ).first()
    if command is None:
        return False
    body = command.body
    if not any(str(item.get("id")) == str(event["file_id"]) for item in body.get("files", [])):
        return False
    return (event["media_type"] == "ad") == (body.get("placement") == "advertising")


def store_playback_events(credential, events):
    """Return ACKs only for committed journal rows; conflicts never overwrite data.

    The surrounding station-sync transaction commits before its HTTP response.
    A PostgreSQL journal ACK is deliberately not a ClickHouse projection ACK.
    """
    if not events:
        return [], []
    station_id = credential.nomenclature_id
    installation_id = credential.pk if isinstance(credential, StationInstallation) else None
    # One lock also serializes sessions with no existing rows. Other installations
    # at the same station keep independent playback IDs, not a single current file.
    Nomenclature.objects.select_for_update().get(pk=station_id)
    stored, errors = [], []
    for event in events:
        event_id = event["event_id"]
        code = None
        payload = _wire_payload(event)
        existing = PlaybackEvent.objects.filter(event_id=event_id).first()
        if event["station_id"] != station_id:
            code = "station_mismatch"
        elif existing is not None:
            if (existing.nomenclature_id != station_id or existing.payload != payload
                    or existing.installation_id != installation_id):
                code = "event_conflict"
        elif not _order_matches(event, station_id):
            code = "order_mismatch"
        else:
            session = PlaybackEvent.objects.filter(nomenclature_id=station_id, playback_id=event["playback_id"])
            first = session.order_by("event_sequence").first()
            terminal = session.filter(event_type__in=TERMINAL_TYPES).first()
            if first is not None and (
                first.installation_id != installation_id
                or any(first.payload[key] != payload[key] for key in IDENTITY_FIELDS)
            ):
                code = "event_conflict"
            elif session.filter(event_sequence=event["event_sequence"]).exists():
                code = "sequence_conflict"
            elif terminal is not None and (
                event["event_type"] in TERMINAL_TYPES or event["event_sequence"] >= terminal.event_sequence
            ):
                code = "sequence_conflict"
            if code is None:
                values = {key: value for key, value in event.items() if key not in ("station_id", "event_id")}
                try:
                    # Isolate a concurrent event_id collision from the outer command
                    # receipts transaction; no catch inside a broken transaction.
                    with transaction.atomic():
                        PlaybackEvent.objects.create(
                            event_id=event_id, nomenclature_id=station_id,
                            installation_id=installation_id, payload=payload, **values,
                        )
                except IntegrityError:
                    code = "event_conflict"
        if code:
            errors.append({"event_id": str(event_id), "code": code})
        else:
            stored.append(str(event_id))
    order_ids = {event["order_id"] for event in events if event["order_id"] is not None and str(event["event_id"]) in stored}
    if order_ids:
        def project_started():
            from orders.services.order_air_state import confirm_on_air_revisions
            confirm_on_air_revisions(order_ids)
        # Release station/order locks before projection to avoid lock inversion
        # with a parallel apply receipt. Exact revision predicates fence edits.
        transaction.on_commit(project_started)
    return stored, errors


def completed_playbacks():
    """Count only a terminal completion paired with a persisted actual start."""
    starts = PlaybackEvent.objects.filter(
        nomenclature_id=OuterRef("nomenclature_id"), playback_id=OuterRef("playback_id"),
        event_type="started", event_sequence=1,
    )
    return PlaybackEvent.objects.filter(event_type="completed").annotate(
        confirmed_start=Exists(starts),
    ).filter(confirmed_start=True)
