"""JWT-защищённая привязка Player к выбранной пользователем точке."""

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from nomenclatures.models import Nomenclature, StationCredential, StationInstallation
from nomenclatures.player_v2.credentials import (
    generate_station_token,
    hash_station_token,
    issue_station_token,
)
from nomenclatures.player_v2.serializers import StationV2BindingRequestSerializer


class StationV2BindingView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = StationV2BindingRequestSerializer

    def post(self, request):
        serializer = StationV2BindingRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nomenclature_id = serializer.validated_data["nomenclature_id"]
        try:
            nomenclature = Nomenclature.objects.select_related("legalEntity").get(pk=nomenclature_id)
        except (Nomenclature.DoesNotExist, ValueError, TypeError):
            return Response({"detail": "Точка вещания не найдена."}, status=status.HTTP_404_NOT_FOUND)

        user = request.user
        is_admin = user.is_authenticated and (
            getattr(user, "is_admin", False)
            or getattr(user, "is_superuser", False)
            or getattr(user, "is_manager", False)
            or getattr(user, "is_staff", False)
        )
        is_allowed = is_admin or (
            getattr(user, "is_contact_person_broadcast", False)
            and user.counterparties.filter(pk=nomenclature.legalEntity_id, broadcast=True).exists()
        )
        if not is_allowed:
            return Response({"detail": "Нет доступа к выбранной точке вещания."}, status=status.HTTP_403_FORBIDDEN)

        installation_id = serializer.validated_data.get("installation_id")
        with transaction.atomic():
            installation = None
            point_ids = {nomenclature.pk}
            if installation_id is not None:
                source_id = StationInstallation.objects.filter(pk=installation_id).values_list(
                    "nomenclature_id", flat=True,
                ).first()
                if source_id is None:
                    return Response({"detail": "Установка Player не найдена."}, status=status.HTTP_404_NOT_FOUND)
                point_ids.add(source_id)

            # Общий замок точки сериализует создание и перенос установок.
            # При переносе всегда блокируем точки в одном порядке, затем установку.
            locked_points = list(Nomenclature.objects.select_for_update().filter(
                pk__in=point_ids,
            ).order_by("pk"))
            if len(locked_points) != len(point_ids):
                return Response({"detail": "Точка вещания не найдена."}, status=status.HTTP_404_NOT_FOUND)
            nomenclature = next(point for point in locked_points if point.pk == nomenclature.pk)
            if not is_admin and not (
                getattr(user, "is_contact_person_broadcast", False)
                and user.counterparties.filter(pk=nomenclature.legalEntity_id, broadcast=True).exists()
            ):
                return Response({"detail": "Нет доступа к выбранной точке вещания."}, status=status.HTTP_403_FORBIDDEN)
            if installation_id is not None:
                installation = StationInstallation.objects.select_for_update().filter(pk=installation_id).first()
                if installation is None:
                    return Response({"detail": "Установка Player не найдена."}, status=status.HTTP_404_NOT_FOUND)
                if installation.nomenclature_id not in point_ids:
                    return Response(
                        {"detail": "Привязка уже изменена; повторите выбор точки.", "code": "installation_moved"},
                        status=status.HTTP_409_CONFLICT,
                    )
                if installation.created_by_id != user.pk and not is_admin:
                    return Response({"detail": "Нет доступа к этой установке Player."}, status=status.HTTP_403_FORBIDDEN)
                if not installation.is_active and not serializer.validated_data["replace_revoked"]:
                    # Старый Player с сохранённым JWT не должен автоматически
                    # отбирать точку у новой установки после своего HTTP 401.
                    return Response(
                        {"detail": "Привязка отозвана. Для восстановления выполните вход и выберите точку.",
                         "code": "installation_revoked"},
                        status=status.HTTP_409_CONFLICT,
                    )
                if installation.nomenclature_id != nomenclature.pk:
                    installation.nomenclature = nomenclature
                    installation.save(update_fields=["nomenclature"])
                token = issue_station_token(installation)
            else:
                token = generate_station_token()
                installation = StationInstallation.objects.create(
                    nomenclature=nomenclature, created_by=user,
                    token_hash=hash_station_token(token),
                )

            StationInstallation.objects.filter(
                nomenclature=nomenclature, is_active=True,
            ).exclude(pk=installation.pk).update(is_active=False)
            StationCredential.objects.filter(
                nomenclature=nomenclature, is_active=True,
            ).update(is_active=False)

        return Response(
            {
                "installation_id": str(installation.pk),
                "station_token": token,
            }, headers={"Cache-Control": "no-store"},
        )
