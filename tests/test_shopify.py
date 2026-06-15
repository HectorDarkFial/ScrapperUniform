from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock

from bs4 import BeautifulSoup

from src.scrapers.shopify import ShopifyScraper
from src.utils.parsers import parse_price

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_chilean_price_display():
    assert parse_price("$27.891", currency="CLP") == Decimal("27891")
    assert parse_price("$8.990", currency="CLP") == Decimal("8990")


def test_shopify_product_fixture():
    html = (FIXTURES / "shopify_product.html").read_text(encoding="utf-8")
    config = {
        "base_url": "https://www.suitmed.cl",
        "currency": "CLP",
        "country": "CL",
        "catalog_urls": [],
        "product_link_pattern": "/products/",
    }
    scraper = ShopifyScraper("suitmed_cl", config, MagicMock())
    scraper.fetch_soup = lambda url: BeautifulSoup(html, "lxml")  # type: ignore[method-assign]

    record = scraper.scrape_product("https://www.suitmed.cl/products/polera-test/")
    assert record is not None
    assert record.country == "CL"
    assert record.currency == "CLP"
    assert record.price == Decimal("27891")
    assert record.price_list == Decimal("32813")
    assert record.discount_display == "15% OFF"
    assert record.discount_percent == Decimal("15")
    assert record.price_without_tax is None
    assert record.price_transfer == Decimal("26500")
    assert record.availability.value == "in_stock"
