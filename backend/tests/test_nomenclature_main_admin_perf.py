import json
from datetime import UTC, datetime
from html.parser import HTMLParser
from unittest.mock import Mock

import pytest
from django.contrib.admin.sites import site
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.test import RequestFactory
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from brands.models import Brand
from counterparties.models import Counterparty
from nomenclatures.admin import StationInstallationInline
from nomenclatures.models import Nomenclature, NomenclatureTenant, StationInstallation


def admin_request(user, path="/admin/nomenclatures/nomenclature/", data=None):
    request = RequestFactory().get(path, data=data)
    request.user = user
    return request


@pytest.mark.django_db
@pytest.mark.parametrize("active_filter", [None, "1", "0"])
def test_station_changelist_includes_inactive_unless_explicitly_filtered(
    nomenclature, nomenclature_1, super_user, active_filter
):
    Nomenclature.objects.filter(pk=nomenclature.pk).update(is_active=True)
    Nomenclature.objects.filter(pk=nomenclature_1.pk).update(is_active=False)
    parameters = {} if active_filter is None else {"is_active__exact": active_filter}
    model_admin = site._registry[Nomenclature]
    changelist = model_admin.get_changelist_instance(admin_request(super_user, data=parameters))

    actual_ids = set(changelist.queryset.values_list("pk", flat=True))
    expected_ids = {
        None: {nomenclature.pk, nomenclature_1.pk},
        "1": {nomenclature.pk},
        "0": {nomenclature_1.pk},
    }
    assert actual_ids == expected_ids[active_filter]
    assert changelist.result_count == len(expected_ids[active_filter])


@pytest.mark.django_db
def test_inactive_station_change_form_is_accessible(client, super_user, nomenclature):
    Nomenclature.objects.filter(pk=nomenclature.pk).update(is_active=False)
    client.force_login(super_user)

    response = client.get(reverse("admin:nomenclatures_nomenclature_change", args=[nomenclature.pk]))

    assert response.status_code == 200
    assert response.context["original"].pk == nomenclature.pk
    assert response.context["original"].is_active is False


@pytest.mark.django_db
def test_station_list_renders_relations_and_distinct_tenant_count_in_two_queries(
    nomenclature, nomenclature_1, super_user
):
    legal_entity = Counterparty.objects.create(keyword="Legal entity")
    brand = Brand.objects.create(name="Brand")
    legal_entity.brands.add(brand)
    Nomenclature.objects.filter(pk__in=[nomenclature.pk, nomenclature_1.pk]).update(
        legalEntity=legal_entity, brand=brand
    )
    # Several placements for one tenant must still count as one tenant.
    NomenclatureTenant.objects.create(nomenclature=nomenclature, tenant=legal_entity, floor="1")
    NomenclatureTenant.objects.create(nomenclature=nomenclature, tenant=legal_entity, floor="2")
    model_admin = site._registry[Nomenclature]
    request = admin_request(super_user)

    with CaptureQueriesContext(connection) as queries:
        rows = list(model_admin.get_queryset(request).order_by("name"))
        rendered = [
            (model_admin.owner_name(row), model_admin.status_display(row),
             model_admin.brand_name(row), model_admin.legal_entity_name(row),
             model_admin.tenants_count_display(row))
            for row in rows
        ]

    assert len(queries) == 2
    assert [row.tenants_count for row in rows] == [1, 0]
    assert all("Legal entity" in fields[3] and "Brand" in fields[3] for fields in rendered)


@pytest.mark.django_db
def test_station_object_loads_editable_fields_without_deferred_queries(
    nomenclature, super_user
):
    model_admin = site._registry[Nomenclature]
    with CaptureQueriesContext(connection) as queries:
        obj = model_admin.get_object(admin_request(super_user), str(nomenclature.pk))
        values = {
            field.attname: getattr(obj, field.attname)
            for field in obj._meta.concrete_fields
        }
    assert len(queries) == 1
    assert values["settings"] == nomenclature.settings
    assert not obj.get_deferred_fields()


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.nested = False
        self.forms = {}
        self.controls = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.nested |= self.depth > 0
            self.depth += 1
            self.forms[attrs.get("id")] = attrs
        if attrs.get("name") in {"enabled", "reason"}:
            self.controls[attrs["name"]] = attrs

    def handle_endtag(self, tag):
        if tag == "form":
            self.depth -= 1


@pytest.mark.django_db
def test_station_change_form_uses_lazy_responsible_widgets_and_separate_command_form(
    client, super_user, nomenclature
):
    client.force_login(super_user)
    response = client.get(reverse("admin:nomenclatures_nomenclature_change", args=[nomenclature.pk]))
    assert response.status_code == 200
    for field in ("responsible_radio", "responsible_ad", "responsible_technic",
                  "responsible_technic_on_address", "responsible_placement_marketing"):
        assert "admin-autocomplete" in str(response.context["adminform"].form[field])
    parser = FormParser()
    parser.feed(response.content.decode())
    assert not parser.nested
    assert parser.forms["maintenance-command-form"]["action"] == reverse(
        "admin:nomenclature_maintenance", args=[nomenclature.pk]
    )
    assert all(attrs["form"] == "maintenance-command-form" for attrs in parser.controls.values())
    assert set(parser.controls) == {"enabled", "reason"}


