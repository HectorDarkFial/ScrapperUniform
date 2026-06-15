from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.config_loader import get_sites


def _load_site_directory() -> dict[str, dict[str, Any]]:
    """slug -> {name, country, slug}."""
    directory: dict[str, dict[str, Any]] = {}
    for slug, cfg in get_sites().items():
        directory[slug] = {
            "slug": slug,
            "name": (cfg.get("name") or slug).strip(),
            "country": cfg.get("country"),
        }
    try:
        from portal.models import Site

        for site in Site.objects.all():
            directory[site.slug] = {
                "slug": site.slug,
                "name": site.name.strip(),
                "country": site.country,
            }
    except Exception:
        pass
    return directory


@lru_cache(maxsize=1)
def _alias_to_slug() -> dict[str, str]:
    """Mapea slug, nombre visible y variantes → slug canónico."""
    mapping: dict[str, str] = {}
    for slug, meta in _load_site_directory().items():
        mapping[slug] = slug
        mapping[slug.lower()] = slug
        name = meta["name"]
        if name:
            mapping[name] = slug
            mapping[name.lower()] = slug
            mapping[name.strip()] = slug
    return mapping


def canonical_source(raw: str | None) -> str:
    if not raw:
        return ""
    key = raw.strip()
    aliases = _alias_to_slug()
    return aliases.get(key, aliases.get(key.lower(), key))


def display_name_for_slug(slug: str) -> str:
    directory = _load_site_directory()
    if slug in directory:
        return directory[slug]["name"]
    return slug.replace("_", " ").title()


def country_for_slug(slug: str) -> str | None:
    directory = _load_site_directory()
    return directory.get(slug, {}).get("country")


def normalize_product_record(record: Any, slug: str, config: dict[str, Any] | None = None) -> None:
    """Fuerza source=slug y país del proveedor antes de guardar."""
    record.source = slug
    if config:
        record.country = config.get("country") or record.country


def aggregate_provider_counts(sources: list[str]) -> list[dict[str, Any]]:
    """
    Agrupa por proveedor canónico (un slug = una barra en gráficos).
    name = nombre legible sin repetir slugs distintos para el mismo proveedor.
    """
    by_slug: dict[str, int] = defaultdict(int)
    for raw in sources:
        slug = canonical_source(raw)
        if slug:
            by_slug[slug] += 1

    by_display: dict[str, dict[str, Any]] = {}
    for slug, count in sorted(by_slug.items(), key=lambda x: -x[1]):
        label = display_name_for_slug(slug)
        key = label.lower()
        if key in by_display:
            by_display[key]["productos"] += count
            by_display[key]["slug"] += f",{slug}"
        else:
            by_display[key] = {
                "slug": slug,
                "name": label,
                "productos": count,
                "country": country_for_slug(slug) or "—",
            }
    return sorted(by_display.values(), key=lambda x: -x["productos"])


def find_duplicate_provider_names() -> list[tuple[str, str, str]]:
    """Detecta nombres visibles repetidos entre slugs distintos."""
    by_name: dict[str, list[str]] = defaultdict(list)
    for slug, meta in _load_site_directory().items():
        by_name[meta["name"].lower()].append(slug)
    dups = []
    for name, slugs in by_name.items():
        if len(slugs) > 1:
            dups.append((name, slugs[0], ", ".join(slugs[1:])))
    return dups


def validate_provider_name_unique(name: str, country: str, exclude_slug: str | None = None) -> str | None:
    """None si OK; mensaje de error si el nombre ya existe en ese país."""
    name_key = name.strip().lower()
    if not name_key:
        return "El nombre del proveedor es obligatorio."
    for slug, meta in _load_site_directory().items():
        if exclude_slug and slug == exclude_slug:
            continue
        if meta.get("country") == country and meta["name"].strip().lower() == name_key:
            return f"Ya existe un proveedor con el nombre «{meta['name']}» ({slug})."
    return None


def clear_provider_cache() -> None:
    _alias_to_slug.cache_clear()


def normalize_sources_in_database(db_path: str | Path) -> int:
    """Unifica source antiguos (nombre visible) al slug canónico. Retorna filas actualizadas."""
    import sqlite3
    from pathlib import Path

    path = Path(db_path)
    if not path.exists():
        return 0
    aliases = _alias_to_slug()
    updated = 0
    with sqlite3.connect(path) as conn:
        rows = conn.execute("SELECT DISTINCT source FROM products").fetchall()
        for (raw,) in rows:
            canon = canonical_source(raw)
            if canon and canon != raw:
                cur = conn.execute(
                    "UPDATE products SET source = ? WHERE source = ?",
                    (canon, raw),
                )
                updated += cur.rowcount
    return updated
