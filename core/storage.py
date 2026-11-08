"""Persistance légère : réglages et historique des conversions (JSON)."""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

APP_DIR_NAME = ".dosto-crypt"
HISTORY_LIMIT = 500
ACCENT_CHOICES = ("cyan", "green", "magenta", "yellow", "blue", "red", "white")
WIDTH_CHOICES = (8, 16, 24, 32)
DEFAULT_SETTINGS = {"accent": "cyan", "hexdump_width": 16, "output_dir": "."}


class StorageError(Exception):
    """Erreur de lecture ou d'écriture des données de l'application."""


def app_home() -> Path:
    """Dossier de données (surchargeable via la variable DOSTO_CRYPT_HOME)."""
    override = os.environ.get("DOSTO_CRYPT_HOME")
    return Path(override).expanduser() if override else Path.home() / APP_DIR_NAME


def settings_path() -> Path:
    return app_home() / "settings.json"


def history_path() -> Path:
    return app_home() / "history.json"


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# Réglages
# --------------------------------------------------------------------------- #
def load_settings() -> dict:
    """Réglages valides ; toute valeur absente ou incorrecte retombe sur le défaut."""
    settings = dict(DEFAULT_SETTINGS)
    stored = _read_json(settings_path(), {})
    if isinstance(stored, dict):
        for key, default in DEFAULT_SETTINGS.items():
            if isinstance(stored.get(key), type(default)):
                settings[key] = stored[key]
    if settings["accent"] not in ACCENT_CHOICES:
        settings["accent"] = DEFAULT_SETTINGS["accent"]
    if settings["hexdump_width"] not in WIDTH_CHOICES:
        settings["hexdump_width"] = DEFAULT_SETTINGS["hexdump_width"]
    return settings


def save_settings(settings: dict) -> bool:
    try:
        _write_json(settings_path(), {k: settings[k] for k in DEFAULT_SETTINGS})
    except OSError:
        return False
    return True


# --------------------------------------------------------------------------- #
# Historique
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class HistoryEntry:
    timestamp: str
    operation: str
    source: str
    target: str
    size: int
    sha256: str = ""


_FIELDS = [f.name for f in fields(HistoryEntry)]


def load_history() -> list[HistoryEntry]:
    rows = _read_json(history_path(), [])
    entries: list[HistoryEntry] = []
    if not isinstance(rows, list):
        return entries
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            entries.append(HistoryEntry(**{k: row[k] for k in _FIELDS if k in row}))
        except TypeError:
            continue  # ligne incomplète : ignorée
    return entries


def add_history(
    operation: str, source: str, target: str = "-", size: int = 0, sha256: str = ""
) -> bool:
    """Ajoute une entrée ; l'historique n'est jamais bloquant (retourne False si échec)."""
    entry = HistoryEntry(
        timestamp=dt.datetime.now().isoformat(timespec="seconds"),
        operation=operation,
        source=source,
        target=target,
        size=size,
        sha256=sha256,
    )
    entries = (load_history() + [entry])[-HISTORY_LIMIT:]
    try:
        _write_json(history_path(), [asdict(e) for e in entries])
    except OSError:
        return False
    return True


def clear_history() -> bool:
    try:
        _write_json(history_path(), [])
    except OSError:
        return False
    return True


def export_history(destination: Path | str, fmt: str = "json") -> Path:
    """Exporte l'historique en JSON ou CSV."""
    if fmt not in ("json", "csv"):
        raise StorageError(f"Format d'export inconnu : {fmt!r}.")
    path = Path(destination).expanduser()
    rows = [asdict(e) for e in load_history()]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if fmt == "json":
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=_FIELDS)
                writer.writeheader()
                writer.writerows(rows)
    except OSError as exc:
        raise StorageError(f"Export impossible vers « {path} » : {exc.strerror or exc}.") from exc
    return path
