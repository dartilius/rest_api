"""Shared validation rules for privacy-safe marketing attribution."""

import re


ATTRIBUTION_TOUCH_FIELDS = {
    "landing_path",
    "referrer_host",
    "utm_source",
    "utm_medium",
    "utm_campaign",
}

_HOST_RE = re.compile(r"^[A-Za-z0-9.-]+(?::[0-9]{1,5})?$")
_PHONE_LIKE_RE = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d)")


def validate_attribution_payload(value):
    """Validate the small, allow-listed attribution payload stored by the API."""
    if not isinstance(value, dict):
        raise ValueError("Attribution must be an object.")

    required_keys = {"version", "first_touch", "last_touch"}
    if set(value) != required_keys:
        raise ValueError(
            "Attribution must contain only version, first_touch and last_touch."
        )
    if value["version"] != 1 or isinstance(value["version"], bool):
        raise ValueError("Only attribution version 1 is supported.")

    for touch_name in ("first_touch", "last_touch"):
        touch = value[touch_name]
        if not isinstance(touch, dict):
            raise ValueError(f"{touch_name} must be an object.")
        unknown_fields = set(touch) - ATTRIBUTION_TOUCH_FIELDS
        if unknown_fields:
            raise ValueError(
                f"Unsupported attribution fields: {', '.join(sorted(unknown_fields))}."
            )

        for field, raw_value in touch.items():
            if not isinstance(raw_value, str) or not raw_value.strip():
                raise ValueError(f"{touch_name}.{field} must be a non-empty string.")
            if len(raw_value) > 255:
                raise ValueError(f"{touch_name}.{field} must not exceed 255 characters.")
            if "@" in raw_value or _PHONE_LIKE_RE.search(raw_value):
                raise ValueError(
                    f"{touch_name}.{field} must not contain contact information."
                )

            if field == "landing_path":
                if (
                    not raw_value.startswith("/")
                    or "?" in raw_value
                    or "#" in raw_value
                    or "://" in raw_value
                ):
                    raise ValueError(
                        f"{touch_name}.landing_path must be a path without query parameters."
                    )
            elif field == "referrer_host" and not _HOST_RE.fullmatch(raw_value):
                raise ValueError(
                    f"{touch_name}.referrer_host must be a hostname, not a full URL."
                )
            elif field.startswith("utm_") and any(
                marker in raw_value for marker in ("?", "&", "=")
            ):
                raise ValueError(
                    f"{touch_name}.{field} contains unsupported tracking or contact data."
                )

    return value
