from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Availability(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"
    PREORDER = "preorder"


class ProductRecord(BaseModel):
    scrape_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    source: str
    country: str | None = None
    product_url: str
    sku: str | None = None
    name: str
    category: str | None = None
    price: Decimal | None = None
    price_display: str | None = None
    currency: str = "ARS"
    price_list: Decimal | None = None
    price_list_display: str | None = None
    discount_percent: Decimal | None = None
    discount_display: str | None = None
    price_without_tax: Decimal | None = None
    price_without_tax_display: str | None = None
    price_transfer: Decimal | None = None
    price_transfer_display: str | None = None
    availability: Availability = Availability.UNKNOWN
    stock_text: str | None = None
    sizes: list[str] = Field(default_factory=list)
    colors: list[str] = Field(default_factory=list)
    image_url: str | None = None
    raw_attributes: dict[str, Any] = Field(default_factory=dict)

    @field_validator(
        "price",
        "price_list",
        "discount_percent",
        "price_without_tax",
        "price_transfer",
        mode="before",
    )
    @classmethod
    def coerce_decimal(cls, v: Any) -> Decimal | None:
        if v is None or v == "":
            return None
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v).replace(",", "."))

    def is_valid_for_storage(self) -> bool:
        """Campos mínimos para persistir según criterios del plan."""
        has_price_or_stock = self.price is not None or self.availability != Availability.UNKNOWN
        return bool(self.name.strip() and self.product_url.strip() and self.source and has_price_or_stock)

    def sizes_json(self) -> str:
        return json.dumps(self.sizes, ensure_ascii=False)

    def colors_json(self) -> str:
        return json.dumps(self.colors, ensure_ascii=False)

    def raw_attributes_json(self) -> str:
        return json.dumps(self.raw_attributes, ensure_ascii=False)


class ScrapeStats(BaseModel):
    source: str
    ok: int = 0
    errors: int = 0
    skipped: int = 0
