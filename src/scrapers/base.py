from __future__ import annotations

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.config_loader import get_settings
from src.models import ProductRecord, ScrapeStats
from src.utils.http import HttpClient
from src.utils.logging import setup_logging

logger = setup_logging()


class ScraperBase(ABC):
    def __init__(self, slug: str, config: dict[str, Any], http: HttpClient) -> None:
        self.slug = slug
        self.config = config
        self.http = http
        self.base_url = config["base_url"].rstrip("/")
        self.currency = config.get("currency", "ARS")
        self.stats = ScrapeStats(source=slug)

    @abstractmethod
    def scrape_catalog(self, max_pages: int = 3) -> list[str]:
        ...

    @abstractmethod
    def scrape_product(self, url: str) -> ProductRecord | None:
        ...

    def normalize_url(self, href: str) -> str | None:
        if not href or href.startswith("#") or href.startswith("javascript:"):
            return None
        full = urljoin(self.base_url + "/", href)
        parsed = urlparse(full)
        if parsed.netloc and parsed.netloc not in urlparse(self.base_url).netloc:
            return None
        return full.split("#")[0].rstrip("/")

    def fetch_soup(self, url: str) -> BeautifulSoup:
        html = self.http.get(url)
        return BeautifulSoup(html, "lxml")

    def _process_product_url(self, url: str) -> ProductRecord | None:
        try:
            return self.scrape_product(url)
        except Exception as exc:
            self.stats.errors += 1
            logger.error("Error en %s: %s", url, exc)
            return None

    def _concurrent_workers(self) -> int:
        cfg = get_settings().get("scraping", {})
        if not cfg.get("fast_mode", False):
            return 1
        return max(1, min(int(cfg.get("concurrent_product_requests", 1)), 8))

    def run(
        self,
        max_pages: int = 3,
        max_products: int = 50,
        on_progress: Callable[..., None] | None = None,
        should_stop: Callable[[], bool] | None = None,
    ) -> list[ProductRecord]:
        if on_progress:
            on_progress(
                phase="catalog",
                message=f"{self.slug}: leyendo catálogo ({max_pages} pág. máx.)…",
            )
        urls = self.scrape_catalog(max_pages=max_pages)
        seen: set[str] = set()
        unique_urls: list[str] = []
        for url in urls:
            if url in seen:
                continue
            seen.add(url)
            unique_urls.append(url)
            if len(unique_urls) >= max_products:
                break

        records: list[ProductRecord] = []
        workers = self._concurrent_workers()
        total = len(unique_urls)

        def report_products(done: int) -> None:
            if on_progress:
                on_progress(
                    phase="products",
                    products_done=done,
                    products_total=total,
                    message=f"{self.slug}: producto {done}/{total}",
                )

        def collect(record: ProductRecord | None) -> None:
            if record and record.is_valid_for_storage():
                records.append(record)
                self.stats.ok += 1
            else:
                self.stats.skipped += 1

        report_products(0)
        if workers <= 1:
            for idx, url in enumerate(unique_urls, start=1):
                if should_stop and should_stop():
                    logger.info("%s — scraping detenido por solicitud", self.slug)
                    break
                collect(self._process_product_url(url))
                report_products(idx)
        else:
            done_count = 0
            with ThreadPoolExecutor(max_workers=workers) as pool:
                futures = {pool.submit(self._process_product_url, u): u for u in unique_urls}
                for fut in as_completed(futures):
                    if should_stop and should_stop():
                        logger.info("%s — scraping detenido por solicitud", self.slug)
                        break
                    collect(fut.result())
                    done_count += 1
                    report_products(done_count)

        logger.info(
            "%s — OK: %s, errores: %s, omitidos: %s",
            self.slug,
            self.stats.ok,
            self.stats.errors,
            self.stats.skipped,
        )
        return records
