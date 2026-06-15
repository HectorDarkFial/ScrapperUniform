from django.urls import path

from portal import api_views

urlpatterns = [
    path("csrf/", api_views.api_csrf, name="api_csrf"),
    path("metrics/", api_views.api_metrics, name="api_metrics"),
    path("sites/", api_views.api_sites, name="api_sites"),
    path("sites/create/", api_views.api_site_create, name="api_site_create"),
    path("sites/<slug:slug>/", api_views.api_site_update, name="api_site_update"),
    path("sites/<slug:slug>/delete/", api_views.api_site_delete, name="api_site_delete"),
    path("products/", api_views.api_products, name="api_products"),
    path("scrape/", api_views.api_scrape, name="api_scrape"),
    path("scrape/stop/", api_views.api_scrape_stop, name="api_scrape_stop"),
    path("export/readiness/", api_views.api_export_readiness, name="api_export_readiness"),
    path("export/", api_views.api_export, name="api_export"),
    path("job/", api_views.api_job_status, name="api_job_status"),
    path("exports/", api_views.api_exports_list, name="api_exports_list"),
    path("exports/download/", api_views.api_export_download, name="api_export_download"),
]
