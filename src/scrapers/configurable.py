from __future__ import annotations

import re
from urllib.parse import urljoin

from src.models import Availability, ProductRecord
from src.scrapers.base import ScraperBase
from src.utils.parsers import infer_availability_from_soup, parse_availability
from src.utils.price_extract import apply_price_breakdown, resolve_product_prices


class ConfigurableScraper(ScraperBase):
    """Scraper basado en selectores CSS definidos en sites.yaml."""

    def scrape_catalog(self, max_pages: int = 3) -> list[str]:
        selectors = self.config.get("selectors", {})
        link_sel = selectors.get("product_links", "a[href]")
        urls: list[str] = []
        seen: set[str] = set()

        for catalog_url in self.config.get("catalog_urls", []):
            page_url = catalog_url
            for _ in range(max_pages):
                soup = self.fetch_soup(page_url)
                for a in soup.select(link_sel):
                    href = a.get("href", "")
                    full = self.normalize_url(href)
                    if full and full not in seen:
                        seen.add(full)
                        urls.append(full)

                next_link = soup.select_one("a.next, .pages-item-next a, .action.next")
                if not next_link or not next_link.get("href"):
                    break
                page_url = urljoin(page_url, next_link["href"])

        return urls

    def scrape_product(self, url: str) -> ProductRecord | None:
        soup = self.fetch_soup(url)
        sel = self.config.get("selectors", {})

        def text(css: str | None) -> str | None:
            if not css:
                return None
            el = soup.select_one(css)
            return el.get_text(strip=True) if el else None

        name = text(sel.get("name"))
        if not name:
            return None

        sale_text = text(sel.get("price"))
        list_text = text(sel.get("price_list"))
        if sale_text is None:
            for node in soup.find_all(string=re.compile(r"\$\s*[\d.]")):
                sale_text = str(node).strip()
                if sale_text:
                    break

        extracted = resolve_product_prices(
            currency=self.currency,
            sale_html_text=sale_text,
            list_html_text=list_text,
            soup=soup,
        )
        stock_text = text(sel.get("availability"))
        availability = parse_availability(stock_text)
        availability = infer_availability_from_soup(soup, availability)
        sku = text(sel.get("sku"))
        category = text(sel.get("category"))

        img_el = soup.select_one("img[itemprop='image'], .gallery img, .product-image img")
        image_url = img_el.get("src") if img_el else None

        canonical = url.split("?")[0].rstrip("/")

        record = ProductRecord(
            source=self.slug,
            country=self.config.get("country"),
            product_url=canonical,
            sku=sku,
            name=name,
            category=category,
            currency=self.currency,
            availability=availability,
            stock_text=stock_text,
            image_url=image_url,
        )
        apply_price_breakdown(record, extracted)
        return record
