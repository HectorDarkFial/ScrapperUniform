from __future__ import annotations

from typing import Any

from src.scrapers.base import ScraperBase
from src.scrapers.configurable import ConfigurableScraper
from src.scrapers.shopify import ShopifyScraper
from src.scrapers.tiendanube import TiendaNubeScraper
from src.scrapers.woocommerce import WooCommerceScraper
from src.utils.http import HttpClient

SCRAPER_TYPES = {
    "tiendanube": TiendaNubeScraper,
    "woocommerce": WooCommerceScraper,
    "shopify": ShopifyScraper,
    "configurable": ConfigurableScraper,
}


def build_scraper(slug: str, config: dict[str, Any], http: HttpClient) -> ScraperBase:
    scraper_type = config.get("scraper", "configurable")
    cls = SCRAPER_TYPES.get(scraper_type)
    if not cls:
        raise ValueError(f"Tipo de scraper desconocido: {scraper_type}")
    return cls(slug, config, http)
