#!/usr/bin/env python3
"""Dosto-Crypt — TEXT • BINARY • HEXADECIMAL : point d'entrée."""

from __future__ import annotations

import sys


def _configure_stdio() -> None:
    """Force l'UTF-8 sur la sortie (consoles Windows / Termux mal configurées)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    try:
        from interface import menus
    except ModuleNotFoundError as exc:
        if (exc.name or "").split(".")[0] == "rich":
            print("Le module « rich » est requis : pip install -r requirements.txt", file=sys.stderr)
            return 1
        raise
    _configure_stdio()
    try:
        menus.run()
    except KeyboardInterrupt:
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
