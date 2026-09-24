"""Standalone serializers for the inbound 1C nomenclature API."""

from datetime import time

from django.db import transaction
from rest_framework import serializers

from addresses.models import Address as AddressBook
from addresses.serializers import AddressCreateSerializer
from brands.models import Brand
from counterparties.models import Counterparty
from nomenclatures.models import (
    AVAILABLE_CONTENT_TYPES,
    Nomenclature,
    NomenclatureAddress,
    NomenclatureTenant,
    TypeOfPlace,
)
from nomenclatures.services.indexing import suppress_tenant_indexing
from nomenclatures.services.naming import build_nomenclature_web_name
from users.models import CustomUser


class Nomenclature1CTenantListSerializer(serializers.ListSerializer):
    """Validate tenant UUIDs in one query before replacing the relation."""

    def validate(self, data):
        tenant_ids = {item["id"] for item in data}
        existing_ids = set(
            Counterparty.objects.filter(id__in=tenant_ids).values_list("id", flat=True)
        )
        missing_ids = tenant_ids - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                {"id": f"Арендатор с id {next(iter(missing_ids))} не найден"}
            )
        return data


class Nomenclature1CTenantWriteSerializer(serializers.Serializer):
    """Writable tenant relation used only by the 1C API contract."""

    id = serializers.UUIDField()
    floor = serializers.CharField(required=False, allow_blank=True)
    atm = serializers.BooleanField(required=False, default=False)
    brand = serializers.PrimaryKeyRelatedField(
        queryset=Brand.objects.all(),
        required=False,
        allow_null=True,
    )

    class Meta:
        list_serializer_class = Nomenclature1CTenantListSerializer


class Nomenclature1CTenantReadSerializer(serializers.ModelSerializer):
    """Flat representation of a nomenclature tenant relation for 1C."""

    id = serializers.UUIDField(source="tenant_id", read_only=True)
    brand = serializers.UUIDField(source="brand_id", read_only=True, allow_null=True)

    class Meta:
        model = NomenclatureTenant
        fields = ("id", "floor", "atm", "brand")
        read_only_fields = fields


class Nomenclature1CReadSerializer(serializers.ModelSerializer):
    """Flat, read-only nomenclature representation returned to 1C."""

    owner_id = serializers.UUIDField(read_only=True, allow_null=True)
    responsible_radio_id = serializers.UUIDField(read_only=True, allow_null=True)
    responsible_ad_id = serializers.UUIDField(read_only=True, allow_null=True)
    responsible_technic_id = serializers.UUIDField(read_only=True, allow_null=True)
    responsible_technic_on_address_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
    )
    responsible_placement_marketing_id = serializers.UUIDField(
        read_only=True,
        allow_null=True,
    )
    brand_id = serializers.UUIDField(read_only=True, allow_null=True)
    legalEntity_id = serializers.UUIDField(read_only=True, allow_null=True)
    typeOfPlace_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = Nomenclature
        fields = (
            "id",
            "owner_id",
            "name",
            "is_active",
            "created",
            "for_web",
            "broadcast",
            "slots_per_hour",
            "external_video_media",
            "external_audio_media",
            "internal_video_media",
            "internal_audio_media",
            "worktime_start",
            "worktime_end",
            "id_rasb",
            "square",
            "possibility",
            "article",
            "description",
            "responsible_radio_id",
            "responsible_ad_id",
            "responsible_technic_id",
            "responsible_technic_on_address_id",
            "responsible_placement_marketing_id",
            "timezone",
            "code1c",
            "version",
            "settings",
            "applied_settings_revision",
            "station_capabilities",
            "visual_output_settings",
            "hw_info",
            "runtime_state",
            "brand_id",
            "legalEntity_id",
            "contentType",
            "typeOfPlace_id",
            "pricePerMonth",
            "old_catalog_slug",
        )
        read_only_fields = fields

