#!/usr/bin/env python3
"""
Atajo para exportar datos.

Equivalente a: python -m src export --format csv
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.cli.export_cmd import app

if __name__ == "__main__":
    app()
