"""Saisies interactives : choix, texte, multiligne, chemins, confirmations."""

from __future__ import annotations

from typing import Sequence

from rich.prompt import Confirm, Prompt
from rich.text import Text

from core import file_manager as fm
from interface import display
from interface.display import console
from utils.validators import ValidationError, parse_int

END_MARKER = ":fin"


def ask_choice(label: str, choices: Sequence[str], default: str | None = None) -> str:
    return Prompt.ask(
        f"[bold {display.accent()}]{label}[/]",
        console=console,
        choices=list(choices),
        default=default,
        show_choices=False,
    )


def ask_text(label: str, default: str | None = None) -> str:
    kwargs = {} if default is None else {"default": default}
    return Prompt.ask(f"[bold {display.accent()}]{label}[/]", console=console, **kwargs)


def ask_confirm(label: str, default: bool = True) -> bool:
    return Confirm.ask(f"[bold {display.accent()}]{label}[/]", console=console, default=default)


def ask_int(label: str, default: int, minimum: int = 0, maximum: int | None = None) -> int:
    while True:
        raw = ask_text(label, default=str(default))
        try:
            return parse_int(raw, minimum, maximum)
        except ValidationError as exc:
            display.error(str(exc))


def _read_block(hint: str, is_end) -> str:
    console.print(Text(hint, style="dim"))
    lines: list[str] = []
    while True:
        try:
            line = console.input(f"[{display.accent()}]│[/] ")
        except EOFError:
            break
        if is_end(line):
            break
        lines.append(line)
    return "\n".join(lines)


def ask_multiline() -> str:
    """Texte multiligne : se termine par une ligne « :fin » (ou Ctrl+D)."""
    return _read_block(
        f"Saisissez votre texte. Terminez par une ligne contenant uniquement {END_MARKER} (ou Ctrl+D).",
        lambda line: line.strip() == END_MARKER,
    )


def ask_data_block(label: str) -> str:
    """Données binaires/hexa (collage multiligne) : se termine par une ligne vide."""
    return _read_block(f"{label} — terminez par une ligne vide.", lambda line: not line.strip())


def ask_output_kind(stream_only: bool = False) -> str:
    """Choix du format de sortie ; `stream_only` exclut le .bin (conversion de fichiers)."""
    options = [
        ("1", fm.KIND_LABELS[fm.KIND_HEX], fm.KIND_HEX),
        ("2", fm.KIND_LABELS[fm.KIND_BITS], fm.KIND_BITS),
    ]
    if not stream_only:
        options.append(("3", fm.KIND_LABELS[fm.KIND_BIN], fm.KIND_BIN))
    display.show_menu("Format de sortie", [(key, label) for key, label, _ in options])
    choice = ask_choice("Format", [key for key, _, _ in options], default="1")
    return {key: kind for key, _, kind in options}[choice]


def pause() -> None:
    try:
        console.input(Text("\nAppuyez sur Entrée pour continuer…", style="dim"))
    except (EOFError, KeyboardInterrupt):
        console.print()
