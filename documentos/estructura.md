# Estructura del proyecto

```
asaaa/
├── manage.py                 # CLI Django (migrate, runserver, import_sites)
├── README.md                 # Resumen e inicio rápido
├── documentos/               # Toda la documentación (guías, arquitectura, uso)
├── requirements.txt
│
├── uniform_project/          # Proyecto Django
│   ├── settings.py           # Base de datos, apps, idioma
│   ├── urls.py               # API, assets SPA, catch-all React
│   ├── wsgi.py / asgi.py     # Despliegue en servidor (producción)
│
├── frontend/                 # Panel React + Material UI (pnpm)
│   ├── src/                  # Páginas: Dashboard, Productos, Proveedores…
│   └── dist/                 # Build servido por Django (tras pnpm run build)
│
├── portal/                   # Backend Django
│   ├── models.py             # Site, ScrapeJob, Product
│   ├── api_views.py          # REST /api/v1/
│   ├── spa_views.py          # Sirve el build de React
│   ├── admin.py              # Panel /admin/
│   ├── services.py           # Scraping, export, sync YAML
│   └── management/commands/
│       ├── import_sites.py   # YAML → base Django
│       └── scrape.py         # Scraping por terminal
│
├── config/
│   ├── settings.yaml         # HTTP, delays, exclusiones MercadoLibre
│   ├── sites/ar.yaml         # Tiendas Argentina (usado por el scraper)
│   └── sites/cl.yaml         # Tiendas Chile
│
├── src/                      # Motor de scraping (sin Django)
│   ├── pipeline.py
│   ├── models.py             # ProductRecord (Pydantic)
│   ├── db.py                 # SQLite products
│   ├── config_loader.py      # Lee YAML
│   ├── config_store.py       # Escribe YAML desde Django
│   ├── scrapers/             # tiendanube, shopify, woocommerce, configurable
│   ├── etl/normalize.py       # Export CSV/XLSX
│   └── cli/                  # scrape + export por terminal
│
├── scripts/
│   ├── dashboard.py          # Atajo: runserver puerto 8080
│   ├── run_scrape.py
│   └── export_analysis.py
│
├── data/
│   ├── uniforms.db           # Datos (generado)
│   ├── exports/              # Excel/CSV (generado)
│   └── raw/                  # HTML de respaldo opcional
│
└── tests/                    # pytest + fixtures HTML
```

## Archivos “vacíos” que se conservan

| Archivo | Motivo |
|---------|--------|
| `data/exports/.gitkeep` | Git no guarda carpetas vacías; marca que `exports/` debe existir |
| `data/raw/.gitkeep` | Igual para `raw/` (HTML de debug opcional) |
| `portal/migrations/__init__.py` | Paquete Python de migraciones Django |
| `portal/management/__init__.py` | Paquete de comandos `manage.py` |
| `src/**/__init__.py` | Marcan carpetas como módulos importables |

## Eliminado en la limpieza

- `docs/` — movido a `documentos/`
- Panel Django HTML legacy en `portal/templates/`, `portal/static/`, `portal/views.py` — disponible en `/legacy/` (el panel principal sigue siendo React)
- `src/web/` — resto de un panel FastAPI antiguo

## Dónde cambiar qué

| Tarea |-------| Dónde |
|-------|--------|-------|-------|--------|-------|
| Cambiar URL de una tienda||-------|--------| Panel → Proveedores o `config/sites/*.yaml` |
| Agregar tienda nueva |---------|---------| Panel → Proveedores |
| Ajustar delay / User-Agent |--------|--------| `config/settings.yaml` |
| Nuevo tipo de sitio web |---------|---------| `src/scrapers/` + `registry.py` |

