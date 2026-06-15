from __future__ import annotations

import json

import pytest

from portal.export_gate import assess_export_readiness, row_is_exportable, scoped_rows_for_export
from portal.models import ScrapeJob, Site


def test_row_is_exportable_with_price_and_trusted_url():
    assert row_is_exportable(
        {
            "name": "Bata",
            "product_url": "https://www.souluniform.com.ar/productos/test/",
            "source": "soul_uniform",
            "price": 1000,
            "availability": "unknown",
        }
    )


def test_row_is_exportable_without_price_or_stock():
    assert not row_is_exportable(
        {
            "name": "Bata",
            "product_url": "https://x.com/p",
            "source": "soul",
            "price": None,
            "availability": "unknown",
        }
    )


def test_export_blocked_without_successful_scrape(django_db_setup):
    ScrapeJob.objects.all().delete()
    state = assess_export_readiness()
    assert state["canExport"] is False
    assert "scraping" in state["message"].lower() or "Ejecutá" in state["message"]


def test_export_allowed_after_scrape_done(tmp_path, django_db_setup):
    from decimal import Decimal

    from src.db import Database
    from src.models import Availability, ProductRecord

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

    Site.objects.update_or_create(
        slug="soul_uniform",
        defaults={
            "name": "Soul Uniform",
            "enabled": True,
            "country": "AR",
            "base_url": "https://www.souluniform.com.ar",
            "currency": "ARS",
            "scraper": "tiendanube",
            "catalog_urls": "https://www.souluniform.com.ar/productos/",
        },
    )
    ScrapeJob.objects.create(
        job_type="scrape",
        status=ScrapeJob.Status.DONE,
        result_json=json.dumps({"scrapeRunId": "job-1"}),
    )

    state = assess_export_readiness(str(db_path))
    assert state["exportableProducts"] >= 1
    assert state["canExport"] is True


def test_scoped_rows_for_export_uses_latest_scrape_run_id(tmp_path, django_db_setup):
    from decimal import Decimal

    from src.db import Database
    from src.models import Availability, ProductRecord

    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.upsert_product(
        ProductRecord(
            scrape_id="old-run",
            source="old_provider",
            country="AR",
            product_url="https://www.souluniform.com.ar/productos/old/",
            name="Producto viejo",
            price=Decimal("1000"),
            availability=Availability.IN_STOCK,
        )
    )
    db.upsert_product(
        ProductRecord(
            scrape_id="job-22",
            source="new_provider",
            country="AR",
            product_url="https://www.souluniform.com.ar/productos/new/",
            name="Producto nuevo",
            price=Decimal("2000"),
            availability=Availability.IN_STOCK,
        )
    )

    Site.objects.update_or_create(
        slug="new_provider",
        defaults={
            "name": "New Provider",
            "enabled": True,
            "country": "AR",
            "base_url": "https://www.souluniform.com.ar",
            "currency": "ARS",
            "scraper": "tiendanube",
            "catalog_urls": "https://www.souluniform.com.ar/productos/",
        },
    )
    ScrapeJob.objects.create(
        job_type="scrape",
        status=ScrapeJob.Status.DONE,
        result_json=json.dumps({"scrapeRunId": "job-22"}),
    )

    rows = scoped_rows_for_export(db)
    assert len(rows) == 1
    assert rows[0]["source"] == "new_provider"


def test_scoped_rows_for_export_only_active_providers(tmp_path, django_db_setup):
    from decimal import Decimal

    from src.db import Database
    from src.models import Availability, ProductRecord

    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.upsert_product(
        ProductRecord(
            scrape_id="job-77",
            source="active_site",
            country="CL",
            product_url="https://active.example.com/p/1",
            name="Producto activo",
            price=Decimal("12000"),
            availability=Availability.IN_STOCK,
        )
    )
    db.upsert_product(
        ProductRecord(
            scrape_id="job-77",
            source="inactive_site",
            country="CL",
            product_url="https://inactive.example.com/p/1",
            name="Producto inactivo",
            price=Decimal("22000"),
            availability=Availability.IN_STOCK,
        )
    )
    Site.objects.update_or_create(
        slug="active_site",
        defaults={
            "name": "Active",
            "enabled": True,
            "country": "CL",
            "base_url": "https://active.example.com",
            "currency": "CLP",
            "scraper": "shopify",
            "catalog_urls": "https://active.example.com/collections/all",
        },
    )
    Site.objects.update_or_create(
        slug="inactive_site",
        defaults={
            "name": "Inactive",
            "enabled": False,
            "country": "CL",
            "base_url": "https://inactive.example.com",
            "currency": "CLP",
            "scraper": "shopify",
            "catalog_urls": "https://inactive.example.com/collections/all",
        },
    )
    ScrapeJob.objects.create(
        job_type="scrape",
        status=ScrapeJob.Status.DONE,
        result_json=json.dumps({"scrapeRunId": "job-77"}),
    )

    rows = scoped_rows_for_export(db)
    assert len(rows) == 1
    assert rows[0]["source"] == "active_site"


def test_export_allowed_after_scrape_cancelled_with_partial_data(tmp_path, django_db_setup):
    from decimal import Decimal

    from src.db import Database
    from src.models import Availability, ProductRecord

    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.upsert_product(
        ProductRecord(
            scrape_id="job-501",
            source="partial_site",
            country="CL",
            product_url="https://partial.example.com/p/1",
            name="Producto parcial",
            price=Decimal("9900"),
            availability=Availability.IN_STOCK,
        )
    )
    Site.objects.update_or_create(
        slug="partial_site",
        defaults={
            "name": "Partial",
            "enabled": True,
            "country": "CL",
            "base_url": "https://partial.example.com",
            "currency": "CLP",
            "scraper": "shopify",
            "catalog_urls": "https://partial.example.com/collections/all",
        },
    )
    ScrapeJob.objects.create(
        job_type="scrape",
        status=ScrapeJob.Status.CANCELLED,
        result_json=json.dumps({"scrapeRunId": "job-501"}),
    )

    state = assess_export_readiness(str(db_path))
    assert state["exportableProducts"] == 1
    assert state["canExport"] is True
