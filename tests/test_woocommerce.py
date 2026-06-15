from pathlib import Path
from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from src.scrapers.woocommerce import WooCommerceScraper

FIXTURES = Path(__file__).parent / "fixtures"


def test_woocommerce_product_fixture():
    html = (FIXTURES / "woocommerce_product.html").read_text(encoding="utf-8")
    config = {"base_url": "https://terzo.com.ar", "currency": "ARS", "catalog_urls": []}
    scraper = WooCommerceScraper("terzo", config, MagicMock())
    scraper.fetch_soup = lambda url: BeautifulSoup(html, "lxml")  # type: ignore[method-assign]

    record = scraper.scrape_product("https://terzo.com.ar/producto/ambo/")
    assert record is not None
    assert record.name == "Ambo Médico Dama"
    from decimal import Decimal

    assert record.price == Decimal("99000")
    assert record.price_list == Decimal("120000")
    assert record.availability.value == "in_stock"
