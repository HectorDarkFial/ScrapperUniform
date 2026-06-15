import pytest

from src.utils.export_security import row_is_safe_for_export
from src.utils.url_security import (
    UrlTrust,
    assert_safe_fetch_url,
    check_url,
    domains_from_site_config,
    sanitize_excel_value,
)


def test_block_javascript_url():
    result = check_url("javascript:alert(1)")
    assert result.trust == UrlTrust.BLOCKED
    assert not result.safe_for_export


def test_block_localhost():
    result = check_url("http://127.0.0.1/admin")
    assert result.trust == UrlTrust.BLOCKED


def test_trusted_provider_domain():
    cfg = {"base_url": "https://www.suitmed.cl", "catalog_urls": ["https://www.suitmed.cl/collections/all"]}
    allowed = frozenset(domains_from_site_config(cfg))
    result = check_url("https://www.suitmed.cl/products/test", allowed_domains=allowed)
    assert result.trust == UrlTrust.TRUSTED
    assert result.safe_for_fetch


def test_unverified_external_domain():
    result = check_url("https://evil-example.test/product", purpose="export")
    assert result.trust == UrlTrust.UNVERIFIED


def test_assert_safe_fetch_blocks_unlisted():
    with pytest.raises(ValueError, match="no permitida"):
        assert_safe_fetch_url(
            "https://unknown-shop.test/p",
            {"www.suitmed.cl"},
        )


def test_sanitize_excel_formula_injection():
    assert sanitize_excel_value("=CMD|calc") == "'=CMD|calc"
    assert sanitize_excel_value("https://www.suitmed.cl/p") == "https://www.suitmed.cl/p"


def test_export_row_blocks_unverified_by_default():
    row = {
        "name": "Test",
        "product_url": "https://random-unknown.test/p",
        "source": "x",
        "price": 100,
        "availability": "in_stock",
    }
    assert not row_is_safe_for_export(row)
