"""Détection du type de contenu et analyse statistique des octets."""

from __future__ import annotations

import codecs
import math
from collections import Counter
from dataclasses import dataclass

from utils.validators import is_valid_binary, is_valid_hex

KIND_EMPTY = "empty"
KIND_SIGNATURE = "signature"
KIND_BINARY_TEXT = "binary-text"
KIND_HEX_TEXT = "hex-text"
KIND_UTF8 = "utf8-text"
KIND_BINARY = "binary-data"

# (préfixe, description, type MIME, extension usuelle)
SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "Image PNG", "image/png", ".png"),
    (b"\xff\xd8\xff", "Image JPEG", "image/jpeg", ".jpg"),
    (b"GIF87a", "Image GIF", "image/gif", ".gif"),
    (b"GIF89a", "Image GIF", "image/gif", ".gif"),
    (b"%PDF-", "Document PDF", "application/pdf", ".pdf"),
    (b"PK\x03\x04", "Archive ZIP (ou docx, xlsx, jar, apk…)", "application/zip", ".zip"),
    (b"\x7fELF", "Exécutable ELF (Linux)", "application/x-executable", ""),
    (b"\x1f\x8b", "Archive gzip", "application/gzip", ".gz"),
    (b"7z\xbc\xaf\x27\x1c", "Archive 7-Zip", "application/x-7z-compressed", ".7z"),
    (b"Rar!\x1a\x07", "Archive RAR", "application/vnd.rar", ".rar"),
    (b"\xfd7zXZ\x00", "Archive XZ", "application/x-xz", ".xz"),
    (b"SQLite format 3\x00", "Base de données SQLite", "application/vnd.sqlite3", ".sqlite"),
    (b"OggS", "Conteneur Ogg", "application/ogg", ".ogg"),
    (b"fLaC", "Audio FLAC", "audio/flac", ".flac"),
    (b"RIFF", "Conteneur RIFF (WAV, AVI, WebP…)", "application/octet-stream", ""),
)

_NON_PRINTABLE = bytes(b for b in range(256) if not (32 <= b < 127 or b in (9, 10, 13)))


@dataclass(frozen=True)
class Detection:
    kind: str
    description: str
    mime: str | None = None
    extension: str | None = None


@dataclass(frozen=True)
class Analysis:
    size: int
    entropy: float
    printable_ratio: float
    null_bytes: int
    unique_bytes: int

    @property
    def entropy_label(self) -> str:
        return describe_entropy(self.entropy)


def _is_pe(data: bytes) -> bool:
    if len(data) < 64 or data[:2] != b"MZ":
        return False
    pe_offset = int.from_bytes(data[0x3C:0x40], "little")
    return data[pe_offset : pe_offset + 4] == b"PE\x00\x00"


def match_signature(data: bytes) -> Detection | None:
    """Reconnaît un format par ses premiers octets (« nombre magique »)."""
    for prefix, description, mime, extension in SIGNATURES:
        if data.startswith(prefix):
            return Detection(KIND_SIGNATURE, description, mime, extension)
    if _is_pe(data):
        return Detection(
            KIND_SIGNATURE,
            "Exécutable Windows (PE)",
            "application/vnd.microsoft.portable-executable",
            ".exe",
        )
    return None


def is_probably_text(data: bytes) -> bool:
    """Vrai si les octets forment du UTF-8 sans caractères de contrôle suspects."""
    decoder = codecs.getincrementaldecoder("utf-8")()
    try:
        text = decoder.decode(data, final=False)  # tolère une coupure en fin
    except UnicodeDecodeError:
        return False
    if "\x00" in text:
        return False
    controls = sum(1 for ch in text if ord(ch) < 32 and ch not in "\t\n\r\f")
    return controls / max(len(text), 1) < 0.05


def detect_content(data: bytes) -> Detection:
    """Devine la nature d'un contenu à partir de ses octets."""
    if not data:
        return Detection(KIND_EMPTY, "Contenu vide")
    signature = match_signature(data)
    if signature:
        return signature
    try:
        ascii_text = data.decode("ascii")
    except UnicodeDecodeError:
        ascii_text = None
    if ascii_text is not None:
        if is_valid_binary(ascii_text):
            return Detection(
                KIND_BINARY_TEXT, "Représentation binaire textuelle (0/1)", "text/plain", ".txt"
            )
        if len(ascii_text.strip()) >= 2 and is_valid_hex(ascii_text):
            return Detection(
                KIND_HEX_TEXT, "Représentation hexadécimale textuelle", "text/plain", ".hex"
            )
    if is_probably_text(data):
        return Detection(KIND_UTF8, "Texte UTF-8", "text/plain", ".txt")
    return Detection(KIND_BINARY, "Données binaires brutes", "application/octet-stream", ".bin")


def shannon_entropy(data: bytes) -> float:
    """Entropie de Shannon en bits par octet (0 à 8)."""
    if not data:
        return 0.0
    total = len(data)
    return -sum((c / total) * math.log2(c / total) for c in Counter(data).values())


def describe_entropy(value: float) -> str:
    if value < 1.0:
        return "Très faible (données très répétitives)"
    if value < 4.5:
        return "Faible (texte ou données structurées)"
    if value < 7.0:
        return "Moyenne (contenu mixte)"
    return "Élevée (données compressées ou chiffrées ?)"


def analyze(data: bytes) -> Analysis:
    """Statistiques simples : entropie, part d'ASCII imprimable, octets nuls…"""
    size = len(data)
    printable = len(data.translate(None, _NON_PRINTABLE))
    return Analysis(
        size=size,
        entropy=shannon_entropy(data),
        printable_ratio=(printable / size) if size else 0.0,
        null_bytes=data.count(0),
        unique_bytes=len(set(data)),
    )
