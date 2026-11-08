"""Création, lecture, vérification et inspection de fichiers .bin / .hex / .txt."""

from __future__ import annotations

import contextlib
import datetime as dt
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from core import converter, detector
from utils import validators

# Formats de sortie
KIND_BIN = "bin"      # octets bruts
KIND_HEX = "hex"      # hexadécimal textuel
KIND_BITS = "bits"    # binaire textuel (0/1) dans un .txt
KIND_TEXT = "text"    # texte UTF-8
EXTENSIONS = {KIND_BIN: ".bin", KIND_HEX: ".hex", KIND_BITS: ".txt", KIND_TEXT: ".txt"}
KIND_LABELS = {
    KIND_BIN: "Binaire brut (.bin)",
    KIND_HEX: "Hexadécimal (.hex)",
    KIND_BITS: "Binaire texte 0/1 (.txt)",
    KIND_TEXT: "Texte UTF-8 (.txt)",
}
STREAM_KINDS = (KIND_HEX, KIND_BITS)
BYTES_PER_LINE = {KIND_HEX: 32, KIND_BITS: 4, KIND_BIN: 4}

# Formats de lecture
SRC_RAW = "raw"
SRC_HEX = "hex"
SRC_BINARY = "binary"
SOURCE_FOR_KIND = {KIND_BIN: SRC_RAW, KIND_HEX: SRC_HEX, KIND_BITS: SRC_BINARY}
SOURCE_LABELS = {SRC_RAW: "octets bruts", SRC_HEX: "hexadécimal", SRC_BINARY: "binaire texte"}

CHUNK_SIZE = 1 << 20      # 1 Mio (multiple des largeurs de ligne)
SAMPLE_LIMIT = 4 << 20    # 4 Mio analysés pour la détection

ProgressCallback = Callable[[int, int], None]


class FileManagerError(Exception):
    """Erreur de lecture, d'écriture ou de vérification de fichier."""


class FileAlreadyExistsError(FileManagerError):
    def __init__(self, path: Path):
        super().__init__(f"Le fichier existe déjà : {path}")
        self.path = path


@dataclass(frozen=True)
class LoadedData:
    data: bytes
    source: str
    path: Path


@dataclass(frozen=True)
class WriteResult:
    path: Path
    size: int
    sha256: str
    verified: bool


@dataclass(frozen=True)
class FileInfo:
    path: Path
    name: str
    extension: str
    size: int
    modified: dt.datetime
    sha256: str
    detection: detector.Detection
    analysis: detector.Analysis
    head: bytes
    sampled: bool


@dataclass(frozen=True)
class BatchResult:
    source: Path
    output: Path | None
    ok: bool
    message: str
    size: int = 0
    sha256: str = ""


# --------------------------------------------------------------------------- #
# Utilitaires
# --------------------------------------------------------------------------- #
def human_size(size: int) -> str:
    value = float(size)
    for unit in ("o", "Ko", "Mo", "Go"):
        if value < 1024:
            return f"{int(value)} o" if unit == "o" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} To"


def _os_error(action: str, path: Path, exc: OSError) -> FileManagerError:
    return FileManagerError(f"Impossible de {action} « {path} » : {exc.strerror or exc}.")


def resolve_path(raw: str | Path) -> Path:
    """Nettoie une saisie (guillemets, ~) et retourne un Path."""
    return Path(str(raw).strip().strip("\"'")).expanduser()


def check_readable_file(raw: str | Path) -> Path:
    path = resolve_path(raw)
    if not path.exists():
        raise FileManagerError(f"Fichier introuvable : {path}")
    if not path.is_file():
        raise FileManagerError(f"Ce chemin n'est pas un fichier : {path}")
    if not os.access(path, os.R_OK):
        raise FileManagerError(f"Lecture non autorisée : {path}")
    return path


def ensure_directory(raw: str | Path) -> Path:
    path = resolve_path(raw)
    if path.exists() and not path.is_dir():
        raise FileManagerError(f"« {path} » existe mais n'est pas un dossier.")
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise _os_error("créer le dossier", path, exc) from exc
    return path


def default_filename(kind: str, prefix: str = "dosto") -> str:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}{EXTENSIONS[kind]}"


def build_output_path(directory: str | Path, filename: str, kind: str) -> Path:
    name = validators.validate_filename(filename, EXTENSIONS[kind])
    return resolve_path(directory) / name


def list_files(directory: str | Path, pattern: str = "*") -> list[Path]:
    """Fichiers (non récursif) d'un dossier correspondant à un motif glob."""
    folder = resolve_path(directory)
    if not folder.is_dir():
        raise FileManagerError(f"Dossier introuvable : {folder}")
    try:
        return sorted(
            p for p in folder.glob(pattern or "*")
            if p.is_file() and not p.name.endswith(".tmp")
        )
    except (OSError, ValueError, NotImplementedError) as exc:
        raise FileManagerError(f"Motif de recherche invalide : {pattern!r}.") from exc


