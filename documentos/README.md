# Documentación — Uniform Scraper

Toda la guía del proyecto está en esta carpeta.

- [proyecto-general.md](proyecto-general.md): mapa general de capas, flujo y convenciones.
- [react-django-integracion.md](react-django-integracion.md): cómo se mezclan React (SPA) y Django (API/servidor).
- [inicio-rapido.md](inicio-rapido.md): instalar, migrar, build del panel y arrancar Django.
- [estructura.md](estructura.md): árbol del proyecto y rol de cada carpeta.
- [uso.md](uso.md): comandos, scraping y exportación.
- [arquitectura.md](arquitectura.md): flujo técnico y tipos de scraper.
- [fuentes.md](fuentes.md): proveedores AR/CL y exclusiones.
- [configuracion.md](configuracion.md): `config/settings.yaml` y `sites/*.yaml`.
- [scripts.md](scripts.md): atajos en `scripts/`.
- [datos.md](datos.md): base SQLite y carpeta `data/exports/`.
- [frontend-panel.md](frontend-panel.md): panel React (pnpm, dev y producción).
- [seguridad.md](seguridad.md): URLs, exportación Excel y buenas prácticas.

## Inicio mínimo

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py import_sites
cd frontend && pnpm install && pnpm run build
python manage.py runserver
```

