from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from src.utils.parsers import parse_price

DISCOUNT_TEXT_RE = re.compile(
    r"(?:(\d{1,3})\s*%\s*(?:off|dto\.?|descuento)?|(?:descuento|ahorr[aá]s?)\s*(?:del?\s*)?(\d{1,3})\s*%)",
    re.IGNORECASE,
)

WITHOUT_TAX_RE = re.compile(
    r"precio\s+unitario|unitario\s*(?:por\s+unidad)?|por\s+unidad",
    re.IGNORECASE,
)

TRANSFER_RE = re.compile(
    r"(?:precio\s+)?(?:en\s+)?transferencia|pago\s+en\s+efectivo|precio\s+efectivo|d[eé]bito|dep[oó]sito",
    re.IGNORECASE,
)


@dataclass
class ExtractedPrices:
    """Desglose de precios tal como aparece en la tienda."""

    price: Decimal | None = None
    price_display: str | None = None
    price_list: Decimal | None = None
    price_list_display: str | None = None
    discount_percent: Decimal | None = None
    discount_display: str | None = None
    price_without_tax: Decimal | None = None
    price_without_tax_display: str | None = None
    price_transfer: Decimal | None = None
    price_transfer_display: str | None = None
    source: str = "none"
    extra_labels: dict[str, str] = field(default_factory=dict)


def parse_price_exact(value: Any, *, currency: str = "ARS") -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    text = str(value).strip()
    if re.fullmatch(r"\d+(\.\d+)?", text):
        return Decimal(text)
    return parse_price(text, currency=currency)


def _clean_display(text: str | None) -> str | None:
    if not text:
        return None
    cleaned = re.sub(r"\s+", " ", text.strip())
    return cleaned or None


def _compact_currency_space(text: str) -> str:
    return re.sub(r"(\$)\s+(\d)", r"\1\2", text)


def _price_only_display(text: str | None, currency: str) -> str | None:
    cleaned = _clean_display(text)
    if not cleaned:
        return None
    currency_code = (currency or "").upper()
    patterns = [
        r"\$\s*\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?",
        r"\d{1,3}(?:[.\s]\d{3})*(?:,\d{2})?\s*(?:CLP|ARS)",
    ]
    if currency_code:
        patterns.insert(0, rf"\$\s*\d[\d\.\s,]*\s*{currency_code}")
    for pattern in patterns:
        match = re.search(pattern, cleaned, flags=re.IGNORECASE)
        if match:
            return _compact_currency_space(_clean_display(match.group(0)) or "")
    parsed = parse_price(cleaned, currency=currency_code or "ARS")
    if parsed is not None:
        return _format_display(parsed, currency_code or "ARS")
    return cleaned


def _format_display(amount: Decimal, currency: str) -> str:
    cur = currency.upper()
    if cur == "CLP":
        return f"${int(amount):,}".replace(",", ".")
    q = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    int_part, _, frac = f"{q:.2f}".partition(".")
    return f"${int(int_part):,},{frac}".replace(",", "X").replace(".", ",").replace("X", ".")


def parse_discount_from_text(text: str | None) -> tuple[Decimal | None, str | None]:
    if not text:
        return None, None
    match = DISCOUNT_TEXT_RE.search(text)
    if not match:
        badge = re.search(r"(\d{1,3})\s*%", text)
        if badge and re.search(r"(off|dto|desc|ahorr)", text, re.I):
            pct = Decimal(badge.group(1))
            return pct, _clean_display(badge.group(0))
        return None, None
    pct_raw = match.group(1) or match.group(2)
    pct = Decimal(pct_raw)
    return pct, _clean_display(match.group(0))


def compute_discount_percent(
    original: Decimal | None, sale: Decimal | None
) -> Decimal | None:
    if original is None or sale is None or original <= 0 or sale >= original:
        return None
    pct = (original - sale) / original * Decimal(100)
    return pct.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def first_visible_price_text(soup, selectors: list[str]) -> str | None:
    for sel in selectors:
        el = soup.select_one(sel)
        if el:
            text = _clean_display(el.get_text())
            if text and re.search(r"\d", text):
                return text
    return None


def collect_discount_badges(soup) -> str | None:
    selectors = [
        ".js-offer-percentage",
        ".label-offer",
        ".discount-badge",
        "[class*='discount']",
        "[class*='dto']",
        ".product-promo",
        ".sale-badge",
    ]
    parts: list[str] = []
    for sel in selectors:
        for el in soup.select(sel):
            t = _clean_display(el.get_text())
            if t and "%" in t and t not in parts:
                parts.append(t)
    return " · ".join(parts) if parts else None


def _price_near_label(block_text: str, currency: str) -> Decimal | None:
    if not block_text or not re.search(r"\d", block_text):
        return None
    amounts: list[Decimal] = []
    for chunk in re.split(r"[|•\n]", block_text):
        parsed = parse_price(chunk, currency=currency)
        if parsed is not None:
            amounts.append(parsed)
    if not amounts:
        parsed = parse_price(block_text, currency=currency)
        if parsed is not None:
            amounts.append(parsed)
    return amounts[0] if amounts else None


