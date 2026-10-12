"""Защищённый polling endpoint нового протокола Content Player."""

from datetime import time
import logging

from django.db import DatabaseError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from nomenclatures.models import StationCommandV2
from orders.models import Order, OrderStationState
from orders.services.order_progress import store_order_progress
from nomenclatures.player_v2.auth import StationTokenAuthentication
from nomenclatures.player_v2.playback.service import store_playback_events
from nomenclatures.player_v2.presence import schedule_station_presence
from nomenclatures.player_v2.runtime.service import accept_runtime
from nomenclatures.player_v2.serializers import (
    StationV2SyncRequestSerializer,
    StationV2SyncResponseSerializer,
)
from nomenclatures.player_v2.sync_state import StationSyncState

logger = logging.getLogger(__name__)


class HasStationCredential(BasePermission):
    def has_permission(self, request, view):
        return request.auth is not None


class StationV2SyncView(APIView):
    authentication_classes = [StationTokenAuthentication]
    permission_classes = [HasStationCredential]

    @extend_schema(request=StationV2SyncRequestSerializer, responses=StationV2SyncResponseSerializer)
    def post(self, request):
        received_at = timezone.now()
        credential = request.auth
        serializer = StationV2SyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            # A readiness receipt can cancel several predecessor orders. Lock
            # the whole batch in a stable order before individual receipts to
            # avoid old->new / new->old cycles between simultaneous syncs.
            previews = StationCommandV2.objects.filter(
                nomenclature=credential.nomenclature,
                command_id__in=[item["command_id"] for item in serializer.validated_data["receipts"]],
                kind__in=("apply_order_manifest", "cancel_order"),
            )
            order_ids = set()
            for preview in previews:
                if preview.body.get("order_id"):
                    order_ids.add(preview.body["order_id"])
                order_ids.update(item["order_id"] for item in preview.body.get("replaces_permanent_visual", []))
            if order_ids:
                list(Order.objects.select_for_update().filter(
                    pk__in=order_ids, nomenclature=credential.nomenclature,
                ).order_by("pk").values_list("pk", flat=True))
            for receipt in serializer.validated_data["receipts"]:
                preview = StationCommandV2.objects.filter(
                    nomenclature=credential.nomenclature, command_id=receipt["command_id"]
                ).first()
                if preview is not None and preview.kind in ("apply_order_manifest", "cancel_order"):
                    # Match enqueue's order -> state -> command lock ordering.
                    Order.objects.select_for_update().filter(pk=preview.body["order_id"]).first()
                    OrderStationState.objects.select_for_update().filter(order_id=preview.body["order_id"]).first()
                command = StationCommandV2.objects.select_for_update().filter(
                    nomenclature=credential.nomenclature,
                    command_id=receipt["command_id"],
                    status=StationCommandV2.Status.PENDING,
                ).first()
                if command is not None:
                    command.status = receipt["status"]
                    command.result = receipt["result"]
                    command.save(update_fields=["status", "result", "updated_at"])
                    self._store_order_receipt(command, receipt)

            progress_reports = serializer.validated_data["order_progress"]
            if progress_reports:
                def store_progress():
                    try:
                        store_order_progress(credential, progress_reports, received_at)
                    except DatabaseError:
                        logger.warning("Order progress storage unavailable; terminal receipts remain committed.")
                transaction.on_commit(store_progress)
            self._store_applied_settings(credential.nomenclature, serializer.validated_data)
            self._store_station_capabilities(credential.nomenclature, serializer.validated_data)
            self._store_visual_output_settings(credential.nomenclature, serializer.validated_data)
            self._store_station_protocol(credential.nomenclature, serializer.validated_data)
            self._clean_runtime_sync_metadata(credential.nomenclature)

            commands = StationCommandV2.objects.filter(
                nomenclature=credential.nomenclature,
                status=StationCommandV2.Status.PENDING,
            ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
            if serializer.validated_data.get("station_protocol", {}).get("unified_orders_version") != 1:
                commands = commands.exclude(kind__in=("apply_order_manifest", "cancel_order"))
            elif serializer.validated_data.get("station_protocol", {}).get("advertising_options_version") != 1:
                # Guard pending snapshots too: a station can downgrade after enqueue.
                # Each JSON condition explicitly requires the key so old snapshots
                # lacking options retain their legacy behavior and remain deliverable.
                requires_options = (
                    Q(body__requires_advertising_options_version=1,
                      body__requires_advertising_options_version__isnull=False)
                    | Q(body__task__parameters__order_parameters__suppress_background_audio=False,
                        body__task__parameters__order_parameters__suppress_background_audio__isnull=False)
                    | Q(body__task__parameters__order_parameters__suppress_background_visual=False,
                        body__task__parameters__order_parameters__suppress_background_visual__isnull=False)
                    | Q(body__task__parameters__order_parameters__audio_muted=True,
                        body__task__parameters__order_parameters__audio_muted__isnull=False)
                )
                commands = commands.exclude(Q(kind="apply_order_manifest") & requires_options)
            if serializer.validated_data.get("station_protocol", {}).get("background_visual_queue_version") != 1:
                commands = commands.exclude(
                    kind="apply_order_manifest", body__requires_background_visual_queue_version=1,
                    body__requires_background_visual_queue_version__isnull=False,
                )
            if serializer.validated_data.get("station_protocol", {}).get("continuous_advertising_version") != 1:
                requires_continuous = (
                    Q(body__requires_continuous_advertising_version=1,
                      body__requires_continuous_advertising_version__isnull=False)
                    | Q(body__placement="advertising", body__placement__isnull=False,
                        body__task__parameters__broadcast_type=7,
                        body__task__parameters__broadcast_type__isnull=False)
                )
                commands = commands.exclude(Q(kind="apply_order_manifest") & requires_continuous)
            commands = commands.order_by("created_at")[:100]

            command_payloads = []
            undelivered_command_ids = []
            for command in commands:
                payload = dict(command.body)
                if command.kind == "apply_order_manifest":
                    from orders.services.unified_order_delivery import refresh_manifest_urls
                    payload = refresh_manifest_urls(payload)
                # Body из БД не может подменять метаданные протокола.
                payload["command_id"] = str(command.command_id)
                payload["kind"] = command.kind
                command_payloads.append(payload)
                if command.delivered_at is None:
                    undelivered_command_ids.append(command.pk)
            if undelivered_command_ids:
                delivered_command_ids = list(
                    StationCommandV2.objects.filter(pk__in=undelivered_command_ids).values_list("command_id", flat=True)
                )
                StationCommandV2.objects.filter(
                    pk__in=undelivered_command_ids,
                    delivered_at__isnull=True,
                ).update(delivered_at=timezone.now())
                OrderStationState.objects.filter(
                    command_id__in=delivered_command_ids,
                    status=OrderStationState.Status.QUEUED,
                ).update(status=OrderStationState.Status.DELIVERED)
            events_stored, event_errors = store_playback_events(
                credential, serializer.validated_data["playback_events"],
            )
            response = {"commands": command_payloads}
            if "playback_events" in request.data:
                response.update(
                    playback_events_stored=events_stored,
                    playback_event_errors=event_errors,
                    playback_event_storage="postgresql",
                )
            schedule_station_presence(
                credential.nomenclature_id,
                received_at=received_at,
            )
            runtime_frame = serializer.validated_data.get("runtime_snapshot")
            if runtime_frame is not None:
                # Commit commands/events first. The response object remains
                # mutable until DRF renders it after this atomic block exits.
                response["runtime_snapshot_received"] = {"accepted": False}
                def store_runtime():
                    try:
                        response["runtime_snapshot_received"] = accept_runtime(
                            credential, runtime_frame, transport="polling",
                        )
                    except DatabaseError:
                        logger.warning("Runtime storage unavailable; command/event acknowledgements remain committed.")
                        response["runtime_snapshot_received"] = {"accepted": False, "code": "storage_unavailable"}
                transaction.on_commit(store_runtime)
            return Response(response)

    @staticmethod
    def _store_order_receipt(command, receipt):
        """Advance only the state attached to this exact revision command."""
        if command.kind not in ("apply_order_manifest", "cancel_order"):
            return
        body = command.body if isinstance(command.body, dict) else {}
        order_id, revision = body.get("order_id"), body.get("revision")
        if not order_id or not isinstance(revision, int):
            return
        state = OrderStationState.objects.select_for_update().filter(
            order_id=order_id, nomenclature=command.nomenclature, command_id=command.command_id,
            desired_revision=revision,
        ).first()
        if state is None:
            return
        result = receipt["result"] or {}
        if receipt["status"] == StationCommandV2.Status.APPLIED and (
            type(result.get("revision")) is not int
            or result.get("revision") != revision
            or (state.desired_action == "cancel" and result.get("cancelled") is not True)
            or (state.desired_action == "apply" and (
                type(result.get("files_verified")) is not int
                or result.get("files_verified") != len(body.get("files", []))
            ))
        ):
            state.status = OrderStationState.Status.FAILED
            state.last_error = "Player вернул неполное подтверждение заказа."
            command.status = StationCommandV2.Status.FAILED
            command.save(update_fields=("status",))
            state.save()
            return
        if receipt["status"] == StationCommandV2.Status.FAILED:
            state.status = OrderStationState.Status.FAILED
            state.last_error = str((receipt["result"] or {}).get("error", "Player не применил команду."))[:4000]
        elif receipt["status"] == StationCommandV2.Status.SUPERSEDED:
            state.status = OrderStationState.Status.SUPERSEDED
        elif state.desired_action == OrderStationState.Action.CANCEL:
            state.status = OrderStationState.Status.CANCELLED
            Order.objects.filter(pk=state.order_id).update(status=3)
        else:
            state.status = OrderStationState.Status.APPLIED
            state.received_revision = revision
            state.ready_revision = revision
            state.applied_revision = revision
        state.save()

        if state.status == OrderStationState.Status.APPLIED:
            def project_started():
                from orders.services.order_air_state import confirm_on_air_revisions
                confirm_on_air_revisions([state.order_id])
            transaction.on_commit(project_started)
            from orders.services.unified_order_delivery import cancel_replaced_visual_orders
            cancel_replaced_visual_orders(command, result)

    @staticmethod
    def _player_sync_state(nomenclature):
        """Move a legacy snapshot before removing it from the broadcast state."""
        cached = getattr(nomenclature, "_locked_player_sync_state", None)
        if cached is not None:
            return cached
        runtime = nomenclature.runtime_state if isinstance(nomenclature.runtime_state, dict) else {}
        settings = runtime.get("applied_settings")
        protocol = runtime.get("station_protocol")
        state, _created = StationSyncState.objects.get_or_create(
            nomenclature=nomenclature,
            defaults={
                "station_protocol": protocol if isinstance(protocol, dict) else {},
            },
        )
        state = StationSyncState.objects.select_for_update().get(pk=state.pk)
        backfill_fields = []
        confirmed = state.applied_settings if isinstance(state.applied_settings, dict) else settings
        if isinstance(confirmed, dict):
            StationV2SyncView._write_station_settings(nomenclature, confirmed)
        if state.applied_settings is not None:
            state.applied_settings = None
            backfill_fields.append("applied_settings")
        if not state.station_protocol and isinstance(protocol, dict) and protocol:
            state.station_protocol = protocol
            backfill_fields.append("station_protocol")
        if backfill_fields:
            state.save(update_fields=[*backfill_fields, "updated_at"])
        legacy_revision = runtime.get("applied_settings_revision")
        if (
            nomenclature.applied_settings_revision is None
            and type(legacy_revision) is int
            and legacy_revision >= 0
        ):
            nomenclature.applied_settings_revision = legacy_revision
            nomenclature.save(update_fields=["applied_settings_revision"])
        nomenclature._locked_player_sync_state = state
        nomenclature.player_sync_state = state
        return state

    @staticmethod
    def _clean_runtime_sync_metadata(nomenclature):
        runtime = nomenclature.runtime_state
        if not isinstance(runtime, dict):
            return
        technical_keys = {"station_protocol", "applied_settings", "applied_settings_revision"}
        if not technical_keys.intersection(runtime):
            return
        # Copy even when this sync omits settings/protocol. The transaction
        # keeps legacy data intact if either storage or event acceptance fails.
        StationV2SyncView._player_sync_state(nomenclature)
        cleaned = {key: value for key, value in runtime.items() if key not in technical_keys}
        # A concurrent legacy heartbeat may have published a newer current
        # file. Clean only the snapshot we copied, never overwrite that file.
        updated = type(nomenclature).objects.filter(
            pk=nomenclature.pk, runtime_state=runtime,
        ).update(runtime_state=cleaned)
        if updated:
            nomenclature.runtime_state = cleaned

    @staticmethod
    def _store_station_protocol(nomenclature, data):
        # Omitting capabilities represents a downgraded/older client. Do not
        # keep advertising support for commands that it can no longer apply.
        protocol = data.get("station_protocol", {})
        state = StationV2SyncView._player_sync_state(nomenclature)
        if state.station_protocol != protocol:
            state.station_protocol = protocol
            state.save(update_fields=["station_protocol", "updated_at"])

    @staticmethod
    def _store_applied_settings(nomenclature, data):
        """Сохраняет сообщённую Player конфигурацию в исходное поле настроек."""
        settings = data.get("applied_settings")
        if settings is None:
            return

        revision = data["applied_settings_revision"]
        # Move any historical shadow first; a fresh report always wins over it.
        StationV2SyncView._player_sync_state(nomenclature)
        StationV2SyncView._write_station_settings(nomenclature, settings, revision=revision)

    @staticmethod
    def _write_station_settings(nomenclature, settings, *, revision=None):
        fields = []
        if nomenclature.settings != settings:
            nomenclature.settings = settings
            fields.append("settings")
        if revision is not None and nomenclature.applied_settings_revision != revision:
            nomenclature.applied_settings_revision = revision
            fields.append("applied_settings_revision")
        worktimes = {day.get("worktime") for day in settings.values() if isinstance(day, dict) and isinstance(day.get("worktime"), str)}
        if len(worktimes) == 1:
            try:
                start, end = worktimes.pop().split("-")
                start, end = time.fromisoformat(start), time.fromisoformat(end)
            except ValueError:
                pass  # A historical snapshot can predate strict v2 validation.
            else:
                for field, value in (("worktime_start", start), ("worktime_end", end)):
                    if getattr(nomenclature, field) != value:
                        setattr(nomenclature, field, value)
                        fields.append(field)
        if fields:
            nomenclature.save(update_fields=fields)

    @staticmethod
    def _store_station_capabilities(nomenclature, data):
        """Сохраняет только изменившуюся минимальную карту устройств Player."""
        capabilities = data.get("station_capabilities")
        if capabilities is None or nomenclature.station_capabilities == capabilities:
            return
        nomenclature.station_capabilities = capabilities
        nomenclature.save(update_fields=["station_capabilities"])

    @staticmethod
    def _store_visual_output_settings(nomenclature, data):
        """Сохраняет только подтверждённое самим Player состояние поворота."""
        visual_output = data.get("applied_visual_output")
        if visual_output is None or nomenclature.visual_output_settings == visual_output:
            return
        nomenclature.visual_output_settings = visual_output
        nomenclature.save(update_fields=["visual_output_settings"])