# --------------------------------------------------------------------------- #
# Hachage / intégrité
# --------------------------------------------------------------------------- #
def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(raw: str | Path, progress: ProgressCallback | None = None) -> str:
    path = check_readable_file(raw)
    digest = hashlib.sha256()
    try:
        total = path.stat().st_size
        done = 0
        with path.open("rb") as handle:
            while chunk := handle.read(CHUNK_SIZE):
                digest.update(chunk)
                done += len(chunk)
                if progress:
                    progress(done, total)
    except OSError as exc:
        raise _os_error("lire", path, exc) from exc
    return digest.hexdigest()


# --------------------------------------------------------------------------- #
# Lecture
# --------------------------------------------------------------------------- #
def read_bytes(raw: str | Path, limit: int | None = None) -> bytes:
    path = check_readable_file(raw)
    try:
        with path.open("rb") as handle:
            return handle.read() if limit is None else handle.read(limit)
    except OSError as exc:
        raise _os_error("lire", path, exc) from exc


def read_range(raw: str | Path, offset: int, length: int) -> bytes:
    """Lit `length` octets à partir de `offset` (sans charger tout le fichier)."""
    path = check_readable_file(raw)
    try:
        with path.open("rb") as handle:
            handle.seek(offset)
            return handle.read(length)
    except OSError as exc:
        raise _os_error("lire", path, exc) from exc


def _guess_source(path: Path, data: bytes) -> str:
    extension = path.suffix.lower()
    if extension == ".bin":
        return SRC_RAW
    if extension == ".hex":
        return SRC_HEX
    kind = detector.detect_content(data[:SAMPLE_LIMIT]).kind
    if kind == detector.KIND_HEX_TEXT:
        return SRC_HEX
    if kind == detector.KIND_BINARY_TEXT:
        return SRC_BINARY
    return SRC_RAW


def load_file(raw: str | Path, forced: str | None = None) -> LoadedData:
    """Lit un fichier et retourne les octets d'origine (décode .hex / binaire texte)."""
    path = check_readable_file(raw)
    data = read_bytes(path)
    if not data:
        raise FileManagerError(f"Le fichier est vide : {path}")
    source = forced or _guess_source(path, data)
    if source == SRC_RAW:
        return LoadedData(data, source, path)
    try:
        text = data.decode("ascii")
        decoded = (
            converter.hex_to_bytes(text) if source == SRC_HEX else converter.binary_to_bytes(text)
        )
    except UnicodeDecodeError:
        raise FileManagerError(
            f"« {path.name} » n'est pas de l'{SOURCE_LABELS[source]} : "
            "il contient des caractères non ASCII."
        ) from None
    except converter.ConversionError as exc:
        raise FileManagerError(
            f"Contenu {SOURCE_LABELS[source]} invalide dans « {path.name} » : {exc}"
        ) from exc
    return LoadedData(decoded, source, path)


def extract_text(raw: str | Path, forced: str | None = None) -> tuple[str, LoadedData]:
    """Extrait le texte UTF-8 d'origine d'un fichier .bin / .hex / .txt."""
    loaded = load_file(raw, forced)
    try:
        return converter.bytes_to_text(loaded.data), loaded
    except converter.ConversionError as exc:
        raise FileManagerError(
            f"Extraction impossible pour « {loaded.path.name} » : {exc} "
            "Essayez le Hex Viewer pour visualiser les octets."
        ) from exc


# --------------------------------------------------------------------------- #
# Écriture
# --------------------------------------------------------------------------- #
def render(data: bytes, kind: str) -> str:
    """Représentation textuelle (hex ou bits) ; .bin est affiché en bits."""
    if kind == KIND_HEX:
        return converter.bytes_to_hex(data, bytes_per_line=BYTES_PER_LINE[KIND_HEX])
    return converter.bytes_to_binary(data, bytes_per_line=BYTES_PER_LINE[KIND_BITS])


def _write_atomic(path: Path, payload: bytes, overwrite: bool) -> None:
    if path.is_dir():
        raise FileManagerError(f"« {path} » est un dossier.")
    if path.exists() and not overwrite:
        raise FileAlreadyExistsError(path)
    ensure_directory(path.parent)
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_bytes(payload)
        os.replace(tmp, path)
    except OSError as exc:
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise _os_error("écrire", path, exc) from exc


def save_output(
    raw_path: str | Path, data: bytes, kind: str, overwrite: bool = False
) -> WriteResult:
    """Écrit des octets en .bin / .hex / binaire texte, puis vérifie l'intégrité."""
    if kind not in SOURCE_FOR_KIND:
        raise FileManagerError(f"Format de sortie inconnu : {kind!r}.")
    if not data:
        raise FileManagerError("Aucune donnée à enregistrer.")
    path = resolve_path(raw_path)
    payload = data if kind == KIND_BIN else (render(data, kind) + "\n").encode("ascii")
    _write_atomic(path, payload, overwrite)
    try:
        verified = load_file(path, SOURCE_FOR_KIND[kind]).data == data
    except FileManagerError:
        verified = False
    return WriteResult(path, len(payload), sha256_bytes(data), verified)


