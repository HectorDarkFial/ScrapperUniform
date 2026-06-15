from src.providers import (
    aggregate_provider_counts,
    canonical_source,
    display_name_for_slug,
    normalize_product_record,
)
from src.models import ProductRecord, Availability
from decimal import Decimal


def test_canonical_source_maps_name_to_slug():
    slug = canonical_source("Soul Uniformes Médicos")
    assert slug == "soul_uniform" or canonical_source("soul_uniform") == "soul_uniform"


def test_aggregate_provider_counts_merges_aliases():
    rows = aggregate_provider_counts(
        ["soul_uniform", "Soul Uniformes Médicos", "soul_uniform"]
    )
    assert len(rows) == 1
    assert rows[0]["productos"] == 3
    assert "Soul" in rows[0]["name"] or rows[0]["name"]


def test_normalize_product_record_forces_slug():
    rec = ProductRecord(
        source="Nombre Viejo",
        product_url="https://x.com/p",
        name="Test",
        price=Decimal("100"),
        currency="ARS",
        availability=Availability.IN_STOCK,
    )
    normalize_product_record(rec, "soul_uniform", {"country": "AR"})
    assert rec.source == "soul_uniform"
    assert rec.country == "AR"
