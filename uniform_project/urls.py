from django.contrib import admin
from django.urls import include, path, re_path

from portal import spa_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("portal.api_urls")),
    path("assets/<path:path>", spa_views.spa_asset, name="spa_asset"),
    path("", include("portal.urls")),
    re_path(r"^(?!api|admin|assets|legacy|static).*$", spa_views.spa_index, name="spa"),
]
