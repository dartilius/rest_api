"""Order plan/fact stays in admin, with model permissions and safe rendering."""

import pytest
from django.urls import reverse

from files.models import Playlist
from orders.models import Order


@pytest.fixture
def report_order(nomenclature):
    return Order.objects.create(name="Report order", placement="advertising", nomenclature=nomenclature,
        playlist=Playlist.objects.create(name="Report playlist"), parameters={"times_in_hour": 4})


@pytest.mark.django_db
def test_report_requires_admin_login_and_order_view_permission(client, report_order, user):
    url = reverse("admin:orders_order_plan_fact", args=[report_order.pk])
    assert client.get(url).status_code == 302
    user.is_staff = True
    user.save(update_fields=["is_staff"])
    client.force_login(user)
    assert client.get(url).status_code == 403


@pytest.mark.django_db
def test_report_renders_selected_day_and_escapes_file_names(client, report_order, super_user, monkeypatch):
    observation = {"notes": ["Plan test"], "rows": [{"file_name": "<script>bad()</script>",
        "planned": 4, "due": 2, "completed": 1, "missing": 1, "future": 2, "extra": 0}],
        "summary": {"planned": 4, "due": 2, "completed": 1, "missing": 1, "future": 2, "extra": 0}}
    days = []
    def report(order, day):
        assert order.pk == report_order.pk
        days.append(day.isoformat())
        return observation
    monkeypatch.setattr("orders.services.order_plan_fact.report_for_order", report)
    client.force_login(super_user)
    response = client.get(reverse("admin:orders_order_plan_fact", args=[report_order.pk]), {"day": "2026-10-07"})
    assert response.status_code == 200
    assert days == ["2026-10-07"]
    html = response.content.decode()
    assert "&lt;script&gt;" in html and "<script>bad()" not in html
    assert "План к текущему моменту" in html and "Пока не подтверждено" in html


@pytest.mark.django_db
def test_bad_day_returns_validation_error_and_background_has_no_ad_report(client, report_order, super_user):
    client.force_login(super_user)
    url = reverse("admin:orders_order_plan_fact", args=[report_order.pk])
    assert client.get(url, {"day": "not-a-date"}).status_code == 400
    assert client.get(url, {"day": "9999-12-31"}).status_code == 400
    assert client.get(url).status_code == 200
    report_order.placement = "background"
    report_order.save(update_fields=["placement"])
    assert client.get(url).status_code == 404
