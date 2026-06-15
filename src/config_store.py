from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.config_loader import CONFIG_DIR, get_sites, load_yaml

SITES_DIR = CONFIG_DIR / "sites"
SCRAPER_OPTIONS = ("tiendanube", "shopify", "woocommerce", "configurable")


def _sites_path(country: str) -> Path:
    code = country.upper()
    if code not in ("AR", "CL"):
        raise ValueError("country debe ser AR o CL")
    return SITES_DIR / f"{code.lower()}.yaml"


def _dump_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def find_site_file(slug: str) -> Path | None:
    for path in sorted(SITES_DIR.glob("*.yaml")):
        data = load_yaml(path)
        if slug in data.get("sites", {}):
            return path
    return None


def list_sites_enriched() -> list[dict[str, Any]]:
    items = []
    for slug, cfg in get_sites().items():
        items.append(
            {
                "slug": slug,
                "config_file": str(find_site_file(slug) or ""),
                **cfg,
            }
        )
    return sorted(items, key=lambda x: (x.get("country", ""), x.get("slug", "")))


def save_site(slug: str, config: dict[str, Any]) -> None:
    slug = slug.strip().replace(" ", "_").lower()
    if not slug:
        raise ValueError("El slug no puede estar vacío")

    country = str(config.get("country", "AR")).upper()
    path = _sites_path(country)
    data = load_yaml(path)
    sites = data.setdefault("sites", {})

    old_path = find_site_file(slug)
    if old_path and old_path != path:
        old_data = load_yaml(old_path)
        if slug in old_data.get("sites", {}):
            del old_data["sites"][slug]
            _dump_yaml(old_path, old_data)

    sites[slug] = _build_site_config(config)
    _dump_yaml(path, data)


def delete_site(slug: str) -> None:
    path = find_site_file(slug)
    if not path:
        raise KeyError(f"Sitio no encontrado: {slug}")
    data = load_yaml(path)
    del data["sites"][slug]
    _dump_yaml(path, data)


def _build_site_config(raw: dict[str, Any]) -> dict[str, Any]:
    catalog = raw.get("catalog_urls", [])
    if isinstance(catalog, str):
        catalog = [u.strip() for u in catalog.splitlines() if u.strip()]

    cfg: dict[str, Any] = {
        "enabled": bool(raw.get("enabled", True)),
        "country": str(raw.get("country", "AR")).upper(),
        "name": str(raw.get("name", "")).strip(),
        "base_url": str(raw.get("base_url", "")).strip().rstrip("/"),
        "currency": str(raw.get("currency", "ARS" if raw.get("country") == "AR" else "CLP")),
        "scraper": str(raw.get("scraper", "tiendanube")),
        "catalog_urls": catalog,
        "product_link_pattern": str(raw.get("product_link_pattern", "/productos/")),
        "delay_seconds": float(raw.get("delay_seconds", 2.0)),
    }
    if raw.get("notes"):
        cfg["notes"] = str(raw["notes"]).strip()
    if cfg["scraper"] == "configurable" and raw.get("selectors"):
        cfg["selectors"] = raw["selectors"]
    return cfg