class Nomenclature1CWriteSerializer(serializers.ModelSerializer):
    """Independent write contract for 1C; every input field is optional."""

    name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    code1c = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    contentType = serializers.ChoiceField(
        choices=list(AVAILABLE_CONTENT_TYPES.keys()),
        required=False,
    )
    worktime_start = serializers.TimeField(format="%H:%M", required=False, allow_null=True)
    worktime_end = serializers.TimeField(format="%H:%M", required=False, allow_null=True)
    typeOfPlace_id = serializers.PrimaryKeyRelatedField(
        source="typeOfPlace",
        queryset=TypeOfPlace.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    legalEntity_id = serializers.PrimaryKeyRelatedField(
        source="legalEntity",
        queryset=Counterparty.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    brand_id = serializers.PrimaryKeyRelatedField(
        source="brand",
        queryset=Brand.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    responsible_radio_id = serializers.PrimaryKeyRelatedField(
        source="responsible_radio",
        queryset=CustomUser.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    responsible_ad_id = serializers.PrimaryKeyRelatedField(
        source="responsible_ad",
        queryset=CustomUser.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    responsible_technic_id = serializers.PrimaryKeyRelatedField(
        source="responsible_technic",
        queryset=CustomUser.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    responsible_technic_on_address_id = serializers.PrimaryKeyRelatedField(
        source="responsible_technic_on_address",
        queryset=CustomUser.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    responsible_placement_marketing_id = serializers.PrimaryKeyRelatedField(
        source="responsible_placement_marketing",
        queryset=CustomUser.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Nomenclature
        fields = (
            "name",
            "is_active",
            "for_web",
            "broadcast",
            "slots_per_hour",
            "external_video_media",
            "external_audio_media",
            "internal_video_media",
            "internal_audio_media",
            "worktime_start",
            "worktime_end",
            "id_rasb",
            "square",
            "possibility",
            "description",
            "timezone",
            "code1c",
            "settings",
            "contentType",
            "pricePerMonth",
            "typeOfPlace_id",
            "legalEntity_id",
            "brand_id",
            "responsible_radio_id",
            "responsible_ad_id",
            "responsible_technic_id",
            "responsible_technic_on_address_id",
            "responsible_placement_marketing_id",
        )
        extra_kwargs = {
            field: {"required": False}
            for field in (
                "is_active",
                "for_web",
                "broadcast",
                "slots_per_hour",
                "external_video_media",
                "external_audio_media",
                "internal_video_media",
                "internal_audio_media",
                "worktime_start",
                "worktime_end",
                "id_rasb",
                "square",
                "possibility",
                "description",
                "timezone",
                "settings",
                "pricePerMonth",
            )
        }

    def validate(self, attrs):
        if "address_data" in attrs and "address_id" in attrs:
            raise serializers.ValidationError(
                "Передайте либо address_data, либо address_id."
            )
        return attrs

    def validate_code1c(self, value):
        if not value:
            return None
        queryset = Nomenclature.objects.filter(code1c=value)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError(
                "Номенклатура с таким кодом 1С уже существует."
            )
        return value

    def validate_pricePerMonth(self, value):
        if value < 0:
            raise serializers.ValidationError("Стоимость не может быть меньше 0.")
        return value

    def validate_settings(self, value):
        """Keep the broadcast settings validation local to the 1C contract."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Настройки должны быть объектом JSON.")

        def validate_interval(interval):
            if not isinstance(interval, str):
                raise serializers.ValidationError("Интервал времени должен быть строкой.")
            parts = interval.split("-")
            if len(parts) != 2:
                raise serializers.ValidationError("Интервал должен иметь формат HH:MM-HH:MM.")
            try:
                start = time(*map(int, parts[0].split(":")))
                end = time(*map(int, parts[1].split(":")))
            except (TypeError, ValueError):
                raise serializers.ValidationError(
                    "Интервал должен иметь формат HH:MM-HH:MM."
                )
            if not time.min <= start < end <= time(23, 59, 59):
                raise serializers.ValidationError("Некорректный интервал времени.")

        def validate_volume(volume):
            if not isinstance(volume, (list, tuple)) or len(volume) != 4:
                raise serializers.ValidationError(
                    "Громкость должна содержать ровно четыре значения."
                )
            if not all(isinstance(item, int) and 0 <= item <= 100 for item in volume):
                raise serializers.ValidationError(
                    "Значения громкости должны быть целыми числами от 0 до 100."
                )

        for day_settings in value.values():
            if not isinstance(day_settings, dict):
                raise serializers.ValidationError("Настройки дня должны быть объектом JSON.")
            try:
                validate_interval(day_settings["worktime"])
                validate_volume(day_settings["default_volume"])
            except KeyError as error:
                raise serializers.ValidationError(f"{error} не передан.")

            custom_volume = day_settings.get("custom_volume", {})
            if not isinstance(custom_volume, dict):
                raise serializers.ValidationError("custom_volume должен быть объектом JSON.")
            intervals = []
            for interval, volume in custom_volume.items():
                validate_interval(interval)
                validate_volume(volume)
                start = time(*map(int, interval.split("-")[0].split(":")))
                end = time(*map(int, interval.split("-")[1].split(":")))
                intervals.append((start, end))
            sorted_intervals = sorted(intervals)
            for (_, previous_end), (next_start, _) in zip(
                sorted_intervals,
                sorted_intervals[1:],
            ):
                if previous_end > next_start:
                    raise serializers.ValidationError(
                        "Интервалы custom_volume не должны пересекаться."
                    )
        return value

    @transaction.atomic
    def create(self, validated_data):
        generate_name = not (validated_data.get("name") or "").strip()
        if generate_name:
            validated_data["name"] = "Номенклатура"
        validated_data.setdefault("code1c", None)

        nomenclature = Nomenclature.objects.create(**validated_data)

        if generate_name:
            nomenclature.name = f"Номенклатура {nomenclature.id}"
            nomenclature.name = build_nomenclature_web_name(nomenclature)[:255]
            nomenclature.save(update_fields=["name"])
        return nomenclature

    @transaction.atomic
    def update(self, instance, validated_data):
        for attribute, value in validated_data.items():
            setattr(instance, attribute, value)
        if validated_data:
            instance.save()
        return instance

    def _set_address(self, instance, address_data, address):
        if address is not serializers.empty:
            NomenclatureAddress.objects.update_or_create(
                nomenclature=instance,
                defaults={"address": address},
            )
            return
        if address_data is serializers.empty:
            return
        if address_data is None:
            NomenclatureAddress.objects.update_or_create(
                nomenclature=instance,
                defaults={"address": None},
            )
            return

        address_serializer = AddressCreateSerializer(data=address_data)
        address_serializer.is_valid(raise_exception=True)
        NomenclatureAddress.objects.update_or_create(
            nomenclature=instance,
            defaults={"address": address_serializer.save()},
        )

    def _replace_tenants(self, instance, tenants_data):
        tenant_ids = {item["id"] for item in tenants_data or []}
        counterparties = Counterparty.objects.in_bulk(tenant_ids)
        rows = []
        seen = set()
        for data in tenants_data or []:
            tenant = counterparties[data["id"]]
            brand = data.get("brand")
            key = (
                tenant.id,
                brand.id if brand else None,
                data.get("floor", ""),
                data.get("atm", False),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                NomenclatureTenant(
                    nomenclature=instance,
                    tenant=tenant,
                    brand=brand,
                    floor=data.get("floor", ""),
                    atm=data.get("atm", False),
                )
            )

        with suppress_tenant_indexing(instance.id):
            NomenclatureTenant.objects.filter(nomenclature=instance).delete()
            if rows:
                NomenclatureTenant.objects.bulk_create(rows, batch_size=100)
