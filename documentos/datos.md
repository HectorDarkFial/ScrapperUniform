# Carpeta `data/`

| Elemento | Descripción |
|----------|-------------|
| `uniforms.db` | Base SQLite (productos + tablas Django). **No se sube a git** (`*.db` en `.gitignore`). |
| `exports/` | Archivos generados al exportar (`informe_uniformes_*.xlsx`, CSV en español, etc.). |
| `raw/` | HTML guardado manualmente para depurar selectores (opcional). |

## Archivos `.gitkeep`

Las carpetas `exports/` y `raw/` incluyen un archivo `.gitkeep` **vacío a propósito**: Git no versiona carpetas sin archivos; el `.gitkeep` asegura que la estructura exista al clonar el repo.

Los exports viejos de prueba se pueden borrar; se regeneran desde el panel o con `python -m src export`.
