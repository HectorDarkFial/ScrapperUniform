from __future__ import annotations

from typing import Any

from src.models import ProductRecord
from src.utils.url_security import UrlTrust, check_url, domains_from_site_config


def apply_url_security(record: ProductRecord, site_cfg: dict[str, Any]) -> bool:
    """
    Normaliza y etiqueta URLs del producto. Devuelve False si debe descartarse.
    """
    allowed = frozenset(domains_from_site_config(site_cfg))
    attrs = dict(record.raw_attributes or {})

    product_check = check_url(
        record.product_url,
        allowed_domains=allowed,
        purpose="general",
    )
    if product_check.trust == UrlTrust.BLOCKED:
        return False

    record.product_url = product_check.url
    attrs["url_trust"] = product_check.trust.value
    attrs["url_trust_reason"] = product_check.reason

    if record.image_url:
        image_check = check_url(record.image_url, allowed_domains=allowed, purpose="general")
        if image_check.trust == UrlTrust.BLOCKED:
            record.image_url = None
            attrs["image_url_trust"] = UrlTrust.BLOCKED.value
        else:
            record.image_url = image_check.url
            attrs["image_url_trust"] = image_check.trust.value

    record.raw_attributes = attrs
    return True
