from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from typing import Any
from urllib.parse import urlparse, urlunparse

from src.config_loader import get_settings, get_sites

BLOCKED_SCHEMES = frozenset(
    {
        "javascript",
        "data",
        "file",
        "vbscript",
        "blob",
        "about",
        "chrome",
        "chrome-extension",
    }
)

DANGEROUS_URL_PATTERNS = (
    re.compile(r"[\x00-\x1f\x7f]"),
    re.compile(r"(?i)(javascript:|data:|file:|vbscript:)"),
)


class UrlTrust(str, Enum):
    TRUSTED = "trusted"
    UNVERIFIED = "unverified"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class UrlCheckResult:
    url: str
    trust: UrlTrust
    reason: str
    safe_for_fetch: bool
    safe_for_export: bool


def _security_cfg() -> dict[str, Any]:
    return get_settings().get("security", {})


def host_from_url(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().split(":")[0]
    except Exception:
        return ""


def domains_from_site_config(cfg: dict[str, Any]) -> set[str]:
    domains: set[str] = set()
    base = (cfg.get("base_url") or "").strip()
    if base:
        host = host_from_url(base)
        if host:
            domains.add(host)
    for catalog in cfg.get("catalog_urls") or []:
        if isinstance(catalog, str) and catalog.strip():
            host = host_from_url(catalog.strip())
            if host:
                domains.add(host)
    return domains


@lru_cache(maxsize=1)
def all_provider_domains() -> frozenset[str]:
    domains: set[str] = set()
    for cfg in get_sites().values():
        domains.update(domains_from_site_config(cfg))
    return frozenset(domains)


def host_matches_allowlist(host: str, allowed: frozenset[str] | set[str]) -> bool:
    if not host:
        return False
    host = host.lower()
    for domain in allowed:
        domain = domain.lower()
        if host == domain or host.endswith("." + domain):
            return True
    return False


def _is_private_or_local_host(host: str) -> bool:
    if not host:
        return True
    lower = host.lower()
    if lower in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        return True
    try:
        ip = ipaddress.ip_address(lower.strip("[]"))
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
    except ValueError:
        pass
    if lower.endswith(".local") or lower.endswith(".internal"):
        return True
    return False


def normalize_http_url(url: str) -> str | None:
    raw = (url or "").strip()
    if not raw:
        return None
    if not raw.startswith(("http://", "https://")):
        raw = "https://" + raw.lstrip("/")
    try:
        parsed = urlparse(raw)
    except Exception:
        return None
    if parsed.scheme.lower() not in ("http", "https"):
        return None
    if parsed.username or parsed.password:
        return None
    host = parsed.hostname
    if not host:
        return None
    path = parsed.path or "/"
    if parsed.query:
        path = f"{path}?{parsed.query}"
    return urlunparse((parsed.scheme.lower(), host.lower(), path, "", "", ""))


def check_url(
    url: str,
    *,
    allowed_domains: frozenset[str] | set[str] | None = None,
    purpose: str = "general",
) -> UrlCheckResult:
    """
    Valida URLs para scraping, almacenamiento y exportación.
    purpose: fetch | export | general
    """
    cfg = _security_cfg()
    max_len = int(cfg.get("max_url_length", 2000))
    block_private = bool(cfg.get("block_private_ips", True))
    require_https_export = bool(cfg.get("require_https_for_export", False))

    raw = (url or "").strip()
    if not raw or len(raw) > max_len:
        return UrlCheckResult(
            url=raw[:200],
            trust=UrlTrust.BLOCKED,
            reason="URL vacía o demasiado larga",
            safe_for_fetch=False,
            safe_for_export=False,
        )

    for pattern in DANGEROUS_URL_PATTERNS:
        if pattern.search(raw):
            return UrlCheckResult(
                url=raw[:200],
                trust=UrlTrust.BLOCKED,
                reason="Patrón de URL no permitido",
                safe_for_fetch=False,
                safe_for_export=False,
            )

    try:
        parsed = urlparse(raw)
    except Exception:
        return UrlCheckResult(
            url=raw[:200],
            trust=UrlTrust.BLOCKED,
            reason="URL mal formada",
            safe_for_fetch=False,
            safe_for_export=False,
        )

    scheme = (parsed.scheme or "").lower()
    if scheme in BLOCKED_SCHEMES or scheme not in ("http", "https"):
        return UrlCheckResult(
            url=raw[:200],
            trust=UrlTrust.BLOCKED,
            reason=f"Esquema no permitido: {scheme or '(vacío)'}",
            safe_for_fetch=False,
            safe_for_export=False,
        )

    host = (parsed.hostname or "").lower()
    if block_private and _is_private_or_local_host(host):
        return UrlCheckResult(
            url=raw[:200],
            trust=UrlTrust.BLOCKED,
            reason="Host local o privado no permitido",
            safe_for_fetch=False,
            safe_for_export=False,
        )

    normalized = normalize_http_url(raw)
    if not normalized:
        return UrlCheckResult(
            url=raw[:200],
            trust=UrlTrust.BLOCKED,
            reason="No se pudo normalizar la URL",
            safe_for_fetch=False,
            safe_for_export=False,
        )

    allowed = allowed_domains if allowed_domains is not None else all_provider_domains()
    trusted = host_matches_allowlist(host, allowed)

    if trusted:
        trust = UrlTrust.TRUSTED
        reason = "Dominio de proveedor configurado"
    else:
        trust = UrlTrust.UNVERIFIED
        reason = "Dominio fuera de la lista de proveedores"

    safe_fetch = trusted and trust != UrlTrust.BLOCKED
    safe_export = trust != UrlTrust.BLOCKED
    if require_https_export and purpose == "export" and scheme != "https":
        safe_export = False
        reason = f"{reason}; se requiere HTTPS para exportar"

    if purpose == "fetch" and not safe_fetch:
        safe_fetch = False

    return UrlCheckResult(
        url=normalized,
        trust=trust,
        reason=reason,
        safe_for_fetch=safe_fetch,
        safe_for_export=safe_export,
    )


def assert_safe_fetch_url(url: str, allowed_domains: set[str] | frozenset[str]) -> str:
    result = check_url(url, allowed_domains=frozenset(allowed_domains), purpose="fetch")
    if not result.safe_for_fetch:
        raise ValueError(f"URL no permitida para scraping: {result.reason} ({url})")
    return result.url


def sanitize_excel_value(value: Any) -> Any:
    """Evita inyección de fórmulas al abrir Excel (=CMD|, HYPERLINK malicioso, etc.)."""
    if value is None:
        return value
    if isinstance(value, (int, float, bool)):
        return value
    text = str(value)
    if not text:
        return text
    if text[0] in ("=", "+", "-", "@", "\t", "\r", "\n"):
        return "'" + text
    if text.startswith(("http://", "https://")):
        return text
    return text


def trust_label_es(trust: str) -> str:
    mapping = {
        UrlTrust.TRUSTED.value: "Verificada (proveedor)",
        UrlTrust.UNVERIFIED.value: "No verificada",
        UrlTrust.BLOCKED.value: "Bloqueada",
    }
    return mapping.get(trust, trust)
