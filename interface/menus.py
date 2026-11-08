"""Menus et parcours interactifs de Dosto-Crypt."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from core import converter, hexdump, storage
from core import file_manager as fm
from core.file_manager import FileManagerError
from interface import display, prompts
from utils.validators import ValidationError

HANDLED_ERRORS = (converter.ConversionError, FileManagerError, ValidationError, storage.StorageError)
HEX_PAGE_ROWS = 16

MAIN_OPTIONS = [
    ("1", "Text to Binary / Hexadecimal"),
    ("2", "Binary / Hexadecimal to Text"),
    ("3", "Hex Viewer"),
    ("4", "File Inspector"),
    ("5", "Conversion History"),
    ("6", "Exit"),
    ("s", "Settings"),
]

Handler = Callable[[], None]


# --------------------------------------------------------------------------- #
# Infrastructure de navigation
# --------------------------------------------------------------------------- #
def _run(handler: Handler) -> None:
    """Exécute un parcours : erreurs attendues et Ctrl+C ne quittent jamais l'appli."""
    try:
        handler()
    except HANDLED_ERRORS as exc:
        display.error(str(exc))
    except (KeyboardInterrupt, EOFError):
        display.console.print()
        display.warning("Opération annulée.")
    prompts.pause()


def _submenu(title: str, entries: Sequence[tuple[str, str, Handler]]) -> None:
    handlers = {key: handler for key, _, handler in entries}
    options = [(key, label) for key, label, _ in entries] + [("0", "Retour")]
    while True:
        display.show_menu(title, options)
        try:
            choice = prompts.ask_choice("Votre choix", [*handlers, "0"])
        except (KeyboardInterrupt, EOFError):
            display.console.print()
            return
        if choice == "0":
            return
        _run(handlers[choice])


def _settings() -> dict:
    return storage.load_settings()


def _record(operation: str, source: str, target: str, size: int, sha256: str) -> None:
    if not storage.add_history(operation, source, target, size, sha256):
        display.warning("Historique non enregistré (dossier de données inaccessible).")


# --------------------------------------------------------------------------- #
# Aides de saisie de destination
# --------------------------------------------------------------------------- #
def _ask_destination(kind: str, default_name: str | None = None) -> Path:
    directory = fm.resolve_path(prompts.ask_text("Dossier de destination", default=_settings()["output_dir"]))
    if not directory.exists() and not prompts.ask_confirm(f"Le dossier « {directory} » n'existe pas. Le créer ?"):
        raise FileManagerError("Dossier de destination absent : opération annulée.")
    name = prompts.ask_text("Nom du fichier", default=default_name or fm.default_filename(kind))
    return fm.build_output_path(directory, name, kind)


def _overwrite_allowed(path: Path) -> bool:
    if not path.exists():
        return True
    if prompts.ask_confirm(f"« {path} » existe déjà. Écraser ?", default=False):
        return True
    display.warning("Enregistrement annulé.")
    return False


# --------------------------------------------------------------------------- #
# 1. Texte -> binaire / hexadécimal
# --------------------------------------------------------------------------- #
def text_to_representation_menu() -> None:
    _submenu(
        "Text to Binary / Hexadecimal",
        [
            ("1", "Saisie directe (une ligne)", lambda: _flow_text(multiline=False)),
            ("2", "Saisie multiligne", lambda: _flow_text(multiline=True)),
            ("3", "Convertir un fichier existant", _flow_convert_file),
            ("4", "Conversion par lots (dossier)", _flow_batch),
        ],
    )


def _flow_text(multiline: bool) -> None:
    text = prompts.ask_multiline() if multiline else prompts.ask_text("Texte à convertir")
    data = converter.text_to_bytes(text)
    kind = prompts.ask_output_kind()
    label = fm.KIND_LABELS[kind]
    display.show_result(f"Aperçu — {label}", fm.render(data, kind), subtitle=f"{len(data)} octet(s)")

    source = f"texte ({len(data)} octets)"
    operation = f"Texte → {label}"
    checksum = fm.sha256_bytes(data)
    if not prompts.ask_confirm("Enregistrer dans un fichier ?", default=True):
        _record(operation, source, "(affichage)", len(data), checksum)
        return
    target = _ask_destination(kind)
    if not _overwrite_allowed(target):
        return
    result = fm.save_output(target, data, kind, overwrite=True)
    display.show_write_result(result)
    _record(operation, source, str(result.path), result.size, result.sha256)


