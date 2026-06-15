# Guía de uso

## 1. Instalación

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

## 2. Configuración

### `config/settings.yaml`

| Clave | Descripción |
|-------|-------------|
| `database.path` | Ruta del archivo SQLite |
| `http.delay_seconds` | Pausa entre requests (recomendado ≥ 2) |
| `http.user_agent` | Identificación del bot |
| `excluded_domains` | Dominios bloqueados (MercadoLibre) |

### `config/sites/ar.yaml` y `config/sites/cl.yaml`

Por cada proveedor (en el archivo del país correspondiente):

- `enabled`: `true` / `false`
- `scraper`: `tiendanube` | `shopify` | `woocommerce` | `configurable`
- `catalog_urls`: páginas de listado
- `selectors`: solo para `configurable`

## 3. Panel web Django

Primera vez:

```bash
python manage.py migrate
python manage.py import_sites
python manage.py runserver
```

En **http://127.0.0.1:8000/** (puerto por defecto de Django):

1. **Editar URLs** en formularios Django (se guardan en la base y se sincronizan a `config/sites/*.yaml`).
2. **Ejecutar todo** o scrapear una tienda con un botón.
3. Ver **actividad** y productos en tablas.
4. **Admin** en `/admin/` para gestión avanzada (opcional: `python manage.py createsuperuser`).

El panel web es únicamente Django (`python manage.py runserver`).

## 4. Ejecución por terminal

### Scrape por país

```bash
# Solo Chile
python scripts/run_scrape.py run --site all --country CL --max-products 20

# Solo Argentina
python scripts/run_scrape.py run --site all --country AR --max-products 20

# Todos
python scripts/run_scrape.py run --site all --max-pages 3 --max-products 50
```

### Scrape de prueba (smoke)

```bash
python scripts/run_scrape.py run --site soul_uniform --max-products 5
```

### Con export al terminar

```bash
python scripts/run_scrape.py run --site all --export --format xlsx
```

## 4. Exportación y análisis

```bash
python scripts/export_analysis.py
python scripts/export_analysis.py --format xlsx
python scripts/export_analysis.py --format parquet
```

Archivos generados:

Los archivos incluyen fecha y hora en el nombre: **dia-mes-año-hora-minuto-segundo** (ej. `22-05-2026-14-30-45`).

- `data/exports/products_22-05-2026-14-30-45.csv` — catálogo deduplicado
- `data/exports/summary_by_source_22-05-2026-14-30-45.csv` — conteos y precios por proveedor
- `data/exports/summary_by_category_22-05-2026-14-30-45.csv` — agregación por categoría

Mismo patrón con extensión `.xlsx` si usás `--format xlsx`.

Abrir en Excel o pandas:

```python
import pandas as pd
df = pd.read_csv("data/exports/products_20260522.csv")
```

## 5. Programación automática (Windows)

1. Abrir **Programador de tareas**.
2. Crear tarea semanal.
3. Acción: iniciar programa  
   `C:\...\asaaa\.venv\Scripts\python.exe`  
   Argumentos: `scripts\run_scrape.py run --site all --export`

## 6. Solución de problemas

| Síntoma | Acción |
|---------|--------|
| 0 productos | Revisar `catalog_urls` y selectores en `sites.yaml` |
| 403 / timeout | Aumentar `delay_seconds`; reducir `max_products` |
| Precio vacío | Revisar fixture; sitio puede usar “consultar precio” |
| Error MercadoLibre | Esperado — dominio excluido |

## 7. Buenas prácticas

- Corridas en horario de baja carga.
- No paralelizar requests al mismo dominio.
- Revisar `robots.txt` antes de aumentar volumen.
- Mantener fixtures actualizados cuando cambie el HTML.
