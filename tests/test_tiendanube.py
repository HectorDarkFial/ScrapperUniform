from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from src.scrapers.tiendanube import TiendaNubeScraper

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_product_from_fixture():
    html = (FIXTURES / "soul_product.html").read_text(encoding="utf-8")
    config = {
        "base_url": "https://www.souluniform.com.ar",
        "currency": "ARS",
        "catalog_urls": [],
        "product_link_pattern": "/productos/",
    }
    scraper = TiendaNubeScraper("soul_uniform", config, MagicMock())
    scraper.fetch_soup = lambda url: BeautifulSoup(html, "lxml")  # type: ignore[method-assign]

    record = scraper.scrape_product("https://www.souluniform.com.ar/productos/conjunto-test/")
    assert record is not None
    assert record.name == "Conjunto Médico Unisex Importado"
    assert record.price == Decimal("99999")
    assert record.price_list == Decimal("129999")
    assert record.discount_display == "23% OFF"
    assert record.price_without_tax is None
    assert record.sku == "42029V"
    assert record.availability.value == "in_stock"
    assert record.is_valid_for_storage()


def test_scrape_catalog_links():
    html = (FIXTURES / "soul_listing.html").read_text(encoding="utf-8")
    config = {
        "base_url": "https://www.souluniform.com.ar",
        "catalog_urls": ["https://www.souluniform.com.ar/productos/"],
        "product_link_pattern": "/productos/",
    }
    scraper = TiendaNubeScraper("soul_uniform", config, MagicMock())
    scraper.fetch_soup = lambda url: BeautifulSoup(html, "lxml")  # type: ignore[method-assign]

    urls = scraper.scrape_catalog(max_pages=1)
    assert len(urls) == 2
    assert all("/productos/" in u for u in urls)
