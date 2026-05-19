import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from typing import Optional

from celery import shared_task

from rmc_rest_api.settings import EMAIL_HOST_USER, EMAIL_PORT, EMAIL_HOST_PASSWORD, EMAIL_HOST

logger = logging.getLogger('placement_order')


def _send(to: str, subject: str, body: str) -> None:
    msg = MIMEMultipart()
    msg["From"] = f"RMC <{EMAIL_HOST_USER}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="krasrm.com")
    msg.attach(MIMEText(body, "plain", "utf-8"))

    with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        s.sendmail(EMAIL_HOST_USER, to, msg.as_string())


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_placement_order_email(
    self,
    order_id: str,
) -> str:
    logger.info(f"[TASK] Отправка письма по заказу {order_id}")
    try:
        from placement_order.models import PlacementOrder

        order = (
            PlacementOrder.objects
            .select_related("owner")
            .prefetch_related(
                "items__nomenclature__brand",
                "items__nomenclature__typeOfPlace",
                "items__nomenclature__address__address__city",
                "items__nomenclature__address__address__street",
                "items__nomenclature__address__address__house",
                "items__nomenclature__address__address__building",
                "items__responsible",
            )
            .get(id=order_id)
        )

        owner = order.owner
        owner_name = f"{owner.first_name or ''} {owner.email}".strip()

        # даты
        start = order.start_date.strftime("%d.%m.%Y") if order.start_date else "—"
        end = order.end_date.strftime("%d.%m.%Y") if order.end_date else "—"

        # дни размещения
        if order.all_days:
            days_line = "Все дни недели"
        else:
            days_map = {
                "mon": "Пн", "tue": "Вт", "wed": "Ср",
                "thu": "Чт", "fri": "Пт", "sat": "Сб", "sun": "Вс",
            }
            days_line = ", ".join(days_map.get(d, d) for d in order.days_of_week)

        # места
        items_lines = []
        total_price = 0

        for item in order.items.all():
            nom = item.nomenclature

            place = nom.typeOfPlace
            place_name = ""
            if place:
                place_name = place.abbreviation or place.tariff_single or place.name or ""

            brand_name = nom.brand.name if nom.brand else "—"
            address = nom.formatted_address or "—"
            price = getattr(nom, "price", 0) or 0
            total_price += price

            responsible = item.responsible
            responsible_name = f"{responsible.first_name} {responsible.email}".strip() if responsible else "—"

            items_lines.append(
                f"  • {place_name} «{brand_name}» {address}\n"
                f"    Ответственный: {responsible_name} | Цена: {price:,} ₽/день".replace(",", " ")
            )

        items_block = "\n".join(items_lines) or "  —"
        final_price = total_price * order.duration

        body = "\n".join([
            "Новая заявка на размещение ролика",
            "=" * 40,
            "",
            f"Отправитель:    {owner_name} ({owner.email})",
            f"Дата начала:    {start}",
            f"Дата окончания: {end}",
            f"Кол-во дней:    {order.duration}",
            f"Дни размещения: {days_line}",
            "",
            "Места размещения:",
            items_block,
            "",
            f"Итоговая сумма: {final_price:,} ₽".replace(",", " "),
            "",
            f"ID заказа: {order.id}",
        ])

        _send(
            to=EMAIL_HOST_USER,
            subject=f"Новая заявка на размещение — {owner_name}",
            body=body,
        )

        logger.info(f"[TASK] ✅ Письмо отправлено по заказу {order_id}")
        return f"Письмо отправлено: {order_id}"

    except Exception as e:
        logger.error(f"[TASK] ❌ Ошибка: {e}")
        raise self.retry(exc=e)