from django.contrib import admin

from portal.models import Product, ScrapeJob, Site


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "country", "scraper", "enabled", "base_url")
    list_filter = ("country", "scraper", "enabled")
    search_fields = ("slug", "name", "base_url")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ScrapeJob)
class ScrapeJobAdmin(admin.ModelAdmin):
    list_display = ("id", "job_type", "status", "country", "site_slug", "created_at")
    list_filter = ("status", "job_type")
    readonly_fields = ("log", "result_json", "error_message", "started_at", "finished_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "source", "price", "currency", "availability", "scraped_at")
    list_filter = ("source", "country", "availability")
    search_fields = ("name", "sku", "product_url")
    readonly_fields = tuple(f.name for f in Product._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
