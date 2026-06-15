from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.db.models import Avg, Count, Q
from django.http import FileResponse, Http404, HttpRequest, JsonResponse
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods

from portal.models import Product, ScrapeJob, Site
from portal.export_gate import assess_export_readiness
from portal.services import (
    import_sites_from_yaml,
    scrape_limits_from_settings,
    start_export_job,
    start_scrape_job,
    stop_job,
    sync_site_to_yaml,
)
from src.providers import (
    aggregate_provider_counts,
    canonical_source,
    clear_provider_cache,
    display_name_for_slug,
    validate_provider_name_unique,
)
from src.utils.url_security import UrlTrust, check_url, normalize_http_url, trust_label_es


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"error": message}, status=status)


def _exports_dir() -> Path:
    return Path(settings.BASE_DIR) / "data" / "exports"


def _safe_export_path(name: str) -> Path | None:
    """Resuelve un archivo dentro de data/exports sin permitir path traversal."""
    clean = (name or "").strip()
    if not clean or clean != Path(clean).name or ".." in clean:
        return None
    base = _exports_dir().resolve()
    path = (base / clean).resolve()
    if not path.is_file() or base not in path.parents:
        return None
    return path


def _validate_site_urls(base_url: str, catalog_urls: list) -> str | None:
    base_check = check_url(base_url, purpose="general")
    if base_check.trust == UrlTrust.BLOCKED:
        return f"URL base rechazada: {base_check.reason}"
    for raw in catalog_urls:
        u = str(raw).strip()
        if not u:
            continue
        cat_check = check_url(u, purpose="general")
        if cat_check.trust == UrlTrust.BLOCKED:
            return f"URL de catálogo rechazada: {cat_check.reason}"
    return None


@ensure_csrf_cookie
@require_GET
def api_csrf(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"ok": True})


def _site_to_provider(site: Site) -> dict:
    product_count = Product.objects.filter(source=site.slug).count()
    last_job = (
        ScrapeJob.objects.filter(site_slug=site.slug, status=ScrapeJob.Status.DONE)
        .order_by("-finished_at")
        .first()
    )
    last_scrape = last_job.finished_at.isoformat() if last_job and last_job.finished_at else None
    if not last_scrape:
        latest_product = Product.objects.filter(source=site.slug).order_by("-scraped_at").first()
        if latest_product:
            last_scrape = latest_product.scraped_at.isoformat()

    return {
        "id": site.slug,
        "slug": site.slug,
        "name": site.name,
        "country": site.country,
        "baseUrl": site.base_url,
        "catalogUrls": site.catalog_urls_list(),
        "isActive": site.enabled,
        "scraper": site.scraper,
        "currency": site.currency,
        "productLinkPattern": site.product_link_pattern,
        "delaySeconds": site.delay_seconds,
        "notes": site.notes,
        "lastScrape": last_scrape,
        "productsCount": product_count,
    }


def _product_to_json(p: Product) -> dict:
    avail = p.availability or "unknown"
    if avail in ("in_stock", "in-stock"):
        availability = "in-stock"
    elif avail in ("out_of_stock", "out-of-stock"):
        availability = "out-of-stock"
    else:
        availability = "low-stock" if avail else "in-stock"

    category = (p.category or "scrubs").lower()
    if "guardapolvo" in category or "bata" in category:
        cat = "lab-coats"
    elif "calzado" in category or "zapato" in category:
        cat = "shoes"
    elif "accesorio" in category:
        cat = "accessories"
    else:
        cat = "scrubs"

    price_display = getattr(p, "price_display", None) or None
    price_list_display = getattr(p, "price_list_display", None) or None

    url_trust = UrlTrust.TRUSTED.value
    if p.raw_attributes:
        try:
            attrs = json.loads(p.raw_attributes)
            url_trust = attrs.get("url_trust", url_trust)
        except json.JSONDecodeError:
            pass
    url_check = check_url(p.product_url, purpose="export")

    return {
        "id": str(p.pk),
        "name": p.name,
        "category": cat,
        "provider": display_name_for_slug(canonical_source(p.source)),
        "providerSlug": canonical_source(p.source),
        "stockText": p.stock_text or None,
        "price": float(p.price) if p.price is not None else None,
        "priceDisplay": price_display,
        "priceList": float(p.price_list) if p.price_list is not None else None,
        "priceListDisplay": price_list_display,
        "discountPercent": float(p.discount_percent)
        if getattr(p, "discount_percent", None) is not None
        else None,
        "discountDisplay": getattr(p, "discount_display", None),
        "priceWithoutTax": float(p.price_without_tax)
        if getattr(p, "price_without_tax", None) is not None
        else None,
        "priceWithoutTaxDisplay": getattr(p, "price_without_tax_display", None),
        "priceTransfer": float(p.price_transfer)
        if getattr(p, "price_transfer", None) is not None
        else None,
        "priceTransferDisplay": getattr(p, "price_transfer_display", None),
        "currency": p.currency or "ARS",
        "availability": availability,
        "url": url_check.url,
        "verifyUrl": url_check.url,
        "urlTrust": url_check.trust.value,
        "urlTrustLabel": trust_label_es(url_check.trust.value),
        "safeToOpen": url_check.trust == UrlTrust.TRUSTED and url_check.safe_for_export,
        "imageUrl": p.image_url or None,
        "lastUpdated": p.scraped_at.isoformat(),
        "priceHistory": [
            {"date": p.scraped_at.isoformat(), "price": float(p.price)}
        ]
        if p.price is not None
        else [],
    }


