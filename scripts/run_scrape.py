#!/usr/bin/env python3
"""
Atajo para scraping.

Equivalente a: python -m src scrape run ...
Ver también: python -m src scrape list
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.cli.scrape import app

if __name__ == "__main__":
    app()
