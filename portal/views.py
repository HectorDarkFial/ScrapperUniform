from __future__ import annotations

from django.contrib import messages
from django.db.models import Count
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from portal.export_gate import assess_export_readiness
from portal.forms import RunScrapeForm, SiteForm
from portal.models import Product, ScrapeJob, Site
from portal.services import import_sites_from_yaml, scrape_limits_from_settings, start_export_job, start_scrape_job, sync_site_to_yaml


def dashboard(request: HttpRequest) -> HttpResponse:
    if Site.objects.count() == 0:
        import_sites_from_yaml()

    sites = Site.objects.all()
    products = Product.objects.all()[:30]
    stats = {
        "total_products": Product.objects.count(),
        "active_sites": sites.filter(enabled=True).count(),
        "total_sites": sites.count(),
    }
    by_country = (
        Product.objects.exclude(country__isnull=True)
        .values("country")
        .annotate(c=Count("id"))
    )
    latest_job = ScrapeJob.objects.first()
    default_pages, default_products = scrape_limits_from_settings()
    run_form = RunScrapeForm(
        initial={
            "max_pages": default_pages,
            "max_products": default_products,
            "do_export": False,
        }
    )
    export_state = assess_export_readiness()

    return render(
        request,
        "portal/dashboard.html",
        {
            "sites": sites,
            "products": products,
            "stats": stats,
            "by_country": list(by_country),
            "latest_job": latest_job,
            "run_form": run_form,
            "site_form": SiteForm(),
            "export_state": export_state,
        },
    )


def site_edit(request: HttpRequest, slug: str) -> HttpResponse:
    site = get_object_or_404(Site, slug=slug)
    if request.method == "POST":
        form = SiteForm(request.POST, instance=site)
        if form.is_valid():
            obj = form.save()
            sync_site_to_yaml(obj)
            messages.success(request, f"Tienda «{obj.name}» guardada y sincronizada.")
            return redirect("dashboard")
    else:
        form = SiteForm(instance=site)
    return render(request, "portal/site_form.html", {"form": form, "site": site})


def site_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = SiteForm(request.POST)
        if form.is_valid():
            obj = form.save()
            sync_site_to_yaml(obj)
            messages.success(request, f"Tienda «{obj.name}» creada.")
            return redirect("dashboard")
    else:
        form = SiteForm()
    return render(request, "portal/site_form.html", {"form": form, "site": None})


@require_POST
def site_save(request: HttpRequest) -> HttpResponse:
    slug = request.POST.get("slug", "").strip()
    instance = Site.objects.filter(slug=slug).first() if slug else None
    form = SiteForm(request.POST, instance=instance)
    if form.is_valid():
        obj = form.save()
        sync_site_to_yaml(obj)
        messages.success(request, "Configuración guardada.")
    else:
        messages.error(request, f"Revisá el formulario: {form.errors}")
    return redirect("dashboard")


@require_POST
def run_scrape(request: HttpRequest) -> HttpResponse:
    form = RunScrapeForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Datos de ejecución inválidos.")
        return redirect("dashboard")

    site_slug = request.POST.get("site_slug", "all")
    job = start_scrape_job(
        country=form.cleaned_data["country"],
        site_slug=site_slug or "all",
        max_pages=form.cleaned_data["max_pages"],
        max_products=form.cleaned_data["max_products"],
        do_export=form.cleaned_data.get("do_export", False),
        export_format=form.cleaned_data["export_format"],
    )
    if job is None:
        messages.warning(request, "Ya hay un scraping en curso.")
    else:
        messages.info(request, "Scraping iniciado. El log se actualiza solo abajo.")
    return redirect("dashboard")


@require_POST
def run_export(request: HttpRequest) -> HttpResponse:
    fmt = request.POST.get("export_format", "xlsx")
    try:
        job = start_export_job(export_format=fmt)
    except ValueError as exc:
        messages.error(request, str(exc))
        return redirect("dashboard")
    if job is None:
        messages.warning(request, "Ya hay un trabajo en curso.")
    else:
        messages.info(request, "Exportación iniciada. Cuando termine, descargá desde Exportar (panel nuevo) o data/exports/.")
    return redirect("dashboard")


@require_GET
def job_status(request: HttpRequest) -> HttpResponse:
    from portal.job_status_helpers import serialize_job_status

    job = ScrapeJob.objects.first()
    return JsonResponse(serialize_job_status(job))
