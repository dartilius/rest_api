"""JWT-защищённая привязка Player к выбранной пользователем точке."""

from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from nomenclatures.models import Nomenclature, StationInstallation
from nomenclatures.station_credentials import generate_station_token, hash_station_token, issue_station_token
from nomenclatures.station_v2_serializers import StationV2BindingRequestSerializer


class StationV2BindingView(APIView):
    permission_classes = [IsAuthenticated]

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
            if installation_id is None:
                token = generate_station_token()
                installation = StationInstallation.objects.create(
                    nomenclature=nomenclature,
                    created_by=user,
                    token_hash=hash_station_token(token),
                )
            else:
                try:
                    installation = StationInstallation.objects.select_for_update().get(
                        pk=installation_id
                    )
                except StationInstallation.DoesNotExist:
                    return Response(
                        {"detail": "Установка Player не найдена."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                if installation.created_by_id != user.pk and not is_admin:
                    return Response(
                        {"detail": "Нет доступа к этой установке Player."},
                        status=status.HTTP_403_FORBIDDEN,
                    )
                if installation.nomenclature_id != nomenclature.pk:
                    installation.nomenclature = nomenclature
                    installation.save(update_fields=["nomenclature"])
                token = issue_station_token(installation)

        return Response(
            {
                "installation_id": str(installation.pk),
                "station_token": token,
            }
        )