def _site_slugs_by_country() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {"AR": [], "CL": []}
    for slug, country in Site.objects.values_list("slug", "country"):
        if country in result:
            result[country].append(slug)
    return result


def _products_queryset(country: str | None = None):
    """Productos filtrados por país (campo country o proveedor asociado)."""
    qs = Product.objects.all()
    if country not in ("AR", "CL"):
        return qs
    slugs = _site_slugs_by_country().get(country, [])
    return qs.filter(Q(country=country) | Q(source__in=slugs))


def _build_metrics_payload(qs, country: str | None) -> dict:
    slugs_map = _site_slugs_by_country()
    site_country = {}
    for c, slugs in slugs_map.items():
        for s in slugs:
            site_country[s] = c

    total_products = qs.count()
    if country in ("AR", "CL"):
        active_providers = Site.objects.filter(enabled=True, country=country).count()
        currency = "CLP" if country == "CL" else "ARS"
    else:
        active_providers = Site.objects.filter(enabled=True).count()
        currency = "MIXED"

    avg_row = qs.exclude(price__isnull=True).aggregate(avg=Avg("price"))
    avg_price = float(avg_row["avg"] or 0)

    since = timezone.now() - timedelta(hours=24)
    price_changes_24h = qs.filter(scraped_at__gte=since).count()

    latest = qs.order_by("-scraped_at").first()
    last_update = latest.scraped_at.isoformat() if latest else None

    category_rows = (
        qs.exclude(category__isnull=True)
        .exclude(category="")
        .values("category")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )
    category_data = [
        {"name": row["category"] or "Sin categoría", "value": row["count"]}
        for row in category_rows
    ]

    raw_sources = list(qs.values_list("source", flat=True))
    provider_data = aggregate_provider_counts(raw_sources)[:12]

    top_price = (
        qs.exclude(price__isnull=True).order_by("-price")[:5].values("name", "price", "currency")
    )
    price_data = [
        {
            "name": (row["name"][:22] + "...") if len(row["name"]) > 25 else row["name"],
            "precio": float(row["price"] or 0),
            "currency": row["currency"] or currency,
        }
        for row in top_price
    ]

    history = []
    for day_offset in range(7, -1, -1):
        day = (timezone.now() - timedelta(days=day_offset)).date()
        day_avg = qs.filter(scraped_at__date=day).aggregate(avg=Avg("price"))
        if day_avg["avg"]:
            history.append(
                {
                    "fecha": day.strftime("%d %b"),
                    "promedio": round(float(day_avg["avg"]), 0),
                }
            )

    country_compare = []
    if country is None:
        for c, label in (("CL", "Chile"), ("AR", "Argentina")):
            slugs = _site_slugs_by_country().get(c, [])
            cqs = qs.filter(Q(country=c) | Q(source__in=slugs))
            moneda = "CLP" if c == "CL" else "ARS"
            country_compare.append(
                {
                    "country": c,
                    "label": label,
                    "currency": moneda,
                    "productos": cqs.count(),
                    "proveedores": Site.objects.filter(enabled=True, country=c).count(),
                    "precioPromedio": round(
                        float(
                            cqs.exclude(price__isnull=True).aggregate(avg=Avg("price"))["avg"] or 0
                        ),
                        0,
                    ),
                }
            )

    return {
        "country": country or "all",
        "currency": currency,
        "totalProducts": total_products,
        "activeProviders": active_providers,
        "avgPrice": round(avg_price, 2),
        "lastUpdate": last_update,
        "priceChanges24h": price_changes_24h,
        "hasData": total_products > 0,
        "charts": {
            "categoryData": category_data,
            "providerData": provider_data,
            "priceData": price_data,
            "priceHistoryData": history,
            "countryCompare": country_compare,
        },
    }


