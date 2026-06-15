from django.urls import path
from django.views.generic import RedirectView

from portal import views

urlpatterns = [
    path("legacy/", views.dashboard, name="dashboard"),
    path("legacy/tiendas/nueva/", views.site_create, name="site_create"),
    path("legacy/tiendas/<slug:slug>/", views.site_edit, name="site_edit"),
    path("legacy/tiendas/guardar/", views.site_save, name="site_save"),
    path("legacy/ejecutar/", views.run_scrape, name="run_scrape"),
    path("legacy/exportar/", views.run_export, name="run_export"),
    path("legacy/api/estado/", views.job_status, name="job_status"),
    path("legacy/tiendas/", RedirectView.as_view(url="/legacy/", permanent=False)),
    path("tiendas/", RedirectView.as_view(url="/providers", permanent=False)),
    path("tiendas/nueva/", RedirectView.as_view(url="/providers", permanent=False)),
]
