"""Подтверждение первого выхода применённой версии заказа."""

from collections import defaultdict

from django.db.models import Exists, F, OuterRef

from nomenclatures.player_v2.playback.models import PlaybackEvent
from orders.models import Order, OrderStationState


def confirm_on_air_revisions(order_ids):
    """Факт запуска подтверждает версию и переводит ожидающий заказ в эфир."""
    starts = PlaybackEvent.objects.filter(
        order_id=OuterRef("order_id"), nomenclature_id=OuterRef("nomenclature_id"),
        order_revision=OuterRef("desired_revision"), event_type="started", event_sequence=1,
    )
    confirmed = OrderStationState.objects.filter(
        order_id__in=order_ids, desired_action="apply", status="applied",
        applied_revision=F("desired_revision"), order__revision=F("desired_revision"),
    ).annotate(has_started=Exists(starts)).filter(has_started=True)
    confirmed.exclude(
        on_air_revision=F("applied_revision"),
    ).update(on_air_revision=F("applied_revision"))
    # Подтверждаем первый выход конкретной версии. Одновременное изменение
    # или отмена заказа не должны подтверждаться событием прежней версии.
    revisions = defaultdict(list)
    for order_id, revision in confirmed.values_list("order_id", "applied_revision"):
        revisions[revision].append(order_id)
    for revision, identifiers in revisions.items():
        Order.objects.filter(
            pk__in=identifiers, revision=revision, is_active=True, status=0,
            station_state__desired_action="apply",
            station_state__desired_revision=revision,
            station_state__applied_revision=revision,
            station_state__status="applied",
        ).update(status=1)