def scan_labeled_prices(soup, currency: str) -> dict[str, tuple[Decimal | None, str | None]]:
    found: dict[str, tuple[Decimal | None, str | None]] = {}
    candidates = soup.select(
        '[class*="price"], [class*="precio"], [class*="payment"], '
        '[class*="pago"], [class*="transfer"], li, p, span, div'
    )
    for el in candidates:
        text = _clean_display(el.get_text(" ", strip=True))
        if not text or len(text) > 280 or not re.search(r"\d", text):
            continue
        lower = text.lower()
        parsed = _price_near_label(text, currency)
        if parsed is None:
            continue
        display = text
        if WITHOUT_TAX_RE.search(lower) and "without_tax" not in found:
            found["without_tax"] = (parsed, display)
        if TRANSFER_RE.search(lower) and "transfer" not in found:
            found["transfer"] = (parsed, display)
    return found


def resolve_product_prices(
    *,
    currency: str,
    offers: dict[str, Any] | None = None,
    sale_html_text: str | None = None,
    list_html_text: str | None = None,
    soup: Any | None = None,
    discount_html_text: str | None = None,
) -> ExtractedPrices:
    """
    Precio de venta, precio original, descuento, sin impuestos y transferencia.
    Prioridad numérica: JSON-LD → HTML etiquetado → selectores de precio.
    """
    result = ExtractedPrices()
    cur = (currency or "ARS").upper()
    sale_text = _clean_display(sale_html_text)
    list_text = _clean_display(list_html_text)
    discount_text = _clean_display(discount_html_text)

    if offers:
        raw_sale = offers.get("price")
        if raw_sale is None and offers.get("lowPrice") is not None:
            raw_sale = offers.get("lowPrice")
        if raw_sale is not None:
            parsed = parse_price_exact(raw_sale, currency=cur)
            if parsed is not None:
                result.price = parsed
                result.price_display = _price_only_display(sale_text, cur) or _clean_display(
                    str(raw_sale)
                )
                result.source = "json_ld"
        raw_list = offers.get("highPrice")
        if raw_list is not None and str(raw_list) != str(raw_sale):
            parsed_list = parse_price_exact(raw_list, currency=cur)
            if parsed_list is not None:
                result.price_list = parsed_list
                result.price_list_display = _price_only_display(list_text, cur) or _clean_display(
                    str(raw_list)
                )

    if result.price is None and sale_text:
        parsed = parse_price(sale_text, currency=cur)
        if parsed is not None:
            result.price = parsed
            result.price_display = _price_only_display(sale_text, cur)
            result.source = "html"

    if result.price_list is None and list_text:
        parsed_list = parse_price(list_text, currency=cur)
        if parsed_list is not None:
            result.price_list = parsed_list
            result.price_list_display = _price_only_display(list_text, cur)

    if soup is not None:
        if not discount_text:
            discount_text = collect_discount_badges(soup)
        labeled = scan_labeled_prices(soup, cur)
        if "without_tax" in labeled:
            result.price_without_tax, result.price_without_tax_display = labeled["without_tax"]
        if "transfer" in labeled:
            result.price_transfer, result.price_transfer_display = labeled["transfer"]

    if discount_text:
        pct, disp = parse_discount_from_text(discount_text)
        if pct is not None:
            result.discount_percent = pct
            result.discount_display = disp
        elif result.discount_display is None:
            result.discount_display = discount_text

    if result.discount_percent is None:
        computed = compute_discount_percent(result.price_list, result.price)
        if computed is not None:
            result.discount_percent = computed
            if not result.discount_display:
                result.discount_display = f"{computed}% OFF"

    if result.price_display is None and result.price is not None:
        result.price_display = _format_display(result.price, cur)
    if result.price_list_display is None and result.price_list is not None:
        result.price_list_display = _format_display(result.price_list, cur)

    return result


def apply_price_breakdown(record: Any, extracted: ExtractedPrices) -> None:
    """Copia el desglose al ProductRecord."""
    record.price = extracted.price
    record.price_display = extracted.price_display
    record.price_list = extracted.price_list
    record.price_list_display = extracted.price_list_display
    record.discount_percent = extracted.discount_percent
    record.discount_display = extracted.discount_display
    record.price_without_tax = extracted.price_without_tax
    record.price_without_tax_display = extracted.price_without_tax_display
    record.price_transfer = extracted.price_transfer
    record.price_transfer_display = extracted.price_transfer_display
    attrs = dict(record.raw_attributes or {})
    attrs["price_source"] = extracted.source
    if extracted.extra_labels:
        attrs["price_labels"] = extracted.extra_labels
    record.raw_attributes = attrs
