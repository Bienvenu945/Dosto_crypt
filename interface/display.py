"""Affichage : bannière, menus, tableaux, panneaux et barres de progression."""

from __future__ import annotations

from typing import Iterable, Sequence

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich.text import Text

from core import file_manager as fm
from core.hexdump import HexLine
from core.storage import HistoryEntry

console = Console()
_accent = "cyan"


def set_accent(color: str) -> None:
    global _accent
    _accent = color


def accent() -> str:
    return _accent


# --------------------------------------------------------------------------- #
# Messages
# --------------------------------------------------------------------------- #
def _message(symbol: str, style: str, message: str) -> None:
    console.print(Text.assemble((f"{symbol} ", f"bold {style}"), message))


def success(message: str) -> None:
    _message("✔", "green", message)


def error(message: str) -> None:
    _message("✘", "red", message)


def warning(message: str) -> None:
    _message("!", "yellow", message)


def info(message: str) -> None:
    _message("•", _accent, message)


# --------------------------------------------------------------------------- #
# Structure
# --------------------------------------------------------------------------- #
def clear() -> None:
    console.clear()


def show_banner() -> None:
    title = Text("DOSTO-CRYPT", style=f"bold {_accent}", justify="center")
    subtitle = Text("TEXT • BINARY • HEXADECIMAL", style="dim", justify="center")
    console.print(
        Panel(Group(title, subtitle), box=box.DOUBLE, border_style=_accent, padding=(1, 4))
    )


def show_menu(title: str, options: Sequence[tuple[str, str]]) -> None:
    table = Table(
        box=box.ROUNDED,
        border_style=_accent,
        show_header=False,
        title=title,
        title_style=f"bold {_accent}",
    )
    table.add_column("Touche", style=f"bold {_accent}", justify="right", no_wrap=True)
    table.add_column("Action")
    for key, label in options:
        table.add_row(Text(key), Text(label))
    console.print(table)


def show_result(title: str, content: str, subtitle: str | None = None) -> None:
    console.print(
        Panel(
            Text(content),
            title=title,
            subtitle=subtitle,
            border_style=_accent,
            title_align="left",
            subtitle_align="right",
        )
    )


def _kv_table(title: str, rows: Iterable[tuple[str, str]]) -> Table:
    table = Table(box=box.SIMPLE_HEAD, show_header=False, title=title, title_style=f"bold {_accent}")
    table.add_column("Propriété", style=f"bold {_accent}", no_wrap=True)
    table.add_column("Valeur", overflow="fold")
    for key, value in rows:
        table.add_row(Text(key), Text(value))
    return table


# --------------------------------------------------------------------------- #
# Hex viewer / inspecteur
# --------------------------------------------------------------------------- #
def show_hexdump(lines: Iterable[HexLine], title: str) -> None:
    table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {_accent}", title=title)
    table.add_column("Offset", style="yellow", no_wrap=True)
    table.add_column("Hexadécimal", no_wrap=True)
    table.add_column("ASCII", style="green", no_wrap=True)
    for line in lines:
        table.add_row(Text(f"{line.offset:08x}"), Text(line.hex), Text(line.ascii))
    console.print(table)


def show_file_info(info_: fm.FileInfo) -> None:
    a = info_.analysis
    rows = [
        ("Nom", info_.name),
        ("Chemin", str(info_.path)),
        ("Extension", info_.extension or "(aucune)"),
        ("Taille", f"{fm.human_size(info_.size)} ({info_.size} octets)" if info_.size >= 1024 else f"{info_.size} octets"),
        ("Modifié le", info_.modified.strftime("%d/%m/%Y %H:%M:%S")),
        ("Type détecté", info_.detection.description),
        ("Type MIME", info_.detection.mime or "inconnu"),
        ("Entropie", f"{a.entropy:.2f} bits/octet — {a.entropy_label}"),
        ("ASCII imprimable", f"{a.printable_ratio:.1%}"),
        ("Octets nuls", str(a.null_bytes)),
        ("Octets distincts", f"{a.unique_bytes} / 256"),
        ("SHA-256", info_.sha256),
    ]
    if info_.sampled:
        rows.append(("Note", f"Détection et statistiques calculées sur les {fm.human_size(fm.SAMPLE_LIMIT)} initiaux."))
    console.print(_kv_table("File Inspector", rows))


# --------------------------------------------------------------------------- #
# Résultats d'écriture, lots, historique, réglages
# --------------------------------------------------------------------------- #
def show_write_result(result: fm.WriteResult) -> None:
    success(f"Fichier enregistré : {result.path} ({fm.human_size(result.size)})")
    console.print(Text(f"  SHA-256 des données : {result.sha256}", style="dim"))
    if result.verified:
        success("Intégrité vérifiée (relecture identique aux données d'origine).")
    else:
        warning("La relecture ne correspond pas aux données d'origine !")


def show_batch_results(results: Sequence[fm.BatchResult]) -> None:
    table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {_accent}", title="Résultat du lot")
    table.add_column("Source", overflow="fold")
    table.add_column("Résultat", overflow="fold")
    table.add_column("Taille", justify="right", no_wrap=True)
    for r in results:
        if r.ok:
            table.add_row(Text(r.source.name), Text(f"✔ {r.output.name}", style="green"), Text(fm.human_size(r.size)))
        else:
            table.add_row(Text(r.source.name), Text(f"✘ {r.message}", style="red"), Text("-"))
    console.print(table)
    ok = sum(r.ok for r in results)
    console.print(Text(f"{ok} réussi(s), {len(results) - ok} en erreur.", style="bold"))


def show_history(entries: Sequence[HistoryEntry], title: str = "Historique") -> None:
    if not entries:
        info("L'historique est vide.")
        return
    table = Table(box=box.SIMPLE_HEAD, header_style=f"bold {_accent}", title=title)
    for column in ("Date", "Opération", "Source", "Cible", "Taille"):
        table.add_column(column, overflow="fold", justify="right" if column == "Taille" else "left")
    for e in entries:
        table.add_row(
            Text(e.timestamp.replace("T", " ")),
            Text(e.operation),
            Text(e.source),
            Text(e.target),
            Text(fm.human_size(e.size)),
        )
    console.print(table)


def show_settings(settings: dict, home: str) -> None:
    console.print(
        _kv_table(
            "Réglages",
            [
                ("Couleur d'accent", settings["accent"]),
                ("Largeur du Hex Viewer", f"{settings['hexdump_width']} octets/ligne"),
                ("Dossier de sortie", settings["output_dir"]),
                ("Données de l'application", home),
            ],
        )
    )


# --------------------------------------------------------------------------- #
# Progression
# --------------------------------------------------------------------------- #
class ProgressReporter:
    """Barre de progression utilisable comme callback `(fait, total)`."""

    def __init__(self) -> None:
        self._progress = Progress(
            TextColumn("{task.description}", markup=False),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=True,
        )
        self._task = None

    def __enter__(self) -> "ProgressReporter":
        self._progress.start()
        return self

    def __exit__(self, *exc_info) -> None:
        self._progress.stop()

    def start(self, description: str, total: int | None = None) -> None:
        if self._task is None:
            self._task = self._progress.add_task(description, total=total)
        else:
            self._progress.reset(self._task, description=description, total=total)

    def __call__(self, done: int, total: int) -> None:
        if self._task is not None:
            self._progress.update(self._task, completed=done, total=total)
