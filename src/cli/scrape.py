"""scraping."""

from __future__ import annotations

import typer

from src.config_loader import get_sites
from src.etl.normalize import export_analysis
from src.pipeline import Pipeline
from src.utils.logging import setup_logging

app = typer.Typer(help="Extraer precios y disponibilidad de tiendas configuradas")
logger = setup_logging()


@app.command("run")
def run(
    site: str = typer.Option("all", "--site", "-s", help="Slug del sitio o 'all'"),
    country: str = typer.Option("all", "--country", "-c", help="AR, CL o all"),
    max_pages: int = typer.Option(3, "--max-pages", help="Páginas de catálogo por URL"),
    max_products: int = typer.Option(50, "--max-products", help="Máximo de productos por sitio"),
    do_export: bool = typer.Option(False, "--export", help="Exportar al finalizar"),
    format: str = typer.Option("csv", "--format", help="csv, xlsx o parquet"),
) -> None:
    """Ejecuta el scraping y guarda en SQLite."""
    pipeline = Pipeline()
    try:
        if site != "all" and site not in get_sites():
            typer.echo(f"Sitio desconocido: {site}")
            typer.echo(f"Disponibles: {', '.join(sorted(get_sites()))}")
            raise typer.Exit(1)

        summary = pipeline.run_all(
            site,
            max_pages=max_pages,
            max_products=max_products,
            country=country,
        )
        typer.echo(typer.style("Resumen:", bold=True))
        for slug, data in summary["sites"].items():
            typer.echo(f"  {slug}: {data}")
        typer.echo(f"Total guardados: {summary['total_saved']}")

        if do_export:
            rows = pipeline.db.fetch_all()
            paths = export_analysis(rows, fmt=format)
            typer.echo("Exportados:")
            for key, path in paths.items():
                typer.echo(f"  {key}: {path}")
    finally:
        pipeline.close()


def _print_sites(country: str) -> None:
    for slug, cfg in get_sites().items():
        if country.upper() != "ALL" and cfg.get("country") != country.upper():
            continue
        status = "activo" if cfg.get("enabled", True) else "deshabilitado"
        pais = cfg.get("country", "?")
        scraper = cfg.get("scraper", "?")
        typer.echo(f"{slug:20} {pais}  {scraper:14}  {status:12}  {cfg.get('name')}")


@app.command("list")
def list_sites(
    country: str = typer.Option("all", "--country", "-c", help="AR, CL o all"),
) -> None:
    """Lista proveedores configurados."""
    _print_sites(country)


@app.command("list-sites")
def list_sites_legacy(
    country: str = typer.Option("all", "--country", "-c", help="AR, CL o all"),
) -> None:
    """Alias de list (compatibilidad)."""
    _print_sites(country)
