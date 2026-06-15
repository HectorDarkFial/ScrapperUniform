from src.etl.normalize import build_summary, deduplicate, load_products_df


def test_deduplicate_and_summary():
    rows = [
        {
            "scrape_id": "1",
            "scraped_at": "2026-05-22T10:00:00",
            "source": "a",
            "product_url": "https://x.com/1",
            "sku": "S1",
            "name": "Ambo Test",
            "category": "Sanidad",
            "price": 100.0,
            "currency": "ARS",
            "price_list": None,
            "availability": "in_stock",
            "stock_text": None,
            "sizes": "[]",
            "colors": "[]",
            "image_url": None,
            "raw_attributes": "{}",
        },
        {
            "scrape_id": "2",
            "scraped_at": "2026-05-22T11:00:00",
            "source": "a",
            "product_url": "https://x.com/1",
            "sku": "S1",
            "name": "Ambo Test",
            "category": "Sanidad",
            "price": 110.0,
            "currency": "ARS",
            "price_list": None,
            "availability": "in_stock",
            "stock_text": None,
            "sizes": "[]",
            "colors": "[]",
            "image_url": None,
            "raw_attributes": "{}",
        },
    ]
    df = deduplicate(load_products_df(rows))
    assert len(df) == 1
    summary = build_summary(df)
    assert summary.iloc[0]["Total productos"] == 1
