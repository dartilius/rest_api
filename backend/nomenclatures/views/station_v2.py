"""Защищённый polling endpoint нового протокола Content Player."""

from datetime import time

from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from nomenclatures.models import StationCommandV2
from nomenclatures.station_auth import StationTokenAuthentication
from nomenclatures.station_v2_serializers import StationV2SyncRequestSerializer


class HasStationCredential(BasePermission):
    def has_permission(self, request, view):
        return request.auth is not None


class StationV2SyncView(APIView):
    authentication_classes = [StationTokenAuthentication]
    permission_classes = [HasStationCredential]

    def post(self, request):
        credential = request.auth
        serializer = StationV2SyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            for receipt in serializer.validated_data["receipts"]:
                command = StationCommandV2.objects.select_for_update().filter(
                    nomenclature=credential.nomenclature,
                    command_id=receipt["command_id"],
                    status=StationCommandV2.Status.PENDING,
                ).first()
                if command is not None:
                    command.status = receipt["status"]
                    command.result = receipt["result"]
                    command.save(update_fields=["status", "result", "updated_at"])

            self._store_applied_settings(credential.nomenclature, serializer.validated_data)
            self._store_station_capabilities(credential.nomenclature, serializer.validated_data)
            self._store_visual_output_settings(credential.nomenclature, serializer.validated_data)

            commands = StationCommandV2.objects.filter(
                nomenclature=credential.nomenclature,
                status=StationCommandV2.Status.PENDING,
            ).filter(Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now()))
            commands = commands.order_by("created_at")[:100]

            command_payloads = []
            undelivered_command_ids = []
            for command in commands:
                payload = dict(command.body)
                # Body из БД не может подменять метаданные протокола.
                payload["command_id"] = str(command.command_id)
                payload["kind"] = command.kind
                command_payloads.append(payload)
                if command.delivered_at is None:
                    undelivered_command_ids.append(command.pk)
            if undelivered_command_ids:
                StationCommandV2.objects.filter(
                    pk__in=undelivered_command_ids,
                    delivered_at__isnull=True,
                ).update(delivered_at=timezone.now())
            return Response({"commands": command_payloads})

    @staticmethod
    def _store_applied_settings(nomenclature, data):
        """Сохраняет снимок Player как подтверждённые настройки номенклатуры."""
        settings = data.get("applied_settings")
        if settings is None:
            return

        runtime_state = dict(nomenclature.runtime_state or {})
        revision = data["applied_settings_revision"]
        runtime_state.pop("applied_settings", None)
        runtime_state.pop("applied_settings_revision", None)
        runtime_changed = runtime_state != (nomenclature.runtime_state or {})
        settings_changed = nomenclature.settings != settings
        revision_changed = nomenclature.applied_settings_revision != revision
        if not (runtime_changed or settings_changed or revision_changed):
            return

        nomenclature.runtime_state = runtime_state
        nomenclature.settings = settings
        nomenclature.applied_settings_revision = revision

        update_fields = ["runtime_state", "settings", "applied_settings_revision"]
        worktimes = {day["worktime"] for day in settings.values() if isinstance(day, dict)}
        if len(worktimes) == 1:
            start, end = worktimes.pop().split("-")
            nomenclature.worktime_start = time.fromisoformat(start)
            nomenclature.worktime_end = time.fromisoformat(end)
            update_fields.extend(("worktime_start", "worktime_end"))
        nomenclature.save(update_fields=update_fields)

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
