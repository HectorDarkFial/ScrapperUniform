# Uniform Scraper

Scraping de precios y disponibilidad de uniformes médicos en **Chile** (sin MercadoLibre).



Panel:Primera vez: [documentos/inicio-rapido.md](documentos/inicio-rapido.md)

## Estructura (resumen)

| Carpeta | Uso |
|---------|-----|
| `frontend/` | Panel React + Material UI |
| `portal/` | API REST y modelos Django |
| `src/` | Motor de scraping y exportación |
| `config/` | Ajustes y listas de tiendas (`sites/ar.yaml`, `cl.yaml`) |
| `data/` | SQLite y exports generados |
| `documentos/` | **Toda la documentación** |
| `scripts/` | Atajos de terminal |
| `tests/` | Pruebas (`pytest -q`) |

## Exportación consistente (última corrida)

La exportación del panel usa la **última corrida de scraping completada** (por `scrapeRunId`) para evitar mezclar productos históricos con la selección actual de proveedores.

## Documentación

Índice completo: [documentos/README.md](documentos/README.md)
Mapa general del proyecto: [documentos/proyecto-general.md](documentos/proyecto-general.md)
