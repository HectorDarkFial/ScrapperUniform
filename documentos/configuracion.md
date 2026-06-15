# Configuración

| Archivo | Propósito |
|---------|-----------|
| [`config/settings.yaml`](../config/settings.yaml) | Base de datos, HTTP, delays, dominios bloqueados (MercadoLibre) |
| [`config/sites/ar.yaml`](../config/sites/ar.yaml) | Proveedores de **Argentina** |
| [`config/sites/cl.yaml`](../config/sites/cl.yaml) | Proveedores de **Chile** |

## Agregar un proveedor

1. Elegir el archivo según país (`ar.yaml` o `cl.yaml`).
2. Copiar un bloque existente con el mismo `scraper` (tiendanube, shopify, woocommerce, configurable).
3. Ajustar `catalog_urls`, `product_link_pattern` y selectores si aplica.
4. Documentar en [fuentes.md](fuentes.md).

## Campos principales por sitio

- `enabled`: `true` para incluirlo en corridas `--site all`
- `country`: `AR` o `CL`
- `scraper`: motor a usar (ver [arquitectura.md](arquitectura.md))
- `catalog_urls`: páginas de listado de productos
- `delay_seconds`: pausa entre requests a ese dominio
