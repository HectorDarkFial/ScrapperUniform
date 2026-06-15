#!/usr/bin/env python3
"""
Herramienta de desarrollo: inspecciona HTML/JSON-LD de sitios nuevos.

Uso: python scripts/dev/probe_sites.py
No forma parte del flujo de producción.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

ua = {"User-Agent": "UniformScraper/1.0"}


def probe_product(url: str) -> None:
    r = httpx.get(url, headers=ua, timeout=25)
    soup = BeautifulSoup(r.text, "lxml")
    print(f"\n=== {url} status={r.status_code} ===")
    for sc in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(sc.string or "")
            items = data if isinstance(data, list) else [data]
            if isinstance(data, dict) and "@graph" in data:
                items = data["@graph"]
            for item in items:
                if item.get("@type") == "Product":
                    offers = item.get("offers", {})
                    if isinstance(offers, list):
                        offers = offers[0] if offers else {}
                    print("  name:", item.get("name"))
                    print("  price:", offers.get("price"), offers.get("priceCurrency"))
        except json.JSONDecodeError:
            pass


def probe_catalog(url: str, pattern: str) -> None:
    r = httpx.get(url, headers=ua, timeout=25)
    soup = BeautifulSoup(r.text, "lxml")
    links = [a.get("href", "") for a in soup.select("a[href]") if pattern in a.get("href", "")]
    print(f"\n=== catalog {url} ===")
    print("  links:", list(dict.fromkeys(links))[:6])


def probe_scorpi_price(url: str) -> None:
    r = httpx.get(url, headers=ua, timeout=25)
    prices = re.findall(r'"price"\s*:\s*"?(\d+)"?', r.text)
    soup = BeautifulSoup(r.text, "lxml")
    h1 = soup.select_one("h1")
    price_el = soup.select_one(".price, .product-price")
    print(f"\n=== scorpi {url} ===")
    print("  h1:", h1.get_text(strip=True) if h1 else None)
    print("  html price:", price_el.get_text(strip=True) if price_el else None)
    print("  json prices:", prices[:3])


if __name__ == "__main__":
    probe_product("https://www.suitmed.cl/products/polera-clinica-mujer-astro-1103")
    probe_catalog("https://www.suitmed.cl/collections/all", "/products/")
    probe_catalog("https://scrubplus.cl/tienda/", "/producto/")
    probe_scorpi_price("https://www.scorpi.cl/products/top-mujer-elements-copia")
