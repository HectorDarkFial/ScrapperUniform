from __future__ import annotations

import json
from urllib.parse import urljoin

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


class WooCommerceScraper(ScraperBase):
    """Scraper para sitios WooCommerce (Terzo)."""

    def scrape_catalog(self, max_pages: int = 3) -> list[str]:
        pattern = self.config.get("product_link_pattern", "/producto/")
        urls: list[str] = []
        seen: set[str] = set()

        for catalog_url in self.config.get("catalog_urls", []):
            page_url = catalog_url
            for _ in range(max_pages):
                soup = self.fetch_soup(page_url)
                for a in soup.select(
                    "a.woocommerce-LoopProduct-link, li.product a[href], a[href*='/producto/']"
                ):
                    href = a.get("href", "")
                    if pattern not in href and "/product/" not in href:
                        continue
                    full = self.normalize_url(href)
                    if full and full not in seen:
                        seen.add(full)
                        urls.append(full)

                next_link = soup.select_one("a.next.page-numbers, .woocommerce-pagination .next a")
                if not next_link or not next_link.get("href"):
                    break
                page_url = urljoin(page_url, next_link["href"])

        return urls

    def scrape_product(self, url: str) -> ProductRecord | None:
        soup = self.fetch_soup(url)

        name_el = soup.select_one("h1.product_title, h1.entry-title, h1")
        if not name_el:
            return None
        name = name_el.get_text(strip=True)

        ld: dict = {}
        offers: dict = {}
        for script in soup.select('script[type="application/ld+json"]'):
            try:
                data = json.loads(script.string or "")
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") == "Product":
                        ld = item
                        raw_offers = item.get("offers", {})
                        if isinstance(raw_offers, dict):
                            offers = raw_offers
            except json.JSONDecodeError:
                pass

        sale_text = first_visible_price_text(
            soup,
            [
                "p.price ins .woocommerce-Price-amount",
                "p.price .amount",
                ".summary .price bdi",
                ".product-price",
                "span.price",
            ],
        )
        list_text = first_visible_price_text(
            soup,
            ["p.price del .woocommerce-Price-amount", "p.price del .amount"],
        )
        currency = offers.get("priceCurrency", self.currency) if offers else self.currency
        extracted = resolve_product_prices(
            currency=currency,
            offers=offers if offers else None,
            sale_html_text=sale_text,
            list_html_text=list_text,
            soup=soup,
            discount_html_text=collect_discount_badges(soup),
        )

        stock_el = soup.select_one(".stock, p.stock")
        stock_text = stock_el.get_text(strip=True) if stock_el else None
        availability = parse_availability(stock_text)
        if availability == Availability.UNKNOWN and stock_el:
            if "out-of-stock" in " ".join(stock_el.get("class", [])):
                availability = Availability.OUT_OF_STOCK
            elif "in-stock" in " ".join(stock_el.get("class", [])):
                availability = Availability.IN_STOCK

        sku_el = soup.select_one(".sku")
        sku = sku_el.get_text(strip=True).replace("SKU:", "").strip() if sku_el else None

        img_el = soup.select_one(".woocommerce-product-gallery__image img, img.wp-post-image")
        image_url = img_el.get("src") if img_el else None

        category = None
        crumbs = soup.select(".woocommerce-breadcrumb a")
        if crumbs:
            category = crumbs[-1].get_text(strip=True)

        if ld:
            offers = ld.get("offers", {})
            if isinstance(offers, dict):
                availability = parse_schema_availability(
                    str(offers.get("availability", ""))
                ) or availability
        availability = infer_availability_from_soup(soup, availability)

        sizes = [
            o.get_text(strip=True)
            for o in soup.select('select[name="attribute_pa_talle"] option, .variations select option')
            if o.get("value")
        ]

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
            image_url=image_url,
            raw_attributes={"json_ld": ld} if ld else {},
        )
        apply_price_breakdown(record, extracted)
        return record
