from __future__ import annotations

import json
import re
from datetime import datetime

import pandas as pd

from pathlib import Path

from src.config_loader import ROOT
from src.models import Availability
from src.providers import canonical_source
from src.utils.parsers import parse_availability
from src.utils.url_security import check_url, sanitize_excel_value, trust_label_es

EXPORT_TIMESTAMP_FMT = "%d-%m-%Y-%H-%M-%S"

PRODUCT_COLUMNS_ES = [
    ("country", "País"),
    ("source", "Proveedor"),
    ("currency", "Moneda"),
    ("name", "Producto"),
    ("category", "Categoría"),
    ("price_list_display", "Precio original (sitio)"),
    ("price_list", "Precio original numérico"),
    ("discount_display", "Descuento (sitio)"),
    ("discount_percent", "Descuento %"),
    ("price_display", "Precio con descuento (sitio)"),
    ("price", "Precio con descuento numérico"),
    ("url_trust_label", "Estado URL"),
    ("product_url", "URL verificación"),
    ("availability", "Disponibilidad"),
    ("sku", "SKU"),
    ("image_url", "URL imagen"),
    ("scraped_at", "Fecha scrape"),
    ("stock_text", "Descripción"),
    ("sizes", "Tallas"),
    ("colors", "Colores"),
]

SUMMARY_COLUMNS_ES = [
    ("country", "País"),
    ("source", "Proveedor"),
    ("total", "Total productos"),
    ("price_mean", "Precio promedio"),
    ("price_min", "Precio mínimo"),
    ("price_max", "Precio máximo"),
    ("in_stock_pct", "% en stock"),
]


def export_timestamp() -> str:
    """Marca de tiempo para nombres de archivo: dia-mes-año-hora-minuto-segundo."""
    return datetime.now().strftime(EXPORT_TIMESTAMP_FMT)


def _write_table(df: pd.DataFrame, path: Path, fmt: str) -> None:
    if fmt == "xlsx":
        df.to_excel(path, index=False, engine="openpyxl")
    elif fmt == "csv":
        df.to_csv(path, index=False, encoding="utf-8-sig")
    else:
        raise ValueError(f"Formato no soportado para tabla: {fmt}")


NORMALIZE_AVAIL = {
    "in_stock": Availability.IN_STOCK,
    "out_of_stock": Availability.OUT_OF_STOCK,
    "unknown": Availability.UNKNOWN,
    "preorder": Availability.PREORDER,
}


def load_products_df(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if "source" in df.columns:
        df["source"] = df["source"].apply(lambda s: canonical_source(str(s)) if s else s)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["price_list"] = pd.to_numeric(df["price_list"], errors="coerce")
    df["availability"] = df["availability"].apply(_normalize_avail_column)
    df["normalized_name"] = df["name"].apply(_normalize_name)
    return df


def _normalize_avail_column(val: str) -> str:
    if val in NORMALIZE_AVAIL:
        return val
    parsed = parse_availability(str(val))
    return parsed.value


def _normalize_name(name: str) -> str:
    text = name.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\w\sáéíóúñ]", "", text, flags=re.I)
    return text


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    key = df["sku"].fillna("") + "|" + df["source"] + "|" + df["normalized_name"]
    df = df.copy()
    df["_dedup_key"] = key
    return df.sort_values("scraped_at", ascending=False).drop_duplicates("_dedup_key").drop(
        columns=["_dedup_key"]
    )


def _country_sort_key(df: pd.DataFrame) -> pd.DataFrame:
    """Chile primero, luego Argentina, resto al final."""
    if df.empty or "country" not in df.columns:
        return df
    order = {"CL": 0, "AR": 1}
    out = df.copy()
    out["_ord"] = out["country"].map(order).fillna(9)
    out = out.sort_values(["_ord", "source", "name"], na_position="last").drop(columns=["_ord"])
    return out


def _rename_columns(df: pd.DataFrame, mapping: list[tuple[str, str]]) -> pd.DataFrame:
    cols = {k: v for k, v in mapping if k in df.columns}
    return df.rename(columns=cols)


def _attach_url_trust_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "product_url" not in df.columns:
        return df
    out = df.copy()
    labels: list[str] = []
    safe_urls: list[str] = []
    for _, row in out.iterrows():
        check = check_url(str(row.get("product_url") or ""), purpose="export")
        labels.append(trust_label_es(check.trust.value))
        safe_urls.append(check.url if check.safe_for_export else "")
    out["url_trust_label"] = labels
    out["product_url"] = safe_urls
    return out