def _flow_convert_file() -> None:
    source = fm.check_readable_file(prompts.ask_text("Chemin du fichier source"))
    kind = prompts.ask_output_kind(stream_only=True)
    target = _ask_destination(kind, default_name=source.name + fm.EXTENSIONS[kind])
    if not _overwrite_allowed(target):
        return
    size = source.stat().st_size
    with display.ProgressReporter() as reporter:
        reporter.start(f"Conversion de {source.name}", total=size)
        result = fm.convert_file(source, target, kind, overwrite=True, progress=reporter)
    display.show_write_result(result)
    _record(f"Fichier → {fm.KIND_LABELS[kind]}", str(source), str(result.path), result.size, result.sha256)


def _flow_batch() -> None:
    files = fm.list_files(
        prompts.ask_text("Dossier source"), prompts.ask_text("Filtre (ex. *.txt)", default="*")
    )
    if not files:
        raise FileManagerError("Aucun fichier ne correspond au filtre.")
    display.info(f"{len(files)} fichier(s) trouvé(s).")
    kind = prompts.ask_output_kind(stream_only=True)
    out_dir = prompts.ask_text("Dossier de destination", default=_settings()["output_dir"])
    overwrite = prompts.ask_confirm("Écraser les fichiers existants ?", default=False)
    label = fm.KIND_LABELS[kind]
    if not prompts.ask_confirm(f"Convertir {len(files)} fichier(s) vers {label} ?"):
        display.warning("Lot annulé.")
        return
    with display.ProgressReporter() as reporter:
        results = fm.batch_convert(
            files, out_dir, kind, overwrite, on_start=lambda p: reporter.start(p.name), progress=reporter
        )
    display.show_batch_results(results)
    for r in results:
        if r.ok:
            _record(f"Lot → {label}", str(r.source), str(r.output), r.size, r.sha256)


# --------------------------------------------------------------------------- #
# 2. Binaire / hexadécimal -> texte
# --------------------------------------------------------------------------- #
def representation_to_text_menu() -> None:
    _submenu(
        "Binary / Hexadecimal to Text",
        [
            ("1", "Saisir du binaire (0/1)", lambda: _flow_decode_input(converter.FORMAT_BINARY)),
            ("2", "Saisir de l'hexadécimal", lambda: _flow_decode_input(converter.FORMAT_HEX)),
            ("3", "Lire un fichier (.bin, .hex, .txt)", _flow_decode_file),
        ],
    )


def _offer_save_text(text: str, operation: str, source: str) -> None:
    if not prompts.ask_confirm("Enregistrer le texte dans un fichier .txt ?", default=False):
        _record(operation, source, "(affichage)", len(text.encode("utf-8")), "")
        return
    target = _ask_destination(fm.KIND_TEXT)
    if not _overwrite_allowed(target):
        return
    result = fm.save_text(target, text, overwrite=True)
    display.show_write_result(result)
    _record(operation, source, str(result.path), result.size, result.sha256)


def _flow_decode_input(fmt: str) -> None:
    label = "Binaire" if fmt == converter.FORMAT_BINARY else "Hexadécimal"
    raw = prompts.ask_data_block(f"Collez ou saisissez le {label.lower()}")
    data = converter.decode_representation(raw, fmt)
    text = converter.bytes_to_text(data)
    display.show_result("Texte décodé", text, subtitle=f"{len(data)} octet(s)")
    _offer_save_text(text, f"{label} → Texte", f"{label.lower()} ({len(data)} octets)")


def _flow_decode_file() -> None:
    text, loaded = fm.extract_text(prompts.ask_text("Chemin du fichier"))
    display.info(f"{loaded.path.name} : lu comme {fm.SOURCE_LABELS[loaded.source]}, {len(loaded.data)} octet(s).")
    display.show_result("Texte extrait", text)
    _offer_save_text(text, "Fichier → Texte", str(loaded.path))


# --------------------------------------------------------------------------- #
# 3. Hex Viewer
# --------------------------------------------------------------------------- #
def hex_viewer() -> None:
    path = fm.check_readable_file(prompts.ask_text("Chemin du fichier"))
    size = path.stat().st_size
    if size == 0:
        raise FileManagerError(f"Le fichier est vide : {path}")
    width = _settings()["hexdump_width"]
    page = width * HEX_PAGE_ROWS
    offset = prompts.ask_int("Offset de départ (décimal ou 0x…)", default=0, minimum=0, maximum=size - 1)
    while True:
        chunk = fm.read_range(path, offset, page)
        last = offset + len(chunk) - 1
        display.show_hexdump(
            hexdump.iter_hexlines(chunk, offset, width),
            title=f"{path.name} — 0x{offset:x} à 0x{last:x} sur {size} octet(s)",
        )
        has_next = offset + page < size
        command = prompts.ask_choice(
            "n = suivant, p = précédent, g = aller à, q = quitter",
            ["n", "p", "g", "q"],
            default="n" if has_next else "q",
        )
        if command == "q":
            return
        if command == "n":
            if has_next:
                offset += page
            else:
                display.warning("Fin du fichier atteinte.")
        elif command == "p":
            offset = max(0, offset - page)
        else:
            offset = prompts.ask_int("Aller à l'offset", default=offset, minimum=0, maximum=size - 1)


