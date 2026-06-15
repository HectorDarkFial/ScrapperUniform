from __future__ import annotations

import json
import threading
import traceback
from datetime import datetime, timezone

from django.utils import timezone as dj_tz

from portal.export_gate import require_export_ready, scoped_rows_for_export
from portal.models import ScrapeJob, Site
from src.config_store import save_site
from src.config_loader import get_settings, get_sites
from src.etl.normalize import export_analysis
from src.pipeline import Pipeline


def scrape_limits_from_settings() -> tuple[int, int]:
    scraping = get_settings().get("scraping", {})
    return (
        int(scraping.get("default_max_pages", 3)),
        int(scraping.get("default_max_products_per_site", 50)),
    )


def sync_site_to_yaml(site: Site) -> None:
    save_site(site.slug, site.to_scraper_config())


def sync_all_sites_to_yaml() -> None:
    for site in Site.objects.all():
        sync_site_to_yaml(site)


def import_sites_from_yaml() -> int:
    """Importa proveedores YAML → modelos Django (sin borrar existentes)."""
    count = 0
    for slug, cfg in get_sites().items():
        catalog = cfg.get("catalog_urls", [])
        if isinstance(catalog, list):
            catalog_text = "\n".join(catalog)
        else:
            catalog_text = str(catalog)

        defaults = {
            "enabled": cfg.get("enabled", True),
            "country": cfg.get("country", "AR"),
            "name": cfg.get("name", slug),
            "base_url": cfg.get("base_url", ""),
            "currency": cfg.get("currency", "ARS"),
            "scraper": cfg.get("scraper", "tiendanube"),
            "catalog_urls": catalog_text,
            "product_link_pattern": cfg.get("product_link_pattern", "/productos/"),
            "delay_seconds": cfg.get("delay_seconds", 2.0),
            "notes": cfg.get("notes", ""),
        }
        Site.objects.update_or_create(slug=slug, defaults=defaults)
        count += 1
    from src.providers import clear_provider_cache

    clear_provider_cache()
    return count


