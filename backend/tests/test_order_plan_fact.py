"""Daily plan matches Player cadence; facts require exact completed sessions."""

from datetime import date, datetime
from uuid import uuid4

import pytest

from files.models import Playlist
from nomenclatures.models import StationCommandV2
from nomenclatures.player_v2.playback.models import PlaybackEvent
from orders.models import Order, OrderStationState
from orders.services.order_plan_fact import report_for_order


DAY = date(2026, 10, 8)


@pytest.fixture
def scheduled(nomenclature):
    nomenclature.settings = {key: {"worktime": "09:00:00-18:00:00"}
        for key in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")}
    nomenclature.save(update_fields=["settings"])
    order = Order.objects.create(name="Plan order", placement="advertising", nomenclature=nomenclature,
        playlist=Playlist.objects.create(name="Plan playlist"), parameters={"times_in_hour": 4})
    ids = [str(uuid4()) for _ in range(3)]
    body = {"order_id": str(order.pk), "revision": 1, "placement": "advertising",
        "files": [{"id": identity, "name": f"Clip {index}"} for index, identity in enumerate(ids, 1)],
        "task": {"task_type": 4, "parameters": {"order_id": str(order.pk), "revision": 1,
            "broadcast_type": 0, "broadcast_start": "2026-10-07 09:00:00", "broadcast_end": "2026-10-10 18:00:00",
            "order_parameters": {"times_in_hour": 4}, "playlist": {"files": [{"id": identity} for identity in ids]}}}}
    command = StationCommandV2.objects.create(nomenclature=nomenclature, kind="apply_order_manifest", body=body)
    return order, command, ids


def configure(command, *, kind=0, **options):
    parameters = command.body["task"]["parameters"]
    parameters["broadcast_type"] = kind
    parameters["order_parameters"].update(options)
    command.save(update_fields=["body"])


def session(order, file_id, start, finish=None, *, terminal="completed", revision=1, include_start=True):
    playback_id = uuid4()
    common = {"nomenclature": order.nomenclature, "playback_id": playback_id, "file_id": file_id,
        "order_id": order.pk, "order_revision": revision, "media_type": "ad", "position_ms": 0,
        "duration_ms": 30000, "payload": {}}
    if include_start:
        PlaybackEvent.objects.create(**common, event_id=uuid4(), event_sequence=1,
            event_type="started", occurred_at=start)
    if finish:
        PlaybackEvent.objects.create(**common, event_id=uuid4(), event_sequence=2,
            event_type=terminal, occurred_at=finish)


@pytest.mark.django_db
@pytest.mark.parametrize("kind,options,expected", [
    (0, {}, 36), (1, {"timedelta": "00:30:00"}, 34), (2, {"timedelta": "00:30:00"}, 34),
    (1, {"timedelta": 30}, 34),
    (3, {"start_time": "06:00:00", "end_time": "08:00:00"}, 8),
    (4, {"end_time": "15:00:00"}, 24), (5, {"start_time": "14:00:00"}, 16),
])
def test_periodic_modes_count_order_exits_not_each_playlist_file(scheduled, kind, options, expected):
    order, command, ids = scheduled
    configure(command, kind=kind, **options)
    report = report_for_order(order, DAY, now=datetime(2026, 10, 9))
    assert report["plan_supported"] is True
    assert report["summary"]["planned"] == expected
    assert sum(row["planned"] for row in report["rows"]) == expected
    assert report["summary"]["due"] == expected


@pytest.mark.django_db
def test_round_robin_due_now_future_and_fractional_cadence(scheduled):
    order, command, ids = scheduled
    report = report_for_order(order, DAY, now=datetime(2026, 10, 8, 10))
    assert [row["planned"] for row in report["rows"]] == [12, 12, 12]
    assert [row["due"] for row in report["rows"]] == [2, 2, 1]
    assert report["summary"]["future"] == 31
    assert report_for_order(order, DAY, now=datetime(2026, 10, 7))["summary"]["due"] == 0
    configure(command, times_in_hour=7)
    assert report_for_order(order, DAY, now=datetime(2026, 10, 9))["summary"]["planned"] == 63


@pytest.mark.django_db
def test_order_starts_at_exact_selected_minute_and_end_is_excluded(scheduled):
    order, command, ids = scheduled
    command.body["task"]["parameters"]["broadcast_start"] = "2026-10-08 13:04:00"
    command.body["task"]["parameters"]["broadcast_end"] = "2026-10-08 14:04:00"
    command.save(update_fields=["body"])
    assert report_for_order(order, DAY, now=datetime(2026, 10, 8, 13, 3, 59))["summary"]["due"] == 0
    assert report_for_order(order, DAY, now=datetime(2026, 10, 8, 13, 4))["summary"]["due"] == 1
    assert report_for_order(order, DAY, now=datetime(2026, 10, 8, 14, 4))["summary"]["planned"] == 4


@pytest.mark.django_db
@pytest.mark.parametrize("kind,options,expected", [(0, {}, 8), (4, {"end_time": "02:00:00"}, 4),
    (5, {"start_time": "23:00:00"}, 7), (5, {"start_time": "01:00:00"}, 5)])
def test_overnight_plans_include_both_calendar_day_halves(scheduled, kind, options, expected):
    order, command, ids = scheduled
    order.nomenclature.settings["thu"]["worktime"] = "22:00:00-06:00:00"
    order.nomenclature.save(update_fields=["settings"])
    configure(command, kind=kind, times_in_hour=1, **options)
    report = report_for_order(order, DAY, now=datetime(2026, 10, 9))
    assert report["summary"]["planned"] == expected
    if kind == 0:
        assert [row["planned"] for row in report["rows"]] == [3, 3, 2]


@pytest.mark.django_db
def test_facts_use_start_day_and_exact_revision_without_partial_playbacks(scheduled):
    order, command, ids = scheduled
    start = datetime(2026, 10, 8, 23, 59)
    finish = datetime(2026, 10, 9, 0, 1)
    session(order, ids[0], start, finish)
    session(order, ids[0], datetime(2026, 10, 8, 10), datetime(2026, 10, 8, 10, 1))
    session(order, ids[0], start, finish, include_start=False)
    session(order, ids[0], start, finish, terminal="interrupted")
    session(order, ids[0], start, finish, terminal="error")
    session(order, ids[0], start, finish, revision=2)
    session(order, ids[0], start)
    report = report_for_order(order, DAY, now=datetime(2026, 10, 9))
    assert report["summary"]["completed"] == 2
    assert report_for_order(order, date(2026, 10, 9), now=finish)["summary"]["completed"] == 0


@pytest.mark.django_db
@pytest.mark.parametrize("kind", [6, 7])
def test_event_and_continuous_show_fact_without_inventing_a_plan(scheduled, kind):
    order, command, ids = scheduled
    configure(command, kind=kind)
    session(order, ids[0], datetime(2026, 10, 8, 10), datetime(2026, 10, 8, 10, 1))
    report = report_for_order(order, DAY)
    assert report["plan_supported"] is False
    assert report["summary"]["planned"] is None and report["summary"]["missing"] is None
    assert report["summary"]["completed"] == 1


@pytest.mark.django_db
@pytest.mark.parametrize("status", [0, 3])
def test_cancelled_order_keeps_last_sent_revision_in_historical_report(scheduled, status):
    order, command, ids = scheduled
    session(order, ids[0], datetime(2026, 10, 8, 10), datetime(2026, 10, 8, 10, 1))
    order.revision = 2
    order.status = status
    order.save(update_fields=["revision", "status"])
    OrderStationState.objects.create(order=order, nomenclature=order.nomenclature, desired_action="cancel", desired_revision=2)
    report = report_for_order(order, DAY, now=datetime(2026, 10, 9))
    assert report["revision"] == 1
    assert report["summary"]["planned"] == 36 and report["summary"]["completed"] == 1


@pytest.mark.django_db
def test_edited_playlist_does_not_rewrite_saved_plan_and_missing_worktime_is_explicit(scheduled, django_assert_num_queries):
    order, command, ids = scheduled
    order.parameters = {"times_in_hour": 60}
    order.playlist = Playlist.objects.create(name="Changed live playlist")
    order.save(update_fields=["parameters", "playlist"])
    with django_assert_num_queries(2):
        report = report_for_order(order, DAY, now=datetime(2026, 10, 9))
    assert report["summary"]["planned"] == 36
    assert report["rows"][0]["file_name"] == "Clip 1"
    order.nomenclature.settings = {}
    order.nomenclature.save(update_fields=["settings"])
    report = report_for_order(order, DAY)
    assert report["plan_supported"] is False and report["summary"]["planned"] is None


@pytest.mark.django_db
def test_cancelled_same_revision_discloses_that_stop_time_is_not_reconstructed(scheduled):
    order, command, ids = scheduled
    order.status = 3
    order.save(update_fields=["status"])
    report = report_for_order(order, DAY)
    assert any("остановки" in note for note in report["notes"])


@pytest.mark.django_db
def test_malformed_file_identity_returns_unknown_plan_instead_of_crashing(scheduled):
    order, command, ids = scheduled
    command.body["task"]["parameters"]["playlist"]["files"] = [{"id": "bad-id"}]
    command.save(update_fields=["body"])
    report = report_for_order(order, DAY)
    assert report["plan_supported"] is False and report["summary"]["planned"] is None
