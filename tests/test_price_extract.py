from decimal import Decimal

from src.utils.price_extract import parse_price_exact, resolve_product_prices
from src.utils.parsers import parse_price


def test_parse_price_clp_thousands():
    assert parse_price("$27.891", currency="CLP") == Decimal("27891")
    assert parse_price("27.891", currency="CLP") == Decimal("27891")


def test_parse_price_exact_from_schema():
    assert parse_price_exact(27891, currency="CLP") == Decimal("27891")
    assert parse_price_exact("15999.50", currency="ARS") == Decimal("15999.50")


def test_woocommerce_discount_from_del_ins():
    from bs4 import BeautifulSoup
    from pathlib import Path

    html = (Path(__file__).parent / "fixtures" / "woocommerce_product.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "lxml")
    extracted = resolve_product_prices(
        currency="ARS",
        sale_html_text="$99.000",
        list_html_text="$120.000",
        soup=soup,
    )
    assert extracted.price == Decimal("99000")
    assert extracted.price_list == Decimal("120000")
    assert extracted.discount_percent is not None


def test_resolve_json_ld_then_display_text():
    extracted = resolve_product_prices(
        currency="CLP",
        offers={"price": 27891, "priceCurrency": "CLP"},
        sale_html_text="$ 27.891",
    )
    assert extracted.price == Decimal("27891")
    assert extracted.price_display == "$27.891"
    assert extracted.source == "json_ld"


def test_resolve_price_display_ignores_stock_labels():
    extracted = resolve_product_prices(
        currency="CLP",
        sale_html_text="$31.990 CLP Precio unitario / Agotado",
        list_html_text="$39.990 CLP Precio unitario / Agotado",
    )
    assert extracted.price == Decimal("31990")
    assert extracted.price_display == "$31.990 CLP"
    assert extracted.price_list == Decimal("39990")
    assert extracted.price_list_display == "$39.990 CLP"
