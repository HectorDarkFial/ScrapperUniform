from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.models import Availability, ProductRecord
from src.scrapers.base import ScraperBase
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


class TiendaNubeScraper(ScraperBase):
    """Scraper para tiendas TiendaNube (soul, coco, dara)."""

    def scrape_catalog(self, max_pages: int = 3) -> list[str]:
        pattern = self.config.get("product_link_pattern", "/productos/")
        urls: list[str] = []
        seen: set[str] = set()

        for catalog_url in self.config.get("catalog_urls", []):
            page_url = catalog_url
            for _ in range(max_pages):
                soup = self.fetch_soup(page_url)
                for a in soup.select("a[href]"):
                    href = a.get("href", "")
                    if pattern not in href:
                        continue
                    full = self.normalize_url(href)
                    if full and full not in seen:
                        seen.add(full)
                        urls.append(full)

                next_link = soup.select_one(
                    'a[rel="next"], .pagination-next a, a.js-pagination-next'
                )
                if not next_link or not next_link.get("href"):
                    break
                page_url = urljoin(page_url, next_link["href"])

        return urls

    def scrape_product(self, url: str) -> ProductRecord | None:
        soup = self.fetch_soup(url)
        ld = self._extract_json_ld(soup)

        name = ld.get("name") if ld else None
        if not name:
            h1 = soup.select_one("h1, .js-product-name, .product-name")
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
                ".js-price-display",
                ".product-price",
                "[data-component='product-price'] .price",
                ".js-price-display .price",
            ],
        )
        compare_text = first_visible_price_text(
            soup,
            [".js-compare-price-display", ".compare-price", ".price-compare"],
        )
        extracted = resolve_product_prices(
            currency=currency,
            offers=offers if offers else None,
            sale_html_text=sale_text,
            list_html_text=compare_text,
            soup=soup,
            discount_html_text=collect_discount_badges(soup),
        )

        avail_url = offers.get("availability", "") if offers else ""
        availability = parse_schema_availability(str(avail_url))
        stock_text = None
        stock_el = soup.select_one(".js-stock-label, .product-stock, #stock")
        if stock_el:
            stock_text = stock_el.get_text(strip=True)
            if availability == Availability.UNKNOWN:
                availability = parse_availability(stock_text)
        availability = infer_availability_from_soup(soup, availability)

        sku = str(ld.get("sku", "")) if ld and ld.get("sku") else None
        if not sku:
            sku_el = soup.select_one(".js-product-sku, .sku")
            sku = sku_el.get_text(strip=True) if sku_el else None

        image = ld.get("image") if ld else None
        if isinstance(image, list):
            image = image[0] if image else None

        category = self._breadcrumb_category(soup)
        sizes, colors = self._variants(soup)

        canonical = url.split("?")[0].rstrip("/")

        record = ProductRecord(
            source=self.slug,
            country=self.config.get("country"),
            product_url=canonical,
            sku=sku,
            name=name,
            category=category,
            currency=currency,
            availability=availability,
            stock_text=stock_text,
            sizes=sizes,
            colors=colors,
            image_url=image,
            raw_attributes={"json_ld": ld} if ld else {},
        )
        apply_price_breakdown(record, extracted)
        return record

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict[str, Any]:
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or "")
            except json.JSONDecodeError:
                continue
            items = data if isinstance(data, list) else [data]
            for item in items:
                if item.get("@type") == "Product":
                    return item
                if item.get("@type") == "WebPage" and item.get("mainEntity", {}).get("@type") == "Product":
                    return item["mainEntity"]
        return {}

    def _breadcrumb_category(self, soup: BeautifulSoup) -> str | None:
        crumbs = soup.select(".breadcrumb a, .breadcrumbs a")
        if len(crumbs) >= 2:
            return crumbs[-1].get_text(strip=True)
        return None

    def _variants(self, soup: BeautifulSoup) -> tuple[list[str], list[str]]:
        sizes: list[str] = []
        colors: list[str] = []
        for opt in soup.select(
            'select[name*="size"] option, select[name*="talle"] option, .js-variant-option'
        ):
            text = opt.get_text(strip=True)
            if text and text.lower() not in ("seleccionar", "elegir", ""):
                if text not in sizes:
                    sizes.append(text)
        color_labels = soup.select('[data-variant-name="Color"] label, .variation-color')
        for el in color_labels:
            t = el.get("title") or el.get_text(strip=True)
            if t and t not in colors:
                colors.append(t)
        return sizes, colors
