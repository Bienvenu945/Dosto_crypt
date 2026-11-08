#!/usr/bin/env python3
"""Génère un exécutable autonome avec PyInstaller.

PyInstaller ne fait pas de compilation croisée : lancez ce script sous Linux
pour obtenir un exécutable Linux, et sous Windows pour obtenir un .exe.
"""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller est absent : pip install pyinstaller", file=sys.stderr)
        return 1
    command = [sys.executable, "-m", "PyInstaller", "--onefile", "--clean", "--name", "dosto-crypt", "main.py"]
    print("→", " ".join(command))
    code = subprocess.call(command)
    if code == 0:
        print("Exécutable généré dans le dossier dist/")
    return code


if __name__ == "__main__":
    sys.exit(main())
