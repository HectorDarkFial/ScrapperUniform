# Proyecto general

Este documento resume la estructura funcional del sistema y define una organización estable para crecer sin mezclar responsabilidades.

## Capas del sistema

- `frontend/`: interfaz React (vistas, filtros, acciones de scraping y exportación).
- `portal/`: API y orquestación de jobs en Django (estado, seguridad, endpoints).
- `src/`: motor de scraping/ETL independiente de Django (parsers, pipeline, exportadores).
- `config/`: configuración versionada (settings + proveedores por país).
- `data/`: datos generados en runtime (SQLite, exports, artefactos temporales).
- `tests/`: cobertura automatizada de reglas de negocio y seguridad.

## Flujo operativo recomendado

1. En `Proveedores`, activar/desactivar sitios y lanzar scraping.
2. El scraping guarda productos con `scrape_id` de corrida.
3. La exportación toma solo la última corrida exitosa (no histórico completo).
4. Se generan archivos en `data/exports/` y se descargan desde el panel.

## Organización de código (convención)

- **UI y estado**: `frontend/src/app/components`, `frontend/src/app/context`, `frontend/src/app/api`.
- **Endpoints HTTP**: `portal/api_views.py` y rutas en `portal/api_urls.py`.
- **Reglas de exportación y seguridad**: `portal/export_gate.py` + `src/utils/export_security.py`.
- **Ejecución de jobs**: `portal/services.py`.
- **Scrapers por plataforma**: `src/scrapers/`.
- **Transformaciones y salida**: `src/etl/normalize.py`.

## Criterios para mantener la estructura ordenada

- No poner parsing HTML en `portal/`; eso vive en `src/scrapers/`.
- No agregar lógica de negocio en componentes UI; usar API/context/hooks.
- Toda regla que afecte exportación debe tener prueba en `tests/`.
- Si un módulo mezcla responsabilidades, extraer helper dedicado antes de crecerlo.

## Próximas mejoras sugeridas

- Separar `portal/services.py` en módulos por dominio (`scrape_jobs.py`, `export_jobs.py`).
- Añadir tests de integración API para validar filtros de exportación por corrida.
- Documentar contratos JSON de endpoints clave en un archivo `documentos/api.md`.