@require_GET
def api_metrics(request: HttpRequest) -> JsonResponse:
    if Site.objects.count() == 0:
        import_sites_from_yaml()

    country = request.GET.get("country", "all").upper()
    if country not in ("AR", "CL"):
        country = None

    last_job = (
        ScrapeJob.objects.filter(job_type="scrape")
        .exclude(result_json="")
        .order_by("-finished_at", "-created_at")
        .first()
    )
    scrape_run_id: str | None = None
    if last_job and last_job.result_json:
        try:
            data = json.loads(last_job.result_json)
            scrape_run_id = data.get("scrapeRunId") or None
        except json.JSONDecodeError:
            scrape_run_id = None

    if scrape_run_id:
        base_qs = Product.objects.filter(scrape_id=scrape_run_id)
        if country in ("AR", "CL"):
            slugs = _site_slugs_by_country().get(country, [])
            qs = base_qs.filter(Q(country=country) | Q(source__in=slugs))
        else:
            qs = base_qs
    else:
        qs = _products_queryset(country)

    payload = _build_metrics_payload(qs, country)

    if country is None:
        if scrape_run_id:
            qs_ar = Product.objects.filter(
                scrape_id=scrape_run_id
            ).filter(Q(country="AR") | Q(source__in=_site_slugs_by_country().get("AR", [])))
            qs_cl = Product.objects.filter(
                scrape_id=scrape_run_id
            ).filter(Q(country="CL") | Q(source__in=_site_slugs_by_country().get("CL", [])))
            payload["byCountry"] = {
                "AR": _build_metrics_payload(qs_ar, "AR"),
                "CL": _build_metrics_payload(qs_cl, "CL"),
            }
        else:
            payload["byCountry"] = {
                "AR": _build_metrics_payload(_products_queryset("AR"), "AR"),
                "CL": _build_metrics_payload(_products_queryset("CL"), "CL"),
            }

    return JsonResponse(payload)


@require_GET
def api_sites(request: HttpRequest) -> JsonResponse:
    if Site.objects.count() == 0:
        import_sites_from_yaml()
    sites = Site.objects.all()
    country = request.GET.get("country", "").upper()
    if country in ("AR", "CL"):
        sites = sites.filter(country=country)
    return JsonResponse({"providers": [_site_to_provider(s) for s in sites]})


