from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect


def _dist_dir() -> Path:
    return Path(settings.BASE_DIR) / "frontend" / "dist"


def spa_index(request: HttpRequest) -> HttpResponse:
    """Sirve la SPA React si existe el build; si no, panel Django clásico."""
    index = _dist_dir() / "index.html"
    if index.exists():
        return FileResponse(index.open("rb"), content_type="text/html; charset=utf-8")
    return redirect("dashboard")


def spa_asset(request: HttpRequest, path: str) -> HttpResponse:
    asset = _dist_dir() / "assets" / path
    if not asset.exists() or not asset.is_file():
        raise Http404
    content_types = {
        ".js": "application/javascript",
        ".css": "text/css",
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".woff2": "font/woff2",
    }
    ctype = content_types.get(asset.suffix, "application/octet-stream")
    return FileResponse(asset.open("rb"), content_type=ctype)
