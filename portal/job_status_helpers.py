from __future__ import annotations

import json
from typing import Any

from portal.models import ScrapeJob


def serialize_job_status(job: ScrapeJob | None) -> dict[str, Any]:
    """Payload JSON unificado para panel React y legacy."""
    if not job:
        return {
            "running": False,
            "status": "idle",
            "log": "",
            "progress": 0,
            "progressMessage": "",
            "progressMeta": {},
            "etaSeconds": None,
            "jobType": None,
            "error": "",
        }

    progress = job.progress or 0
    if job.status in (ScrapeJob.Status.DONE, ScrapeJob.Status.CANCELLED):
        progress = 100
    elif job.status == ScrapeJob.Status.RUNNING and progress == 0:
        lines = job.log.count("\n") if job.log else 0
        progress = min(90, 10 + lines * 8)

    result: dict = {}
    progress_meta: dict = {}
    eta_seconds = None
    progress_message = ""
    if job.result_json:
        try:
            result = json.loads(job.result_json)
            progress_meta = result.get("progressMeta") or {}
            eta_seconds = result.get("etaSeconds")
            progress_message = progress_meta.get("message") or ""
        except json.JSONDecodeError:
            result = {}

    running = job.status in (ScrapeJob.Status.RUNNING, ScrapeJob.Status.PENDING)
    if running and job.started_at and eta_seconds is None and progress >= 8:
        from portal.services import _estimate_eta_seconds

        eta_seconds = _estimate_eta_seconds(job.started_at, progress)

    status_label = {
        ScrapeJob.Status.PENDING: "Pendiente",
        ScrapeJob.Status.RUNNING: "En curso",
        ScrapeJob.Status.DONE: "Completado",
        ScrapeJob.Status.CANCELLED: "Detenido",
        ScrapeJob.Status.ERROR: "Error",
    }.get(job.status, job.status)

    job_type_label = "Exportación" if job.job_type == "export" else "Scraping"

    return {
        "jobId": job.pk,
        "jobType": job.job_type,
        "jobTypeLabel": job_type_label,
        "running": running,
        "status": job.status,
        "statusLabel": status_label,
        "log": job.log,
        "error": job.error_message,
        "progress": progress,
        "progressMessage": progress_message,
        "progressMeta": progress_meta,
        "etaSeconds": eta_seconds,
        "result": result,
    }