def _sanitize_export_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(sanitize_excel_value)
    return out


def _products_export_frame(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    work = _attach_url_trust_columns(df)
    cols = [c for c, _ in PRODUCT_COLUMNS_ES if c in work.columns]
    out = _country_sort_key(work[cols].copy())
    if "country" in out.columns:
        out["country"] = out["country"].replace({"CL": "Chile", "AR": "Argentina"})
    if "currency" in out.columns:
        out.loc[out["country"] == "Chile", "currency"] = out.loc[
            out["country"] == "Chile", "currency"
        ].fillna("CLP")
        out.loc[out["country"] == "Argentina", "currency"] = out.loc[
            out["country"] == "Argentina", "currency"
        ].fillna("ARS")
    out = _rename_columns(out, PRODUCT_COLUMNS_ES)
    return _sanitize_export_frame(out)


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    group_cols = ["source"]
    if "country" in df.columns and df["country"].notna().any():
        group_cols = ["country", "source"]
    grouped = (
        df.groupby(group_cols)
        .agg(
            total=("scrape_id", "count"),
            price_mean=("price", "mean"),
            price_min=("price", "min"),
            price_max=("price", "max"),
            in_stock_pct=("availability", lambda s: (s == "in_stock").mean() * 100),
        )
        .reset_index()
    )
    grouped["price_mean"] = grouped["price_mean"].round(2)
    grouped["in_stock_pct"] = grouped["in_stock_pct"].round(1)
    if "country" in grouped.columns:
        grouped["country"] = grouped["country"].replace({"CL": "Chile", "AR": "Argentina"})
    return _country_sort_key(_rename_columns(grouped, SUMMARY_COLUMNS_ES))


def _export_xlsx_workbook(
    products: pd.DataFrame,
    summary: pd.DataFrame,
    out_path: Path,
) -> None:
    """Un solo Excel estructurado (más rápido que varios archivos)."""
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        products.to_excel(writer, sheet_name="Productos", index=False)
        if not summary.empty:
            for country_name in ("Chile", "Argentina"):
                part = summary[summary["País"] == country_name] if "País" in summary.columns else pd.DataFrame()
                if not part.empty:
                    sheet = "Resumen_Chile" if country_name == "Chile" else "Resumen_Argentina"
                    part.to_excel(writer, sheet_name=sheet[:31], index=False)
            summary.to_excel(writer, sheet_name="Resumen_General", index=False)


def export_analysis(
    rows: list[dict],
    export_dir: str | None = None,
    fmt: str = "csv",
) -> dict[str, str]:
    """Exporta datos ordenados (Chile primero), columnas en español."""
    out_dir = ROOT / (export_dir or "data/exports")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = export_timestamp()
    fmt = fmt.lower()
    if fmt not in ("csv", "xlsx", "parquet"):
        raise ValueError(f"Formato inválido: {fmt}. Usá csv, xlsx o parquet.")

    from src.utils.export_security import filter_rows_for_export

    safe_rows = filter_rows_for_export(rows)
    if not safe_rows:
        raise ValueError(
            "No hay productos exportables (necesitan precio y URL de un proveedor configurado)."
        )
    df = deduplicate(load_products_df(safe_rows))
    products_es = _products_export_frame(df.drop(columns=["raw_attributes", "normalized_name"], errors="ignore"))
    summary_es = _sanitize_export_frame(build_summary(df))
    paths: dict[str, str] = {}

    if fmt == "xlsx":
        xlsx_path = out_dir / f"informe_uniformes_{stamp}.xlsx"
        _export_xlsx_workbook(products_es, summary_es, xlsx_path)
        paths["informe"] = str(xlsx_path)
        return paths

    ext = "parquet" if fmt == "parquet" else "csv"
    products_path = out_dir / f"productos_{stamp}.{ext}"
    if fmt == "parquet":
        products_es.to_parquet(products_path, index=False)
    else:
        _write_table(products_es, products_path, fmt)
    paths["productos"] = str(products_path)

    if not summary_es.empty:
        summary_path = out_dir / f"resumen_proveedores_{stamp}.{ext}"
        if fmt == "parquet":
            summary_es.to_parquet(summary_path, index=False)
        else:
            _write_table(summary_es, summary_path, fmt)
        paths["resumen"] = str(summary_path)

    return paths
