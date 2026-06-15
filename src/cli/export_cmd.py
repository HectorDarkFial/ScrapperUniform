"""exportación a CSV/XLSX."""

from __future__ import annotations

import typer

from src.config_loader import get_settings
from src.db import Database
from src.etl.normalize import export_analysis

app = typer.Typer(help="Exportar datos de SQLite a archivos de análisis")


@app.callback(invoke_without_command=True)
def export(
    format: str = typer.Option("csv", "--format", "-f", help="csv, xlsx o parquet"),
) -> None:
    """Genera archivos en data/exports/ con fecha DD-MM-YYYY-HH-MM-SS."""
    settings = get_settings()
    db = Database(settings["database"]["path"])
    rows = db.fetch_all()
    if not rows:
        typer.echo("No hay productos en la base de datos. Ejecutá el scraping primero.")
        raise typer.Exit(1)

    paths = export_analysis(rows, fmt=format)
    typer.echo("Archivos generados:")
    for name, path in paths.items():
        typer.echo(f"  {name}: {path}")