def save_text(raw_path: str | Path, text: str, overwrite: bool = False) -> WriteResult:
    """Enregistre un texte en UTF-8 (.txt) et vérifie la relecture."""
    if not text:
        raise FileManagerError("Aucun texte à enregistrer.")
    path = resolve_path(raw_path)
    payload = text.encode(converter.ENCODING)
    _write_atomic(path, payload, overwrite)
    return WriteResult(path, len(payload), sha256_bytes(payload), read_bytes(path) == payload)


def _verify_stream(path: Path, kind: str, expected_sha256: str) -> bool:
    decode = converter.hex_to_bytes if kind == KIND_HEX else converter.binary_to_bytes
    digest = hashlib.sha256()
    with path.open("r", encoding="ascii") as handle:
        for line in handle:
            if line.strip():
                digest.update(decode(line))
    return digest.hexdigest() == expected_sha256


def convert_file(
    source: str | Path,
    destination: str | Path,
    kind: str,
    overwrite: bool = False,
    progress: ProgressCallback | None = None,
) -> WriteResult:
    """Convertit un fichier (même volumineux) en .hex ou binaire texte, par blocs."""
    if kind not in STREAM_KINDS:
        raise FileManagerError("La conversion de fichier produit du .hex ou du binaire texte.")
    src = check_readable_file(source)
    dst = resolve_path(destination)
    if dst.is_dir():
        raise FileManagerError(f"« {dst} » est un dossier.")
    with contextlib.suppress(OSError):
        if dst.exists() and dst.samefile(src):
            raise FileManagerError("Le fichier de sortie doit être différent de la source.")
    if dst.exists() and not overwrite:
        raise FileAlreadyExistsError(dst)
    try:
        total = src.stat().st_size
    except OSError as exc:
        raise _os_error("lire", src, exc) from exc
    if total == 0:
        raise FileManagerError(f"Le fichier source est vide : {src}")
    ensure_directory(dst.parent)

    tmp = dst.with_name(dst.name + ".tmp")
    digest = hashlib.sha256()
    done = 0
    try:
        with src.open("rb") as fin, tmp.open("w", encoding="ascii", newline="\n") as fout:
            while block := fin.read(CHUNK_SIZE):
                digest.update(block)
                fout.write(render(block, kind) + "\n")
                done += len(block)
                if progress:
                    progress(done, total)
        checksum = digest.hexdigest()
        if not _verify_stream(tmp, kind, checksum):
            raise FileManagerError("Échec de la vérification d'intégrité : sortie non écrite.")
        os.replace(tmp, dst)
        size = dst.stat().st_size
    except OSError as exc:
        raise _os_error("convertir", src, exc) from exc
    finally:
        with contextlib.suppress(OSError):
            tmp.unlink()
    return WriteResult(dst, size, checksum, True)


def batch_convert(
    files: list[Path],
    out_dir: str | Path,
    kind: str,
    overwrite: bool = False,
    on_start: Callable[[Path], None] | None = None,
    progress: ProgressCallback | None = None,
) -> list[BatchResult]:
    """Convertit plusieurs fichiers ; une erreur n'interrompt pas le lot."""
    folder = ensure_directory(out_dir)
    results: list[BatchResult] = []
    for source in files:
        if on_start:
            on_start(source)
        target = folder / (source.name + EXTENSIONS[kind])
        try:
            written = convert_file(source, target, kind, overwrite, progress)
        except FileManagerError as exc:
            results.append(BatchResult(source, None, False, str(exc)))
        else:
            results.append(
                BatchResult(source, written.path, True, "OK", written.size, written.sha256)
            )
    return results


# --------------------------------------------------------------------------- #
# Inspection
# --------------------------------------------------------------------------- #
def inspect_file(raw: str | Path, progress: ProgressCallback | None = None) -> FileInfo:
    """Propriétés, type détecté et statistiques d'un fichier."""
    path = check_readable_file(raw)
    try:
        stat = path.stat()
    except OSError as exc:
        raise _os_error("lire", path, exc) from exc
    sample = read_bytes(path, SAMPLE_LIMIT)
    return FileInfo(
        path=path.resolve(),
        name=path.name,
        extension=path.suffix.lower(),
        size=stat.st_size,
        modified=dt.datetime.fromtimestamp(stat.st_mtime),
        sha256=sha256_file(path, progress),
        detection=detector.detect_content(sample),
        analysis=detector.analyze(sample),
        head=sample[:128],
        sampled=stat.st_size > SAMPLE_LIMIT,
    )
