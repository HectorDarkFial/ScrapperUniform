from __future__ import annotations

from typing import Any, Callable

from src.config_loader import get_settings, get_sites
from src.db import Database
from src.models import ProductRecord, ScrapeStats
from src.providers import normalize_product_record
from src.scrapers.registry import build_scraper
from src.utils.http import HttpClient
from src.utils.logging import setup_logging
from src.utils.product_security import apply_url_security
from src.utils.url_security import domains_from_site_config

logger = setup_logging()


class Pipeline:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.sites = get_sites()
        db_path = self.settings["database"]["path"]
        self.db = Database(db_path)
        http_cfg = self.settings["http"]
        self.http = HttpClient(
            user_agent=http_cfg["user_agent"],
            timeout=http_cfg["timeout_seconds"],
            delay=http_cfg["delay_seconds"],
            max_retries=http_cfg["max_retries"],
            excluded_domains=self.settings.get("excluded_domains", []),
        )
        scraping = self.settings.get("scraping", {})
        respect = http_cfg.get("respect_robots", True)
        if scraping.get("fast_mode") and scraping.get("skip_robots_in_fast_mode"):
            respect = False
        self.http.respect_robots = respect
        self.default_max_pages = self.settings["scraping"]["default_max_pages"]
        self.default_max_products = self.settings["scraping"]["default_max_products_per_site"]

    def list_active_sites(self, country: str | None = None) -> list[str]:
        slugs = []
        for slug, cfg in self.sites.items():
            if not cfg.get("enabled", True):
                continue
            if country and country.upper() != "ALL" and cfg.get("country") != country.upper():
                continue
            slugs.append(slug)
        return slugs

    def run_site(
        self,
        slug: str,
        max_pages: int | None = None,
        max_products: int | None = None,
        on_progress: Callable[..., None] | None = None,
        should_stop: Callable[[], bool] | None = None,
        scrape_id: str | None = None,
    ) -> tuple[list[ProductRecord], ScrapeStats]:
        if slug not in self.sites:
            raise KeyError(f"Sitio no configurado: {slug}")
        cfg = self.sites[slug]
        if not cfg.get("enabled", True):
            logger.info("Sitio deshabilitado: %s", slug)
            return [], ScrapeStats(source=slug)

        delay = cfg.get("delay_seconds", self.http.delay)
        self.http.delay = delay
        self.http.set_allowed_domains(domains_from_site_config(cfg))

        scraper = build_scraper(slug, cfg, self.http)

        def site_progress(**kwargs: Any) -> None:
            if on_progress:
                on_progress(slug=slug, **kwargs)

        records = scraper.run(
            max_pages=max_pages or self.default_max_pages,
            max_products=max_products or self.default_max_products,
            on_progress=site_progress if on_progress else None,
            should_stop=should_stop,
        )

        saved: list[ProductRecord] = []
        for record in records:
            if should_stop and should_stop():
                break
            if scrape_id:
                record.scrape_id = scrape_id
            normalize_product_record(record, slug, cfg)
            if not apply_url_security(record, cfg):
                scraper.stats.skipped += 1
                logger.warning("Producto omitido (URL insegura): %s", record.name[:80])
                continue
            self.db.upsert_product(record)
            saved.append(record)

        return saved, scraper.stats

    def run_all(
        self,
        site_filter: str = "all",
        max_pages: int | None = None,
        max_products: int | None = None,
        country: str | None = None,
        on_progress: Callable[..., None] | None = None,
        should_stop: Callable[[], bool] | None = None,
        scrape_id: str | None = None,
    ) -> dict[str, Any]:
        if site_filter == "all":
            slugs = self.list_active_sites(country=country)
        else:
            slugs = [site_filter]
        summary: dict[str, Any] = {"sites": {}, "total_saved": 0}
        total_sites = max(len(slugs), 1)
        max_p = max_products or self.default_max_products

        def site_pct(index: int, fraction: float) -> int:
            """fraction 0..1 dentro del tramo del sitio actual."""
            site_span = 90 / total_sites
            base = 5 + index * site_span
            return int(min(94, base + site_span * fraction))

        for index, slug in enumerate(slugs):
            if should_stop and should_stop():
                summary["stopped"] = True
                break
            logger.info("=== Iniciando %s ===", slug)
            if on_progress:
                on_progress(
                    pct=site_pct(index, 0.02),
                    message=f"Proveedor {index + 1}/{total_sites}: {slug}",
                    current_site=slug,
                    site_index=index + 1,
                    total_sites=total_sites,
                    phase="site_start",
                    products_done=0,
                    products_total=max_p,
                )

            def site_callback(
                *,
                slug: str = slug,
                phase: str = "",
                message: str = "",
                products_done: int = 0,
                products_total: int = 0,
            ) -> None:
                if not on_progress:
                    return
                frac = 0.12
                if phase == "catalog":
                    frac = 0.15
                elif phase == "products" and products_total > 0:
                    frac = 0.15 + 0.8 * (products_done / products_total)
                elif phase == "products":
                    frac = 0.2
                on_progress(
                    pct=site_pct(index, frac),
                    message=message,
                    current_site=slug,
                    site_index=index + 1,
                    total_sites=total_sites,
                    phase=phase,
                    products_done=products_done,
                    products_total=products_total or max_p,
                )

            try:
                records, stats = self.run_site(
                    slug,
                    max_pages,
                    max_products,
                    on_progress=site_callback if on_progress else None,
                    should_stop=should_stop,
                    scrape_id=scrape_id,
                )
                summary["sites"][slug] = {
                    "saved": len(records),
                    "ok": stats.ok,
                    "errors": stats.errors,
                    "skipped": stats.skipped,
                }
                summary["total_saved"] += len(records)
                if on_progress:
                    on_progress(
                        pct=site_pct(index, 0.98),
                        message=f"Listo {slug}: {len(records)} productos",
                        current_site=slug,
                        site_index=index + 1,
                        total_sites=total_sites,
                        phase="site_done",
                        products_done=len(records),
                        products_total=max_p,
                    )
            except Exception as exc:
                logger.exception("Fallo sitio %s: %s", slug, exc)
                summary["sites"][slug] = {"error": str(exc)}
        if should_stop and should_stop():
            summary["stopped"] = True

        from src.providers import normalize_sources_in_database

        merged = normalize_sources_in_database(self.db.path)
        if merged:
            logger.info("Fuentes de productos unificadas: %s filas", merged)
            summary["sources_normalized"] = merged

        return summary

    def close(self) -> None:
        self.http.close()