# --------------------------------------------------------------------------- #
# 4. File Inspector
# --------------------------------------------------------------------------- #
def file_inspector() -> None:
    raw = prompts.ask_text("Chemin du fichier")
    with display.ProgressReporter() as reporter:
        reporter.start("Analyse en cours…")
        details = fm.inspect_file(raw, progress=reporter)
    display.show_file_info(details)
    if details.head:
        display.show_hexdump(
            hexdump.preview(details.head, 64, _settings()["hexdump_width"]),
            title="Aperçu des premiers octets",
        )


# --------------------------------------------------------------------------- #
# 5. Historique
# --------------------------------------------------------------------------- #
def history_menu() -> None:
    display.show_history(storage.load_history()[-20:][::-1], "Dernières conversions")
    _submenu(
        "Conversion History",
        [
            ("1", "Afficher tout l'historique", lambda: display.show_history(storage.load_history()[::-1])),
            ("2", "Exporter (JSON ou CSV)", _export_history),
            ("3", "Vider l'historique", _clear_history),
        ],
    )


def _export_history() -> None:
    fmt = prompts.ask_choice("Format d'export (json ou csv)", ["json", "csv"], default="json")
    default = str(Path(_settings()["output_dir"]) / f"dosto_history.{fmt}")
    target = fm.resolve_path(prompts.ask_text("Fichier d'export", default=default))
    if not _overwrite_allowed(target):
        return
    display.success(f"Historique exporté : {storage.export_history(target, fmt)}")


def _clear_history() -> None:
    if prompts.ask_confirm("Supprimer définitivement tout l'historique ?", default=False):
        if storage.clear_history():
            display.success("Historique vidé.")
        else:
            display.error("Impossible de vider l'historique.")


# --------------------------------------------------------------------------- #
# Réglages
# --------------------------------------------------------------------------- #
def settings_menu() -> None:
    display.show_settings(_settings(), str(storage.app_home()))
    _submenu(
        "Settings",
        [
            ("1", "Couleur d'accent", lambda: _change_setting("accent")),
            ("2", "Largeur du Hex Viewer", lambda: _change_setting("hexdump_width")),
            ("3", "Dossier de sortie par défaut", lambda: _change_setting("output_dir")),
            ("4", "Réinitialiser les réglages", _reset_settings),
        ],
    )


def _change_setting(key: str) -> None:
    settings = _settings()
    if key == "accent":
        settings[key] = prompts.ask_choice(
            f"Couleur ({', '.join(storage.ACCENT_CHOICES)})", storage.ACCENT_CHOICES, default=settings[key]
        )
        display.set_accent(settings[key])
    elif key == "hexdump_width":
        choices = [str(w) for w in storage.WIDTH_CHOICES]
        settings[key] = int(prompts.ask_choice("Octets par ligne", choices, default=str(settings[key])))
    else:
        settings[key] = prompts.ask_text("Dossier de sortie par défaut", default=settings[key]).strip() or "."
    _save(settings)


def _reset_settings() -> None:
    settings = dict(storage.DEFAULT_SETTINGS)
    display.set_accent(settings["accent"])
    _save(settings)


def _save(settings: dict) -> None:
    if storage.save_settings(settings):
        display.success("Réglages enregistrés.")
    else:
        display.error("Impossible d'enregistrer les réglages (dossier de données inaccessible).")


# --------------------------------------------------------------------------- #
# Boucle principale
# --------------------------------------------------------------------------- #
def run() -> None:
    display.set_accent(_settings()["accent"])
    actions: dict[str, Handler] = {
        "1": text_to_representation_menu,
        "2": representation_to_text_menu,
        "3": lambda: _run(hex_viewer),
        "4": lambda: _run(file_inspector),
        "5": history_menu,
        "s": settings_menu,
    }
    while True:
        display.clear()
        display.show_banner()
        display.show_menu("Menu principal", MAIN_OPTIONS)
        try:
            choice = prompts.ask_choice("Votre choix", [*actions, "6"])
        except (KeyboardInterrupt, EOFError):
            choice = "6"
        if choice == "6":
            display.info("Au revoir !")
            return
        actions[choice]()
