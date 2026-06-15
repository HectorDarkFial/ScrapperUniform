from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_settings() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "settings.yaml")


def get_sites() -> dict[str, dict[str, Any]]:
    """Carga y fusiona proveedores desde config/sites/*.yaml."""
    sites: dict[str, dict[str, Any]] = {}
    sites_dir = CONFIG_DIR / "sites"

    if sites_dir.is_dir():
        names_seen: dict[str, str] = {}
        for path in sorted(sites_dir.glob("*.yaml")):
            data = load_yaml(path)
            chunk = data.get("sites", {})
            for slug, cfg in chunk.items():
                if slug in sites:
                    raise ValueError(f"Slug duplicado en configuración: {slug}")
                name = (cfg.get("name") or slug).strip()
                name_key = name.lower()
                if name_key in names_seen:
                    raise ValueError(
                        f"Nombre de proveedor duplicado: «{name}» "
                        f"({names_seen[name_key]} y {slug})"
                    )
                names_seen[name_key] = slug
                sites[slug] = cfg
    else:
        legacy = CONFIG_DIR / "sites.yaml"
        if legacy.exists():
            data = load_yaml(legacy)
            sites = data.get("sites", {})

    return sites


def get_sites_by_country(country: str | None = None) -> dict[str, dict[str, Any]]:
    all_sites = get_sites()
    if not country or country.upper() == "ALL":
        return all_sites
    code = country.upper()
    return {k: v for k, v in all_sites.items() if v.get("country") == code}