@pytest.mark.django_db
@pytest.mark.parametrize("same_user", [True, False], ids=["same-user", "different-users"])
def test_station_change_form_loads_selected_responsible_users_once(
    django_user_model, nomenclature, same_user, super_user
):
    users = [super_user]
    for index in range(1, 5):
        users.append(
            django_user_model.objects.create_user(
                email=f"responsible-{index}@example.test",
                phone_number=f"+78005550{index:03d}",
                password="test",
                first_name=f"First {index}",
                last_name=f"Last {index}",
            )
        )
    assigned_users = [users[0]] * 5 if same_user else users
    Nomenclature.objects.filter(pk=nomenclature.pk).update(
        responsible_radio=assigned_users[0],
        responsible_ad=assigned_users[1],
        responsible_technic=assigned_users[2],
        responsible_technic_on_address=assigned_users[3],
        responsible_placement_marketing=assigned_users[4],
    )
    nomenclature.refresh_from_db()
    model_admin = site._registry[Nomenclature]

    with CaptureQueriesContext(connection) as queries:
        form = model_admin.get_form(admin_request(super_user), nomenclature)(instance=nomenclature)
        rendered = [
            str(form[field_name])
            for field_name in model_admin.responsible_fields
        ]

    user_queries = [
        query["sql"] for query in queries if 'FROM "custom_user"' in query["sql"]
    ]
    assert len(user_queries) == 1
    assert all(
        str(user) in field_html for user, field_html in zip(assigned_users, rendered)
    )


@pytest.mark.django_db
def test_installation_inline_does_not_query_users_per_row(nomenclature, super_user):
    for token_hash in ("a" * 64, "b" * 64):
        StationInstallation.objects.create(
            nomenclature=nomenclature, created_by=super_user, token_hash=token_hash
        )
    inline = StationInstallationInline(Nomenclature, site)
    with CaptureQueriesContext(connection) as queries:
        labels = [str(row.created_by) for row in inline.get_queryset(admin_request(super_user))]
    assert len(labels) == 2
    assert len(queries) == 1


@pytest.mark.django_db
@pytest.mark.parametrize("date_from,date_to", [
    ("2026-02-30", "2026-03-01"),
    ("2026-10-01", "2026-09-01"),
    ("invalid", "2026-09-01"),
])
def test_music_stat_rejects_invalid_date_ranges(nomenclature, super_user, date_from, date_to):
    response = site._registry[Nomenclature].music_stat_view(
        admin_request(super_user, data={"date_from": date_from, "date_to": date_to}),
        nomenclature.pk,
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_music_stat_requires_station_view_permission(nomenclature, user):
    with pytest.raises(PermissionDenied):
        site._registry[Nomenclature].music_stat_view(admin_request(user), nomenclature.pk)


@pytest.mark.django_db
def test_music_stat_converts_utc_to_krasnoyarsk(nomenclature, super_user, monkeypatch):
    # ClickHouse is an external statistics store; keep the response test independent
    # of its schema/bootstrap while running the real admin and PostgreSQL objects.
    query = Mock()
    query.order_by.return_value = query
    query.values.return_value = [{
        "file": "test-file", "played": datetime(2026, 9, 30, 20, tzinfo=UTC), "length": 123,
    }]
    monkeypatch.setattr("nomenclatures.admin.MusicStat.objects.filter", lambda **kwargs: query)
    response = site._registry[Nomenclature].music_stat_view(
        admin_request(super_user, data={"date_from": "2026-09-30", "date_to": "2026-09-30"}),
        nomenclature.pk,
    )
    assert json.loads(response.content) == {"count": 1, "results": [{
        "file": "test-file", "played": "2026-09-30 20:00:00",
        "played_krasnoyarsk": "2026-10-01 03:00:00", "length": 123,
    }]}


@pytest.mark.django_db
def test_station_autocomplete_returns_names_without_loading_display_relations(
    client, super_user, nomenclature
):
    client.force_login(super_user)
    with CaptureQueriesContext(connection) as queries:
        response = client.get(reverse("admin:autocomplete"), {
            "app_label": "nomenclatures", "model_name": "nomenclatureaddress",
            "field_name": "nomenclature", "term": "Test Nomenclature",
        })
    assert response.status_code == 200
    assert response.json()["results"][0]["text"] == nomenclature.name
    assert not any('"discount_rule"' in q["sql"] or '"nomenclature_tenant"' in q["sql"] for q in queries)