def _append_log(job: ScrapeJob, line: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    job.log = (job.log + f"\n[{ts}] {line}").strip()
    job.save(update_fields=["log"])


def _estimate_eta_seconds(started_at, progress: int) -> int | None:
    if not started_at or progress < 8:
        return None
    elapsed = (dj_tz.now() - started_at).total_seconds()
    if progress >= 99:
        return 0
    remaining = elapsed * (100 - progress) / progress
    return max(int(remaining), 1)


def _update_job_progress(
    job_id: int,
    pct: int,
    message: str | None = None,
    *,
    meta: dict | None = None,
    append_log: bool = False,
) -> None:
    job = ScrapeJob.objects.get(pk=job_id)
    job.progress = max(0, min(99 if job.status == ScrapeJob.Status.RUNNING else 100, pct))
    fields = ["progress"]
    if append_log and message:
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        job.log = (job.log + f"\n[{ts}] {message}").strip()
        fields.append("log")
    payload: dict = {"progressMeta": meta or {}}
    if message:
        payload["progressMeta"]["message"] = message
    if job.started_at:
        payload["etaSeconds"] = _estimate_eta_seconds(job.started_at, job.progress)
    job.result_json = json.dumps(payload, default=str)
    fields.append("result_json")
    job.save(update_fields=fields)


def run_scrape_job(job_id: int) -> None:
    job = ScrapeJob.objects.get(pk=job_id)
    job.status = ScrapeJob.Status.RUNNING
    job.progress = 2
    job.started_at = dj_tz.now()
    job.log = ""
    job.stop_requested = False
    job.save(update_fields=["status", "started_at", "progress", "log", "stop_requested"])

    _update_job_progress(
        job_id,
        3,
        f"Preparando scraping (país={job.country}, sitio={job.site_slug})…",
        meta={"phase": "init"},
    )

    pipeline = Pipeline()
    scrape_run_id = f"job-{job_id}"

    def _job_stop_requested() -> bool:
        current = ScrapeJob.objects.filter(pk=job_id).values("stop_requested").first()
        return bool(current and current.get("stop_requested"))

    try:
        _append_log(job, f"Iniciando scraping país={job.country} sitio={job.site_slug}")

        def on_progress(
            *,
            pct: int,
            message: str,
            current_site: str | None = None,
            site_index: int = 0,
            total_sites: int = 1,
            phase: str = "",
            products_done: int = 0,
            products_total: int = 0,
        ) -> None:
            meta = {
                "currentSite": current_site,
                "siteIndex": site_index,
                "totalSites": total_sites,
                "phase": phase,
                "productsDone": products_done,
                "productsTotal": products_total,
            }
            _update_job_progress(
                job_id,
                pct,
                message,
                meta=meta,
                append_log=phase in ("site_start", "site_done"),
            )

        summary = pipeline.run_all(
            job.site_slug,
            max_pages=job.max_pages,
            max_products=job.max_products,
            country=job.country,
            on_progress=on_progress,
            should_stop=_job_stop_requested,
            scrape_id=scrape_run_id,
        )
        _append_log(job, f"Total guardados: {summary['total_saved']}")
        for slug, data in summary.get("sites", {}).items():
            _append_log(job, f"  {slug}: {data}")

        export_paths = None
        if job.do_export:
            require_export_ready(pipeline.db.path)
            rows = pipeline.db.fetch_by_scrape_id(scrape_run_id)
            export_paths = export_analysis(rows, fmt=job.export_format)
            _append_log(job, "Exportación completada")
            for name, path in export_paths.items():
                _append_log(job, f"  {name}: {path}")
        else:
            _append_log(job, "Scraping listo. Exportá desde la sección Exportar.")

        job = ScrapeJob.objects.get(pk=job_id)
        job.progress = 100
        stopped = bool(summary.get("stopped"))
        job.status = ScrapeJob.Status.CANCELLED if stopped else ScrapeJob.Status.DONE
        if stopped:
            _append_log(job, "Scraping detenido por el usuario. Se guardaron resultados parciales.")
        job.result_json = json.dumps(
            {
                "summary": summary,
                "export_paths": export_paths,
                "progressMeta": {
                    "phase": "cancelled" if stopped else "done",
                    "message": "Detenido con resultados parciales" if stopped else "Completado",
                },
                "etaSeconds": 0,
                "scrapeRunId": scrape_run_id,
            },
            default=str,
        )
    except Exception as exc:
        job.status = ScrapeJob.Status.ERROR
        job.error_message = str(exc)
        _append_log(job, f"Error: {exc}")
        _append_log(job, traceback.format_exc())
    finally:
        pipeline.close()
        job.finished_at = dj_tz.now()
        job.save(
            update_fields=["status", "error_message", "result_json", "finished_at", "log", "progress"]
        )


def start_scrape_job(
    country: str = "all",
    site_slug: str = "all",
    max_pages: int | None = None,
    max_products: int | None = None,
    do_export: bool = False,
    export_format: str = "xlsx",
) -> ScrapeJob | None:
    if ScrapeJob.objects.filter(status=ScrapeJob.Status.RUNNING).exists():
        return None

    sync_all_sites_to_yaml()
    default_pages, default_products = scrape_limits_from_settings()
    max_pages = max_pages if max_pages is not None else default_pages
    max_products = max_products if max_products is not None else default_products
    job = ScrapeJob.objects.create(
        job_type="scrape",
        country=country,
        site_slug=site_slug,
        max_pages=max_pages,
        max_products=max_products,
        do_export=do_export,
        export_format=export_format,
        status=ScrapeJob.Status.PENDING,
        stop_requested=False,
    )
    threading.Thread(target=run_scrape_job, args=(job.pk,), daemon=True).start()
    return job


def stop_job(job_id: int | None = None) -> ScrapeJob | None:
    qs = ScrapeJob.objects.filter(status=ScrapeJob.Status.RUNNING, job_type="scrape")
    if job_id is not None:
        qs = qs.filter(pk=job_id)
    job = qs.first()
    if not job:
        return None
    job.stop_requested = True
    job.save(update_fields=["stop_requested"])
    _append_log(job, "Solicitud de detención recibida. Cerrando scraping…")
    return job


def run_export_job(job_id: int) -> None:
    job = ScrapeJob.objects.get(pk=job_id)
    job.status = ScrapeJob.Status.RUNNING
    job.progress = 10
    job.started_at = dj_tz.now()
    job.save(update_fields=["status", "started_at", "progress"])

    try:
        from src.config_loader import get_settings
        from src.db import Database

        db = Database(get_settings()["database"]["path"])
        require_export_ready(db.path, exclude_job_id=job_id)
        _update_job_progress(job_id, 50, "Generando archivos…", meta={"phase": "export"})
        rows = scoped_rows_for_export(db)
        paths = export_analysis(rows, fmt=job.export_format)
        job.progress = 100
        _append_log(job, "Archivos generados:")
        for name, path in paths.items():
            _append_log(job, f"  {name}: {path}")
        job.status = ScrapeJob.Status.DONE
        job.result_json = json.dumps({"export_paths": paths})
    except Exception as exc:
        job.status = ScrapeJob.Status.ERROR
        job.error_message = str(exc)
        _append_log(job, str(exc))
    finally:
        job.finished_at = dj_tz.now()
        job.save(
            update_fields=["status", "error_message", "result_json", "finished_at", "log", "progress"]
        )


def start_export_job(export_format: str = "xlsx") -> ScrapeJob | None:
    if ScrapeJob.objects.filter(status=ScrapeJob.Status.RUNNING).exists():
        return None
    require_export_ready()
    job = ScrapeJob.objects.create(
        job_type="export",
        export_format=export_format,
        do_export=True,
        status=ScrapeJob.Status.PENDING,
    )
    threading.Thread(target=run_export_job, args=(job.pk,), daemon=True).start()
    return job
