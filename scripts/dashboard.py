#!/usr/bin/env python3
"""Atajo: inicia Django en el puerto 8080 (equivalente a runserver 8080)."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uniform_project.settings")

from django.core.management import execute_from_command_line

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else "8080"
    print(f"Django: http://8000:{port}/")
    print("Detener con Ctrl+C")
    execute_from_command_line(["manage.py", "runserver", port])
