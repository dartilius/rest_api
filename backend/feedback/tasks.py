# feedback/tasks.py
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from typing import Optional

from celery import shared_task

from rmc_rest_api.settings import EMAIL_HOST_USER, EMAIL_PORT, EMAIL_HOST_PASSWORD, EMAIL_HOST

logger = logging.getLogger('feedback')

_PATHNAME_LABELS = {
    "order": "Заказ",
    "/corporate-broadcast": "Корпоративное вещание",
    "brands": "Бренд",
    "nomenclatures": "Номенклатура",
}


def _nomenclature_display_name(nom) -> str:
    """
    Формирует название площадки для служебного письма.
    Результат: {place_name} "{brand.name}" {address_str}
    """
    if not nom.brand:
        return str(nom.id)

    address_str = nom.formatted_address
    if not address_str:
        return str(nom.id)

    place = nom.typeOfPlace
    if place:
        place_name = place.abbreviation or place.tariff_single or place.name or ""
    else:
        place_name = ""

    parts = filter(None, [place_name, f'"{nom.brand.name}"', address_str])
    return " ".join(parts)


def _resolve_names(
    pathname: Optional[str],
    brand_id: Optional[str],
    nomenclatures_ids: Optional[list[str]],
) -> tuple[Optional[str], Optional[list[str]]]:
    """
    Возвращает (brand_name, nomenclature_names).
    Делает запросы к БД только когда нужно.
    """
    brand_name: Optional[str] = None
    nom_names: Optional[list[str]] = None

    try:
        if pathname == "brands" and brand_id:
            from brands.models import Brand
            brand = Brand.objects.filter(id=brand_id).first()
            brand_name = brand.name if brand else brand_id

        elif pathname in ("order", "nomenclatures") and nomenclatures_ids:
            from nomenclatures.models import Nomenclature
            noms = (
                Nomenclature.objects
                .filter(id__in=nomenclatures_ids)
                .select_related("brand", "typeOfPlace", "address__address__city",
                                "address__address__street", "address__address__house",
                                "address__address__building")
            )
            nom_names = [_nomenclature_display_name(n) for n in noms] or nomenclatures_ids

    except Exception as e:
        logger.warning(f"[_resolve_names] Не удалось получить названия: {e}")

    return brand_name, nom_names


def _build_source_line(
    pathname: Optional[str],
    brand_name: Optional[str],
    nom_names: Optional[list[str]],
) -> str:
    """
    Формирует строку «Источник» для тела письма.

    Примеры:
      order        → Источник: Заказ | Номенклатуры: ТЦ "Nike" ул. Ленина, д. 1, ...
      brands       → Источник: Бренд | Бренд: Adidas
      nomenclatures → Источник: Номенклатура | Номенклатура: ТЦ "Puma" ул. Мира, д. 5
    """
    if not pathname:
        return ""

    label = _PATHNAME_LABELS.get(pathname, pathname)
    parts = [f"Источник: {label}"]

    if pathname in ("order", "nomenclatures") and nom_names:
        key = "Номенклатуры" if len(nom_names) > 1 else "Номенклатура"
        parts.append(f"{key}: {', '.join(nom_names)}")

    if pathname == "brands" and brand_name:
        parts.append(f"Бренд: {brand_name}")

    return " | ".join(parts)


def _corporate_lines(request_type, company, request_data, request_id):
    if request_type != "corporate_broadcast":
        return []
    from corporate_broadcast.constants import BroadcastFormat, CONTENT_LABELS
    data = request_data or {}
    lines = ["", "Тип заявки: Корпоративное вещание", f"Номер: {request_id or '-'}", f"Компания: {company or '-'}"]
    labels = {"business_type": "Тип объекта", "object_count": "Количество объектов", "area_per_object": "Площадь одного объекта, м²", "format": "Формат", "screens": "Экраны", "video_content": "Контент для экранов"}
    values = {**dict(BroadcastFormat.choices), "existing": "Уже есть", "needed": "Нужно подобрать", "own": "Собственный", "production": "Нужно производство", "consultation": "Нужна консультация", "store": "Магазин", "cafe": "Кафе", "restaurant": "Ресторан", "shopping-center": "Торговый центр", "office": "Офис", "fitness": "Фитнес", "hotel": "Отель", "other": "Другое"}
    for key, label in labels.items():
        if key in data:
            value = data[key]
            lines.append(f"{label}: {values.get(value, value)}")
    content = ", ".join(CONTENT_LABELS[key] for key, enabled in data.get("content", {}).items() if enabled and key in CONTENT_LABELS)
    if "content" in data:
        lines.append(f"Контент: {content or 'Обсудить с менеджером'}")
    return lines


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
def send_feedback_email(
    self,
    name: str,
    phone: str,
    email: str,
    message: str,
    created: str,
    pathname: Optional[str] = None,
    brand_id: Optional[str] = None,
    nomenclatures_ids: Optional[list[str]] = None,
    request_type: str = "general",
    company: str = "",
    request_data: Optional[dict] = None,
    request_id: Optional[str] = None,
) -> str:
    """Отправка уведомления админу"""
    logger.info("Feedback manager email: id=%s", request_id)
    try:
        brand_name, nom_names = _resolve_names(pathname, brand_id, nomenclatures_ids)
        source_line = _build_source_line(pathname, brand_name, nom_names)

        body_lines = [
            "Получено новое обращение:",
            "",
            f"Имя:     {name}",
            f"Телефон: {phone}",
            f"Почта:   {email}",
            f"Дата:    {created}",
        ]
        if source_line:
            body_lines.append(source_line)
        body_lines += _corporate_lines(request_type, company, request_data, request_id)
        body_lines += ["", "Сообщение:", message or ""]

        _send(
            to=EMAIL_HOST_USER,
            subject="Заявка на корпоративное вещание" if request_type == "corporate_broadcast" else "Новое обращение с сайта",
            body="\n".join(body_lines),
        )
        logger.info(f"[TASK ADMIN] ✅ Sent")
        return "Admin notification sent"
    except Exception as e:
        logger.error("Feedback manager email failed: id=%s error=%s", request_id, type(e).__name__)
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_feedback_mail(
    self,
    name: str,
    email: str,
    message: str,
    created: str,
    pathname: Optional[str] = None,
    brand_id: Optional[str] = None,
    nomenclatures_ids: Optional[list[str]] = None,
    request_type: str = "general",
    company: str = "",
    request_data: Optional[dict] = None,
    request_id: Optional[str] = None,
) -> str:
    """Отправка подтверждения пользователю"""
    logger.info("Feedback confirmation email: id=%s", request_id)
    try:
        brand_name, nom_names = _resolve_names(pathname, brand_id, nomenclatures_ids)
        source_line = _build_source_line(pathname, brand_name, nom_names)

        body_lines = [
            f"Здравствуйте, {name}!",
            "",
            "Ваша заявка на корпоративное вещание сохранена. Менеджер уточнит детали." if request_type == "corporate_broadcast" else "Ваше обращение принято. Мы свяжемся с вами в ближайшее время.",
        ]
        if source_line:
            body_lines.append(source_line)
        body_lines += _corporate_lines(request_type, company, request_data, request_id)
        body_lines += ["", "Текст вашего сообщения:", message or ""]

        _send(
            to=email,
            subject="Мы получили ваше обращение",
            body="\n".join(body_lines),
        )
        logger.info(f"[TASK USER] ✅ Sent")
        return "User confirmation sent"
    except Exception as e:
        logger.error("Feedback confirmation email failed: id=%s error=%s", request_id, type(e).__name__)
        raise self.retry(exc=e)
