from __future__ import annotations

from django.db import models


class Site(models.Model):
    """Configuración de un proveedor (sincroniza con config/sites/*.yaml)."""

    class Country(models.TextChoices):
        AR = "AR", "Argentina"
        CL = "CL", "Chile"

    class Scraper(models.TextChoices):
        TIENDANUBE = "tiendanube", "TiendaNube"
        SHOPIFY = "shopify", "Shopify"
        WOOCOMMERCE = "woocommerce", "WooCommerce"
        CONFIGURABLE = "configurable", "Configurable (CSS)"

    slug = models.SlugField(max_length=80, unique=True)
    enabled = models.BooleanField(default=True)
    country = models.CharField(max_length=2, choices=Country.choices, default=Country.AR)
    name = models.CharField(max_length=200)
    base_url = models.URLField(max_length=500)
    currency = models.CharField(max_length=8, default="ARS")
    scraper = models.CharField(max_length=20, choices=Scraper.choices, default=Scraper.TIENDANUBE)
    catalog_urls = models.TextField(
        help_text="Una URL de catálogo por línea",
    )
    product_link_pattern = models.CharField(max_length=100, default="/productos/")
    delay_seconds = models.FloatField(default=2.0)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["country", "name"]
        verbose_name = "Tienda"
        verbose_name_plural = "Tiendas"

    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"

    def catalog_urls_list(self) -> list[str]:
        return [u.strip() for u in self.catalog_urls.splitlines() if u.strip()]

    def to_scraper_config(self) -> dict:
        cfg = {
            "enabled": self.enabled,
            "country": self.country,
            "name": self.name,
            "base_url": self.base_url.rstrip("/"),
            "currency": self.currency,
            "scraper": self.scraper,
            "catalog_urls": self.catalog_urls_list(),
            "product_link_pattern": self.product_link_pattern,
            "delay_seconds": self.delay_seconds,
        }
        if self.notes:
            cfg["notes"] = self.notes
        return cfg


class ScrapeJob(models.Model):
    """Registro de ejecuciones desde el dashboard."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        RUNNING = "running", "En curso"
        DONE = "done", "Completado"
        CANCELLED = "cancelled", "Detenido"
        ERROR = "error", "Error"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    job_type = models.CharField(max_length=20, default="scrape")
    country = models.CharField(max_length=10, default="all")
    site_slug = models.CharField(max_length=80, default="all")
    max_products = models.PositiveIntegerField(default=20)
    max_pages = models.PositiveIntegerField(default=2)
    do_export = models.BooleanField(default=False)
    progress = models.PositiveSmallIntegerField(default=0)
    export_format = models.CharField(max_length=10, default="xlsx")
    log = models.TextField(blank=True)
    result_json = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    stop_requested = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Job #{self.pk} {self.job_type} ({self.status})"


class Product(models.Model):
    """Productos scrapeados (tabla existente, solo lectura en Django)."""

    scrape_id = models.CharField(max_length=36)
    scraped_at = models.DateTimeField()
    source = models.CharField(max_length=80, db_index=True)
    country = models.CharField(max_length=2, null=True, blank=True)
    product_url = models.URLField(max_length=500)
    sku = models.CharField(max_length=100, null=True, blank=True)
    name = models.CharField(max_length=500)
    category = models.CharField(max_length=200, null=True, blank=True)
    price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    price_display = models.CharField(max_length=120, null=True, blank=True)
    currency = models.CharField(max_length=8)
    price_list = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    price_list_display = models.CharField(max_length=120, null=True, blank=True)
    discount_percent = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    discount_display = models.CharField(max_length=80, null=True, blank=True)
    price_without_tax = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    price_without_tax_display = models.CharField(max_length=120, null=True, blank=True)
    price_transfer = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    price_transfer_display = models.CharField(max_length=120, null=True, blank=True)
    availability = models.CharField(max_length=20)
    stock_text = models.CharField(max_length=500, null=True, blank=True)
    sizes = models.TextField(blank=True)
    colors = models.TextField(blank=True)
    image_url = models.URLField(max_length=500, null=True, blank=True)
    raw_attributes = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = "products"
        ordering = ["-scraped_at"]
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self) -> str:
        return self.name[:60]
