from decimal import Decimal

from src.models import Availability
from src.utils.parsers import (
    parse_availability,
    parse_price,
    parse_schema_availability,
)


def test_parse_price_argentine_format():
    assert parse_price("$ 99.999,50") == Decimal("99999.50")
    assert parse_price("99999") == Decimal("99999")


def test_parse_price_chile_format():
    assert parse_price("$27.891", currency="CLP") == Decimal("27891")


def test_parse_availability_spanish():
    assert parse_availability("Sin stock") == Availability.OUT_OF_STOCK
    assert parse_availability("Disponible") == Availability.IN_STOCK


def test_parse_schema_availability():
    assert parse_schema_availability("http://schema.org/InStock") == Availability.IN_STOCK
    assert parse_schema_availability("http://schema.org/OutOfStock") == Availability.OUT_OF_STOCK
