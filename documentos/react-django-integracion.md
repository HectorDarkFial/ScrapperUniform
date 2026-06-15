# Integración React + Django

Este proyecto usa Django como backend/API y React como frontend SPA, servidos juntos desde el mismo dominio.

## Arquitectura general

- `frontend/`: app React (Vite + Material UI).
- `portal/`: app Django con endpoints API (`/api/v1/...`) y vistas legacy.
- `uniform_project/urls.py`: enruta API, admin, legacy y SPA.
- `portal/spa_views.py`: entrega `frontend/dist/index.html` para rutas del frontend.

## Flujo de ejecución

1. React llama endpoints Django en `/api/v1/`.
2. Django procesa scraping/export y guarda estado en modelos (`ScrapeJob`, `Product`, `Site`).
3. React consulta estado de jobs y muestra progreso en vivo.
4. Para exportación, Django genera archivos en `data/exports/` y React dispara la descarga.

## Ruteo

- **API**: `portal/api_urls.py` + `portal/api_views.py`.
- **SPA**: rutas como `/`, `/providers`, `/products`, `/export`, `/settings` se resuelven al `index.html` de React.
- **Legacy**: rutas bajo `/legacy/` siguen disponibles en plantillas Django.

## Build y despliegue local

```powershell
cd frontend
pnpm install
pnpm run build
cd ..
python manage.py runserver
```

Resultado:

- Django sirve API + archivos del build React.
- El navegador usa un único origen, así se evita configuración CORS compleja.

## Comunicación frontend-backend

- Cliente frontend: `frontend/src/app/api/client.ts`.
- Base URL API: `/api/v1`.
- CSRF: se solicita token con `/api/v1/csrf/` y luego se envía en métodos mutables (`POST/PUT/DELETE`).
- Descarga de export: `GET /api/v1/exports/download/?name=...`.

## Estado de scraping/exportación

- El backend guarda progreso en `ScrapeJob` (`status`, `progress`, `result_json`, `log`).
- React consulta estado con `/api/v1/job/` y actualiza UI periódicamente.
- Exportación usa la última corrida exitosa de scraping para evitar mezclar histórico.

## Convención recomendada

- UI/UX y estado visual en `frontend/`.
- Reglas de negocio, validación y seguridad en `portal/` y `src/`.
- No duplicar lógica: React solo consume API; decisiones críticas quedan en backend.