@require_http_methods(["POST"])
def api_site_create(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error("JSON inválido")

    name = (data.get("name") or "").strip()
    base_url = (data.get("baseUrl") or "").strip()
    catalog_urls = data.get("catalogUrls") or []
    country = data.get("country", "AR")
    if not name or not base_url:
        return _json_error("Nombre y URL base son obligatorios")

    url_err = _validate_site_urls(base_url, catalog_urls)
    if url_err:
        return _json_error(url_err)
    base_url = normalize_http_url(base_url) or base_url
    catalog_urls = [
        normalize_http_url(str(u).strip()) or str(u).strip()
        for u in catalog_urls
        if u and str(u).strip()
    ]

    dup_msg = validate_provider_name_unique(name, country)
    if dup_msg:
        return _json_error(dup_msg)

    slug = (data.get("slug") or slugify(name)).strip() or slugify(name)
    if Site.objects.filter(slug=slug).exists():
        slug = f"{slug}-{Site.objects.count() + 1}"

    catalog_text = "\n".join(u.strip() for u in catalog_urls if u and str(u).strip())
    if not catalog_text:
        return _json_error("Al menos una URL de catálogo")

    site = Site.objects.create(
        slug=slug,
        name=name,
        enabled=data.get("isActive", True),
        country=data.get("country", "AR"),
        base_url=base_url,
        catalog_urls=catalog_text,
        scraper=data.get("scraper", Site.Scraper.TIENDANUBE),
        currency=data.get("currency", "ARS" if data.get("country", "AR") == "AR" else "CLP"),
        product_link_pattern=data.get("productLinkPattern", "/productos/"),
        delay_seconds=float(data.get("delaySeconds", 2.0)),
        notes=data.get("notes", ""),
    )
    sync_site_to_yaml(site)
    clear_provider_cache()
    return JsonResponse({"provider": _site_to_provider(site)}, status=201)


@require_http_methods(["PUT", "PATCH"])
def api_site_update(request: HttpRequest, slug: str) -> JsonResponse:
    site = Site.objects.filter(slug=slug).first()
    if not site:
        return _json_error("Proveedor no encontrado", 404)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error("JSON inválido")

    if "name" in data:
        new_name = data["name"].strip()
        dup_msg = validate_provider_name_unique(new_name, site.country, exclude_slug=site.slug)
        if dup_msg:
            return _json_error(dup_msg)
        site.name = new_name
    if "baseUrl" in data:
        new_base = data["baseUrl"].strip()
        url_err = _validate_site_urls(new_base, site.catalog_urls_list())
        if url_err:
            return _json_error(url_err)
        site.base_url = normalize_http_url(new_base) or new_base
    if "country" in data:
        site.country = data["country"]
    if "isActive" in data:
        site.enabled = bool(data["isActive"])
    if "scraper" in data:
        site.scraper = data["scraper"]
    if "currency" in data:
        site.currency = data["currency"]
    if "catalogUrls" in data:
        urls = [
            normalize_http_url(u.strip()) or u.strip()
            for u in data["catalogUrls"]
            if u and str(u).strip()
        ]
        url_err = _validate_site_urls(site.base_url, urls)
        if url_err:
            return _json_error(url_err)
        if urls:
            site.catalog_urls = "\n".join(urls)
    if "productLinkPattern" in data:
        site.product_link_pattern = data["productLinkPattern"]
    if "delaySeconds" in data:
        site.delay_seconds = float(data["delaySeconds"])
    if "notes" in data:
        site.notes = data.get("notes", "")

    site.save()
    sync_site_to_yaml(site)
    clear_provider_cache()
    return JsonResponse({"provider": _site_to_provider(site)})


@require_http_methods(["DELETE"])
def api_site_delete(request: HttpRequest, slug: str) -> JsonResponse:
    site = Site.objects.filter(slug=slug).first()
    if not site:
        return _json_error("Proveedor no encontrado", 404)
    site.delete()
    return JsonResponse({"ok": True})


@require_GET
def api_products(request: HttpRequest) -> JsonResponse:
    qs = Product.objects.all()
    search = request.GET.get("q", "").strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(source__icontains=search))
    country = request.GET.get("country", "")
    if country in ("AR", "CL"):
        qs = qs.filter(country=country)
    source = request.GET.get("provider", "")
    if source and source != "all":
        slug = canonical_source(source)
        qs = qs.filter(Q(source=slug) | Q(source=source))
    availability = request.GET.get("availability", "")
    if availability and availability != "all":
        qs = qs.filter(availability__icontains=availability.replace("-", "_"))

    limit = min(int(request.GET.get("limit", 200)), 500)
    products = [_product_to_json(p) for p in qs[:limit]]
    slugs = {canonical_source(s) for s in qs.values_list("source", flat=True) if s}
    providers = sorted({display_name_for_slug(s) for s in slugs if s})
    return JsonResponse({"products": products, "providers": providers})


