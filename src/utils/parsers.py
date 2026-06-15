from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from src.models import Availability

PRICE_RE = re.compile(r"[\d.,]+")
AVAILABILITY_PATTERNS: list[tuple[str, Availability]] = [
    ("sin stock", Availability.OUT_OF_STOCK),
    ("no disponible", Availability.OUT_OF_STOCK),
    ("out of stock", Availability.OUT_OF_STOCK),
    ("outofstock", Availability.OUT_OF_STOCK),
    ("agotado", Availability.OUT_OF_STOCK),
    ("preventa", Availability.PREORDER),
    ("preorder", Availability.PREORDER),
    ("en stock", Availability.IN_STOCK),
    ("in stock", Availability.IN_STOCK),
    ("instock", Availability.IN_STOCK),
    ("disponible", Availability.IN_STOCK),
]


def parse_price(text: str | None, *, currency: str = "ARS") -> Decimal | None:
    if not text:
        return None
    cleaned = text.strip()
    cleaned = re.sub(r"[^\d.,]", "", cleaned)
    if not cleaned:
        return None

    cur = (currency or "ARS").upper()
    if cur == "CLP":
        if "," in cleaned:
            cleaned = cleaned.replace(".", "").replace(",", "")
        elif "." in cleaned:
            parts = cleaned.split(".")
            if len(parts) > 1 and all(len(p) == 3 for p in parts[1:]):
                cleaned = "".join(parts)
            elif len(parts) == 2 and len(parts[1]) == 3:
                cleaned = parts[0] + parts[1]
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts[-1]) == 2:
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        int_part, frac = cleaned.rsplit(".", 1)
        if len(frac) == 3 and frac.isdigit():
            cleaned = int_part + frac
        elif len(frac) == 2 and frac.isdigit():
            cleaned = f"{int_part}.{frac}"
        else:
            cleaned = cleaned.replace(".", "")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def parse_availability(text: str | None) -> Availability:
    if not text:
        return Availability.UNKNOWN
    key = text.strip().lower()
    for pattern, avail in AVAILABILITY_PATTERNS:
        if pattern in key:
            return avail
    return Availability.UNKNOWN


def parse_schema_availability(url: str | None) -> Availability:
    if not url:
        return Availability.UNKNOWN
    lower = url.lower()
    if "instock" in lower or "in_stock" in lower:
        return Availability.IN_STOCK
    if "outofstock" in lower or "out_of_stock" in lower:
        return Availability.OUT_OF_STOCK
    if "preorder" in lower:
        return Availability.PREORDER
    return Availability.UNKNOWN


def extract_sizes_colors(text_blocks: list[str]) -> tuple[list[str], list[str]]:
    sizes: list[str] = []
    colors: list[str] = []
    size_re = re.compile(r"\b(XXS|XS|S|M|L|XL|XXL|XXXL|\d{2,3})\b", re.I)
    for block in text_blocks:
        for m in size_re.findall(block):
            val = m.upper() if m.isalpha() else m
            if val not in sizes:
                sizes.append(val)
    return sizes, colors


def infer_availability_from_soup(soup, current: Availability) -> Availability:
    """
    Refuerza la disponibilidad con señales reales de la página (botón de compra + texto).
    Útil cuando el JSON-LD no coincide con el estado visual del producto.
    """
    if soup is None:
        return current

    def _is_disabled(el) -> bool:
        if not el:
            return False
        if el.has_attr("disabled"):
            return True
        aria = (el.get("aria-disabled") or "").strip().lower()
        if aria in ("true", "1", "disabled"):
            return True
        cls = " ".join(el.get("class", [])).lower()
        return any(k in cls for k in ("disabled", "is-disabled", "btn-disabled", "button--disabled"))

    buy_selectors = [
        "button[type='submit']",
        "button[name='add']",
        "button.add-to-cart",
        ".add-to-cart button",
        ".product-form__submit",
        ".js-addtocart",
        ".js-add-to-cart",
        ".product-buy-button",
        ".single_add_to_cart_button",
    ]
    for sel in buy_selectors:
        btn = soup.select_one(sel)
        if not btn:
            continue
        text = (btn.get_text(" ", strip=True) or "").lower()
        if any(k in text for k in ("agotado", "sin stock", "no disponible", "sold out")):
            return Availability.OUT_OF_STOCK
        if _is_disabled(btn) and any(k in text for k in ("agregar", "comprar", "carrito", "add to cart")):
            return Availability.OUT_OF_STOCK
        if not _is_disabled(btn) and any(k in text for k in ("agregar", "comprar", "carrito", "add to cart")):
            return Availability.IN_STOCK

    text_selectors = [
        ".stock",
        ".product__inventory",
        ".product-form__inventory",
        ".js-stock-label",
        ".product-stock",
        "#stock",
        "[class*='stock']",
        "[class*='inventory']",
        "[data-stock]",
    ]
    blocks: list[str] = []
    for sel in text_selectors:
        for el in soup.select(sel)[:10]:
            t = (el.get_text(" ", strip=True) or "").strip()
            if t and len(t) <= 300:
                blocks.append(t)
    merged = " · ".join(blocks).lower()
    if merged:
        parsed = parse_availability(merged)
        if parsed != Availability.UNKNOWN:
            return parsed

    return current
