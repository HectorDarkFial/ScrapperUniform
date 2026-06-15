from __future__ import annotations

from decimal import Decimal

from portal.export_gate import assess_export_readiness, require_export_ready
from portal.models import ScrapeJob
from src.db import Database
from src.models import Availability, ProductRecord


def test_export_readiness_ignores_current_export_job(tmp_path, django_db_setup):
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.upsert_product(
        ProductRecord(
            source="soul_uniform",
            country="AR",
            product_url="https://www.souluniform.com.ar/productos/test/",
            name="Bata clínica",
            price=Decimal("15000"),
            availability=Availability.IN_STOCK,
        )
    )
    ScrapeJob.objects.create(job_type="scrape", status=ScrapeJob.Status.DONE)
    export_job = ScrapeJob.objects.create(job_type="export", status=ScrapeJob.Status.RUNNING)

    blocked = assess_export_readiness(str(db_path))
    assert blocked["canExport"] is False
    assert "exportación" in blocked["message"].lower()

    allowed = assess_export_readiness(str(db_path), exclude_job_id=export_job.pk)
    assert allowed["canExport"] is True

    require_export_ready(str(db_path), exclude_job_id=export_job.pk)
