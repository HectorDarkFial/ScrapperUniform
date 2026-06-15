from __future__ import annotations

import json
from typing import Any

from src.config_loader import get_settings, get_sites
from src.utils.url_security import UrlTrust, all_provider_domains, check_url, domains_from_site_config


def _security_export_rules() -> dict[str, Any]:
    return get_settings().get("security", {})


def _parse_raw_attributes(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _allowed_domains_for_row(row: dict[str, Any]) -> frozenset[str]:
    source = (row.get("source") or "").strip()
    sites = get_sites()
    if source in sites:
        return frozenset(domains_from_site_config(sites[source]))
    return all_provider_domains()


def row_is_safe_for_export(row: dict[str, Any]) -> bool:
    name = (row.get("name") or "").strip()
    url = (row.get("product_url") or "").strip()
    source = (row.get("source") or "").strip()
    if not (name and url and source):
        return False
    has_price_or_stock = (
        row.get("price") is not None
        or row.get("price_list") is not None
        or bool((row.get("price_display") or "").strip())
        or (row.get("availability") or "unknown").lower() not in ("unknown", "")
    )
    if not has_price_or_stock:
        return False

    attrs = _parse_raw_attributes(row.get("raw_attributes"))
    if attrs.get("url_trust") == UrlTrust.TRUSTED.value:
        return True

    check = check_url(url, allowed_domains=_allowed_domains_for_row(row), purpose="export")
    sec = _security_export_rules()
    if not check.safe_for_export or check.trust == UrlTrust.BLOCKED:
        return False
    if sec.get("export_only_trusted_urls") and check.trust != UrlTrust.TRUSTED:
        return False
    if sec.get("block_unverified_in_export", True) and check.trust == UrlTrust.UNVERIFIED:
        return False
    return True


def filter_rows_for_export(rows: list[dict]) -> list[dict]:
    return [r for r in rows if row_is_safe_for_export(r)]
