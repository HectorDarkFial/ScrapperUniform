from __future__ import annotations

import sqlite3
from pathlib import Path

from src.models import ProductRecord

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scrape_id TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    source TEXT NOT NULL,
    country TEXT,
    product_url TEXT NOT NULL,
    sku TEXT,
    name TEXT NOT NULL,
    category TEXT,
    price REAL,
    price_display TEXT,
    currency TEXT NOT NULL,
    price_list REAL,
    price_list_display TEXT,
    discount_percent REAL,
    discount_display TEXT,
    price_without_tax REAL,
    price_without_tax_display TEXT,
    price_transfer REAL,
    price_transfer_display TEXT,
    availability TEXT NOT NULL,
    stock_text TEXT,
    sizes TEXT,
    colors TEXT,
    image_url TEXT,
    raw_attributes TEXT,
    UNIQUE(source, product_url)
);

CREATE INDEX IF NOT EXISTS idx_products_source ON products(source);
CREATE INDEX IF NOT EXISTS idx_products_scraped_at ON products(scraped_at);
"""


class Database:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)
            for col, ddl in (
                ("country", "TEXT"),
                ("price_display", "TEXT"),
                ("price_list_display", "TEXT"),
                ("discount_percent", "REAL"),
                ("discount_display", "TEXT"),
                ("price_without_tax", "REAL"),
                ("price_without_tax_display", "TEXT"),
                ("price_transfer", "REAL"),
                ("price_transfer_display", "TEXT"),
            ):
                try:
                    conn.execute(f"ALTER TABLE products ADD COLUMN {col} {ddl}")
                except sqlite3.OperationalError:
                    pass

    def upsert_product(self, record: ProductRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO products (
                    scrape_id, scraped_at, source, country, product_url, sku, name, category,
                    price, price_display, currency, price_list, price_list_display,
                    discount_percent, discount_display,
                    price_without_tax, price_without_tax_display,
                    price_transfer, price_transfer_display,
                    availability, stock_text,
                    sizes, colors, image_url, raw_attributes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, product_url) DO UPDATE SET
                    scrape_id=excluded.scrape_id,
                    scraped_at=excluded.scraped_at,
                    country=excluded.country,
                    name=excluded.name,
                    category=excluded.category,
                    price=excluded.price,
                    price_display=excluded.price_display,
                    currency=excluded.currency,
                    price_list=excluded.price_list,
                    price_list_display=excluded.price_list_display,
                    discount_percent=excluded.discount_percent,
                    discount_display=excluded.discount_display,
                    price_without_tax=excluded.price_without_tax,
                    price_without_tax_display=excluded.price_without_tax_display,
                    price_transfer=excluded.price_transfer,
                    price_transfer_display=excluded.price_transfer_display,
                    availability=excluded.availability,
                    stock_text=excluded.stock_text,
                    sizes=excluded.sizes,
                    colors=excluded.colors,
                    image_url=excluded.image_url,
                    raw_attributes=excluded.raw_attributes
                """,
                (
                    record.scrape_id,
                    record.scraped_at.isoformat(),
                    record.source,
                    record.country,
                    record.product_url,
                    record.sku,
                    record.name,
                    record.category,
                    float(record.price) if record.price is not None else None,
                    record.price_display,
                    record.currency,
                    float(record.price_list) if record.price_list is not None else None,
                    record.price_list_display,
                    float(record.discount_percent)
                    if record.discount_percent is not None
                    else None,
                    record.discount_display,
                    float(record.price_without_tax)
                    if record.price_without_tax is not None
                    else None,
                    record.price_without_tax_display,
                    float(record.price_transfer)
                    if record.price_transfer is not None
                    else None,
                    record.price_transfer_display,
                    record.availability.value,
                    record.stock_text,
                    record.sizes_json(),
                    record.colors_json(),
                    record.image_url,
                    record.raw_attributes_json(),
                ),
            )

    def fetch_all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM products ORDER BY scraped_at DESC").fetchall()
            return [dict(r) for r in rows]

    def fetch_by_scrape_id(self, scrape_id: str) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM products WHERE scrape_id = ? ORDER BY scraped_at DESC",
                (scrape_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def count_by_source(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT source, COUNT(*) as total,
                       SUM(CASE WHEN availability = 'in_stock' THEN 1 ELSE 0 END) as in_stock
                FROM products GROUP BY source
                """
            ).fetchall()
            return [dict(r) for r in rows]
