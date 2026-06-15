from decimal import Decimal
from pathlib import Path

from src.db import Database
from src.models import Availability, ProductRecord


def test_upsert_and_fetch(tmp_path: Path):
    db = Database(tmp_path / "test.db")
    record = ProductRecord(
        source="test_site",
        product_url="https://example.com/p/1",
        name="Bata clínica",
        price=Decimal("15000"),
        availability=Availability.IN_STOCK,
    )
    db.upsert_product(record)
    rows = db.fetch_all()
    assert len(rows) == 1
    assert rows[0]["name"] == "Bata clínica"

    record.price = Decimal("16000")
    db.upsert_product(record)
    rows = db.fetch_all()
    assert len(rows) == 1
    assert float(rows[0]["price"]) == 16000.0
