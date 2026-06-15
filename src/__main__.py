

from __future__ import annotations

import sys

import typer

from src.cli.export_cmd import app as export_app
from src.cli.scrape import app as scrape_app

COMMANDS = {
    "scrape": scrape_app,
    "export": export_app,
}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        typer.echo("Uso (terminal):")
        typer.echo("  python -m src scrape run --country CL")
        typer.echo("  python -m src scrape list")
        typer.echo("  python -m src export --format xlsx")
        typer.echo("")
        typer.echo("Panel web (Django):")
        typer.echo("  python manage.py migrate")
        typer.echo("  python manage.py runserver")
        typer.echo("  → http://127.0.0.1:8000")
        raise typer.Exit(0 if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help") else 1)

    cmd = sys.argv[1]
    if cmd == "dashboard":
        typer.echo("El panel web ahora es Django. Usá:")
        typer.echo("  python manage.py runserver")
        raise typer.Exit(0)

    if cmd not in COMMANDS:
        typer.echo(f"Comando desconocido: {cmd}. Usá: scrape | export")
        raise typer.Exit(1)

    sys.argv = [sys.argv[0]] + sys.argv[2:]
    COMMANDS[cmd]()


if __name__ == "__main__":
    main()