@require_http_methods(["POST"])
def api_scrape(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    site_slug = data.get("siteSlug", "all")
    country = data.get("country", "all")
    if site_slug and site_slug != "all":
        site = Site.objects.filter(slug=site_slug).first()
        if site:
            country = site.country

    default_pages, default_products = scrape_limits_from_settings()
    try:
        max_pages = int(data["maxPages"]) if "maxPages" in data else default_pages
        max_products = int(data["maxProducts"]) if "maxProducts" in data else default_products
    except (TypeError, ValueError):
        return _json_error("maxPages y maxProducts deben ser numéricos")
    if max_pages < 1 or max_products < 1:
        return _json_error("maxPages y maxProducts deben ser mayores a 0")

    job = start_scrape_job(
        country=country,
        site_slug=site_slug or "all",
        max_pages=max_pages,
        max_products=max_products,
        do_export=bool(data.get("doExport", False)),
        export_format=data.get("exportFormat", "xlsx"),
    )
    if job is None:
        return _json_error("Ya hay un trabajo en curso", 409)
    return JsonResponse({"jobId": job.pk, "status": job.status})


@require_http_methods(["POST"])
def api_scrape_stop(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}
    job_id = data.get("jobId")
    if job_id is not None:
        try:
            job_id = int(job_id)
        except (TypeError, ValueError):
            return _json_error("jobId inválido")
    job = stop_job(job_id=job_id)
    if job is None:
        return _json_error("No hay un scraping en curso para detener", 404)
    return JsonResponse({"jobId": job.pk, "status": "stopping"})


@require_GET
def api_export_readiness(request: HttpRequest) -> JsonResponse:
    return JsonResponse(assess_export_readiness())


@require_http_methods(["POST"])
def api_export(request: HttpRequest) -> JsonResponse:
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        data = {}

    fmt = data.get("format", "xlsx")
    if fmt == "excel":
        fmt = "xlsx"
    if fmt not in ("xlsx", "csv"):
        fmt = "xlsx"

    state = assess_export_readiness()
    if not state["canExport"]:
        return _json_error(state["message"], 400)

    try:
        job = start_export_job(export_format=fmt)
    except ValueError as exc:
        return _json_error(str(exc), 400)
    if job is None:
        return _json_error("Ya hay un trabajo en curso", 409)
    return JsonResponse({"jobId": job.pk, "status": job.status})


@require_GET
def api_job_status(request: HttpRequest) -> JsonResponse:
    from portal.job_status_helpers import serialize_job_status

    job_id = request.GET.get("jobId")
    if job_id:
        job = ScrapeJob.objects.filter(pk=job_id).first()
    else:
        job = ScrapeJob.objects.first()

    payload = serialize_job_status(job)
    if not job:
        return JsonResponse(payload)

    result = payload.get("result") or {}
    export_files: list[dict[str, str]] = []
    if job.status == ScrapeJob.Status.DONE and job.job_type == "export" and result.get("export_paths"):
        for key, full_path in result["export_paths"].items():
            fname = Path(str(full_path)).name
            if _safe_export_path(fname):
                export_files.append(
                    {
                        "key": key,
                        "name": fname,
                        "downloadUrl": f"/api/v1/exports/download/?name={fname}",
                    }
                )

    scrape_run_id = result.get("scrapeRunId") if isinstance(result, dict) else None
    if scrape_run_id:
        payload["productsForJob"] = Product.objects.filter(scrape_id=scrape_run_id).count()

    payload["productsInDb"] = Product.objects.count()
    payload["exportFiles"] = export_files
    return JsonResponse(payload)


@require_GET
def api_export_download(request: HttpRequest) -> FileResponse | JsonResponse:
    path = _safe_export_path(request.GET.get("name", ""))
    if not path:
        raise Http404("Archivo no encontrado")

    content_types = {
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv; charset=utf-8",
        ".parquet": "application/octet-stream",
    }
    suffix = path.suffix.lower()
    return FileResponse(
        path.open("rb"),
        as_attachment=True,
        filename=path.name,
        content_type=content_types.get(suffix, "application/octet-stream"),
    )


@require_GET
def api_exports_list(request: HttpRequest) -> JsonResponse:
    exports_dir = _exports_dir()
    files = []
    if exports_dir.exists():
        for path in sorted(exports_dir.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
            if path.is_file() and not path.name.startswith("."):
                files.append(
                    {
                        "name": path.name,
                        "size": path.stat().st_size,
                        "modified": path.stat().st_mtime,
                        "downloadUrl": f"/api/v1/exports/download/?name={path.name}",
                    }
                )
    return JsonResponse({"exports": files})
