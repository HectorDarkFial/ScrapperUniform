from __future__ import annotations

import json
from typing import Any

from portal.models import ScrapeJob, Site
from src.config_loader import get_settings
from src.providers import canonical_source
from src.utils.export_security import row_is_safe_for_export
from src.utils.url_security import UrlTrust, check_url


def row_is_exportable(row: dict[str, Any]) -> bool:
    return row_is_safe_for_export(row)


def _reconcile_stale_jobs() -> None:
    """Marca trabajos colgados para no bloquear exportaciones nuevas."""
    from datetime import timedelta

    from django.utils import timezone as dj_tz

    now = dj_tz.now()
    for job in ScrapeJob.objects.filter(status__in=(ScrapeJob.Status.RUNNING, ScrapeJob.Status.PENDING)):
        started = job.started_at or job.created_at
        if not started:
            continue
        limit = timedelta(minutes=8 if job.job_type == "export" else 180)
        if now - started <= limit:
            continue
        job.status = ScrapeJob.Status.ERROR
        job.error_message = "El trabajo tardó demasiado o se interrumpió. Volvé a intentar."
        job.finished_at = now
        job.save(update_fields=["status", "error_message", "finished_at"])


def latest_scrape_run_id() -> str | None:
    """Obtiene el scrapeRunId de la última corrida finalizada (completa o cancelada)."""
    last_scrape = (
        ScrapeJob.objects.filter(
            job_type="scrape", status__in=(ScrapeJob.Status.DONE, ScrapeJob.Status.CANCELLED)
        )
        .exclude(result_json="")
        .order_by("-finished_at", "-created_at")
        .first()
    )
    if not last_scrape or not last_scrape.result_json:
        return None
    try:
        payload = json.loads(last_scrape.result_json)
    except json.JSONDecodeError:
        return None
    run_id = payload.get("scrapeRunId")
    return str(run_id) if run_id else None


def scoped_rows_for_export(db) -> list[dict[str, Any]]:
    """
    Devuelve filas para exportar limitadas a la última corrida de scraping.

    Si no se encuentra scrapeRunId (instancias viejas), cae en histórico completo.
    """
    run_id = latest_scrape_run_id()
    if run_id:
        rows = db.fetch_by_scrape_id(run_id)
        if not rows:
            rows = db.fetch_all()
    else:
        rows = db.fetch_all()

    active_slugs = set(Site.objects.filter(enabled=True).values_list("slug", flat=True))
    if not active_slugs:
        return rows

    filtered = [r for r in rows if canonical_source(str(r.get("source") or "")) in active_slugs]
    return filtered


def assess_export_readiness(
    db_path: str | None = None,
    *,
    exclude_job_id: int | None = None,
) -> dict[str, Any]:
    from src.db import Database

    _reconcile_stale_jobs()

    db = Database(db_path or get_settings()["database"]["path"])
    rows = scoped_rows_for_export(db)
    total = len(rows)
    exportable = sum(1 for r in rows if row_is_exportable(r))
    blocked_urls = sum(
        1
        for r in rows
        if r.get("product_url") and check_url(str(r["product_url"]), purpose="export").trust == UrlTrust.BLOCKED
    )
    unverified_urls = sum(
        1
        for r in rows
        if r.get("product_url") and check_url(str(r["product_url"]), purpose="export").trust == UrlTrust.UNVERIFIED
    )

    active_qs = ScrapeJob.objects.filter(
        status__in=(ScrapeJob.Status.RUNNING, ScrapeJob.Status.PENDING)
    )
    if exclude_job_id:
        active_qs = active_qs.exclude(pk=exclude_job_id)
    active = active_qs.first()
    scraping_running = active is not None and active.job_type == "scrape"
    any_job_running = active is not None

    last_scrape = (
        ScrapeJob.objects.filter(job_type="scrape").order_by("-created_at").first()
    )

    can_export = (
        not any_job_running
        and exportable > 0
        and last_scrape is not None
        and last_scrape.status in (ScrapeJob.Status.DONE, ScrapeJob.Status.CANCELLED)
    )

    if any_job_running:
        if scraping_running:
            message = "Esperá a que termine el scraping para exportar."
        else:
            message = "Hay una exportación en curso."
    elif last_scrape is None:
        message = "Ejecutá scraping primero (Proveedores → Scrapear)."
    elif last_scrape.status not in (ScrapeJob.Status.DONE, ScrapeJob.Status.CANCELLED):
        message = "El último scraping no terminó bien. Volvé a scrapear."
    elif exportable == 0:
        if blocked_urls:
            message = "Hay productos con URLs bloqueadas. Volvé a scrapear desde proveedores configurados."
        elif unverified_urls:
            message = "Solo se exportan URLs de proveedores verificados. Revisá la configuración de tiendas."
        else:
            message = "No hay productos con precio o disponibilidad. Completá un scraping."
    else:
        message = "Datos listos para exportar (URLs verificadas)."

    return {
        "canExport": can_export,
        "totalProducts": total,
        "exportableProducts": exportable,
        "blockedUrls": blocked_urls,
        "unverifiedUrls": unverified_urls,
        "scrapingRunning": scraping_running,
        "jobRunning": any_job_running,
        "lastScrapeStatus": last_scrape.status if last_scrape else None,
        "lastScrapeAt": (
            last_scrape.finished_at.isoformat()
            if last_scrape and last_scrape.finished_at
            else None
        ),
        "message": message,
        "securityNote": (
            "Las URLs del Excel son texto plano (sin hipervínculos automáticos) "
            "para reducir riesgos al abrir el archivo."
        ),
    }


def require_export_ready(
    db_path: str | None = None,
    *,
    exclude_job_id: int | None = None,
) -> dict[str, Any]:
    state = assess_export_readiness(db_path, exclude_job_id=exclude_job_id)
    if not state["canExport"]:
        raise ValueError(state["message"])
    return state
