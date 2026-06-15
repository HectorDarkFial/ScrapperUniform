# Seguridad — scraping y exportación

Este proyecto recopila URLs públicas de **proveedores configurados** para análisis de mercado. No sustituye antivirus ni revisión humana al abrir enlaces.

## Medidas implementadas

### 1. URLs al scrapear

- Solo esquemas **http/https** (bloqueo de `javascript:`, `data:`, `file:`, etc.).
- Bloqueo de hosts **locales/privados** (SSRF: `127.0.0.1`, `localhost`, redes internas).
- Solo se descargan páginas de **dominios del proveedor** definidos en `config/sites/*.yaml`.
- MercadoLibre y dominios en `excluded_domains` siguen bloqueados.

### 2. Al guardar productos

- Cada ficha valida `product_url` e `image_url`.
- Productos con URL **bloqueada** no se guardan.
- Metadatos `url_trust` en la base: `trusted` | `unverified` | `blocked`.

### 3. Al exportar Excel/CSV

- Solo filas con URL **verificada** (dominio del proveedor) y datos útiles.
- URLs **no listadas** en proveedores no se exportan por defecto.
- Celdas sanitizadas contra **inyección de fórmulas** Excel (`=`, `+`, `@`, etc.).
- URLs exportadas como **texto plano** (sin hipervínculos automáticos en el generador).

### 4. Panel web

- API con **CSRF** en operaciones de escritura.
- En Productos: enlace “verificar” solo si `safeToOpen` (URL de proveedor confiable).
- Estado visible: **Verificada (proveedor)** / **No verificada** / **Bloqueada**.

## Configuración (`config/settings.yaml`)

```yaml
security:
  max_url_length: 2000
  block_private_ips: true
  require_https_for_export: false
  export_only_trusted_urls: false
  block_unverified_in_export: true
```

| Clave | Efecto |
|-------|--------|
| `block_unverified_in_export` | `true` = Excel solo con URLs de proveedores configurados |
| `export_only_trusted_urls` | `true` = aún más estricto (solo dominio exacto del proveedor) |
| `require_https_for_export` | `true` = rechaza `http://` en exportación |

## Buenas prácticas para el equipo

1. Abrí enlaces del Excel **copiando la URL** al navegador o desde el panel, no ejecutes macros del archivo.
2. Mantené actualizada la lista de proveedores en **Proveedores** (solo tiendas reales del rubro).
3. Tras agregar un sitio nuevo, ejecutá scraping y revisá que el estado URL sea **Verificada**.
4. No desactives `block_private_ips` salvo entornos de laboratorio aislados.

## Límites

- No escanea malware en servidores remotos.
- Un sitio comprometido legítimo podría servir contenido malicioso; por eso se limita a dominios conocidos y revisión manual.
