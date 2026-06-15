# Fuentes de datos — Uniformes clínicos (Argentina y Chile)

## Exclusiones

| Dominio | Motivo |
|---------|--------|
| `mercadolibre.com.ar` | Marketplace agregador — excluido |
| `mercadolibre.cl` | Idem (Chile) |
| `mercadolibre.com` | Idem |
| `mercadolibre.com.mx` | Idem |

## Argentina (AR)

| Slug | Nombre | URL base | Tipo sitio | Scraper | Riesgo |
|------|--------|----------|------------|---------|--------|
| `soul_uniform` | Soul Uniformes Médicos | https://www.souluniform.com.ar | TiendaNube | `tiendanube` | Bajo |
| `coco_wear` | COCO Uniformes Médicos | https://www.cocowearshop.com | TiendaNube | `tiendanube` | Bajo |
| `dara_scrubs` | Dara Scrubs | https://www.darascrubs.ar | TiendaNube | `tiendanube` | Bajo |
| `saber_uniformes` | Saber Uniformes | https://www.saberuniformes.com.ar | HTML custom | `configurable` | Medio |
| `terzo` | Terzo Indumentaria | https://terzo.com.ar | WooCommerce | `woocommerce` | Medio |
| `carolina_uniforms` | Carolina Uniforms | https://www.carolinauniforms.com.ar | Por validar | `configurable` | Alto — **deshabilitado** |

## Chile (CL)

| Slug | Nombre | URL base | Tipo sitio | Scraper | Riesgo |
|------|--------|----------|------------|---------|--------|
| `suitmed_cl` | Suitmed | https://www.suitmed.cl | Shopify | `shopify` | Bajo |
| `scorpi_cl` | Scorpi | https://www.scorpi.cl | Shopify | `shopify` | Bajo |
| `allscrubs_cl` | All Scrubs | https://allscrubs.cl | Shopify | `shopify` | Bajo |
| `scrubplus_cl` | Scrubplus | https://scrubplus.cl | WooCommerce | `woocommerce` | Medio |
| `moneruss_cl` | Moneruss | https://moneruss.cl | WooCommerce | `woocommerce` | Alto — **deshabilitado** |

## Criterios de selección

1. **Relevancia**: venta directa de uniformes médicos o sanitarios.
2. **Accesibilidad**: catálogo público sin login.
3. **Nacional**: operación y envíos en Argentina o Chile.
4. **Sin MercadoLibre**: no se scrapean marketplaces.

## Notas por plataforma

### TiendaNube (Argentina)

- JSON-LD `schema.org/Product` en fichas.
- Listados bajo `/productos/`.

### Shopify (Chile)

- JSON-LD en Suitmed y All Scrubs; Scorpi puede requerir fallback HTML para precio.
- URLs canónicas: `/products/{slug}`.
- Moneda: **CLP** (formato `$27.891` = 27891 pesos).

### WooCommerce

- Argentina: Terzo (`/producto/`).
- Chile: Scrubplus (`/producto/`).

## bots.txt

Revisar antes de corridas masivas. Delay recomendado: 2–3 s entre requests.

## Agregar un proveedor

1. Fila en esta tabla con `country: AR` o `CL`.
2. Entrada en `config/sites/ar.yaml` o `config/sites/cl.yaml`.
3. Elegir scraper: `tiendanube`, `shopify`, `woocommerce` o `configurable`.
4. Fixture en `tests/fixtures/` y test de integración.
