from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

from src.models import Availability, ProductRecord
from src.scrapers.base import ScraperBase
from src.utils.logging import setup_logging

logger = setup_logging()
from src.utils.parsers import (
    infer_availability_from_soup,
    parse_availability,
    parse_schema_availability,
)
from src.utils.price_extract import (
    apply_price_breakdown,
    collect_discount_badges,
    first_visible_price_text,
    resolve_product_prices,
)


class ShopifyScraper(ScraperBase):
    """Scraper para tiendas Shopify (Chile y otros)."""

    def scrape_catalog(self, max_pages: int = 3) -> list[str]:
        pattern = self.config.get("product_link_pattern", "/products/")
        urls: list[str] = []
        seen: set[str] = set()

        for catalog_url in self.config.get("catalog_urls", []):
            page_url = catalog_url
            for _ in range(max_pages):
                try:
                    soup = self.fetch_soup(page_url)
                except Exception as exc:
                    logger.warning("Catálogo omitido %s: %s", page_url, exc)
                    break
                for a in soup.select("a[href]"):
                    href = a.get("href", "")
                    if pattern not in href:
                        continue
                    full = self._canonical_product_url(href)
                    if full and full not in seen:
                        seen.add(full)
                        urls.append(full)

                next_link = soup.select_one(
                    'a[rel="next"], .pagination__next a, a.pagination__next'
                )
                if not next_link or not next_link.get("href"):
                    break
                page_url = urljoin(page_url, next_link["href"])

        return urls

    def _canonical_product_url(self, href: str) -> str | None:
        full = self.normalize_url(href)
        if not full:
            return None
        match = re.search(r"/products/([^/?#]+)", full)
        if not match:
            return None
        slug = match.group(1)
        return f"{self.base_url}/products/{slug}"

    def scrape_product(self, url: str) -> ProductRecord | None:
        canonical = self._canonical_product_url(url) or url
        soup = self.fetch_soup(canonical)
        ld = self._extract_json_ld(soup)

        name = ld.get("name") if ld else None
        if not name:
            h1 = soup.select_one("h1, .product__title, .product-title")
            name = h1.get_text(strip=True) if h1 else None
        if not name:
            return None

        offers = ld.get("offers", {}) if ld else {}
        if isinstance(offers, list):
            offers = offers[0] if offers else {}

        currency = offers.get("priceCurrency", self.currency) if offers else self.currency
        sale_text = first_visible_price_text(
            soup,
            [
                ".price-item--sale",
                ".price-item--last",
                ".price__regular .price-item",
                ".product-price",
                ".price .amount",
                "span.price",
                "[data-product-price]",
            ],
        )
        list_text = first_visible_price_text(
            soup,
            [
                ".price__compare",
                ".price-item--regular",
                "s.price-item",
                ".compare-at-price",
            ],
        )
        extracted = resolve_product_prices(
            currency=currency,
            offers=offers if offers else None,
            sale_html_text=sale_text,
            list_html_text=list_text,
            soup=soup,
            discount_html_text=collect_discount_badges(soup),
        )

        avail_url = str(offers.get("availability", "")) if offers else ""
        availability = parse_schema_availability(avail_url)
        stock_text = None
        if availability == Availability.UNKNOWN:
            avail_el = soup.select_one(".product__inventory, .product-form__inventory")
            if avail_el:
                stock_text = avail_el.get_text(strip=True)
                availability = parse_availability(stock_text)
        availability = infer_availability_from_soup(soup, availability)

        sku = str(ld.get("sku", "")) if ld and ld.get("sku") else None
        if not sku:
            sku_el = soup.select_one(".product__sku, [data-product-sku]")
            sku = sku_el.get_text(strip=True) if sku_el else None

        image = ld.get("image") if ld else None
        if isinstance(image, list):
            image = image[0] if image else None

        category = self._breadcrumb_category(soup)

        record = ProductRecord(
            source=self.slug,
            product_url=canonical,
            sku=sku,
            name=name,
            category=category,
            currency=currency,
            availability=availability,
            stock_text=stock_text,
            image_url=image,
            raw_attributes={"json_ld": ld} if ld else {},
            country=self.config.get("country"),
        )
        apply_price_breakdown(record, extracted)
        return record

    def _extract_json_ld(self, soup) -> dict[str, Any]:
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or "")
            except json.JSONDecodeError:
                continue
            items: list[dict] = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if "@graph" in data:
                    items = data["@graph"]
                else:
                    items = [data]
            for item in items:
                t = item.get("@type", "")
                if t == "Product":
                    return item
                if t == "ProductGroup" and item.get("hasVariant"):
                    variants = item["hasVariant"]
                    if variants:
                        return variants[0] if isinstance(variants, list) else variants
            for item in items:
                if item.get("@type") == "Product":
                    return item
        return {}

    def _breadcrumb_category(self, soup) -> str | None:
        crumbs = soup.select(".breadcrumbs a, nav[aria-label*='breadcrumb'] a")
        if len(crumbs) >= 2:
            return crumbs[-1].get_text(strip=True)
        return None
