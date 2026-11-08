"""Moteur de conversion Texte <-> Binaire / Hexadécimal (UTF-8)."""

from __future__ import annotations

from utils.validators import ValidationError, clean_binary, clean_hex

ENCODING = "utf-8"
FORMAT_BINARY = "binary"
FORMAT_HEX = "hex"
SUPPORTED_FORMATS = (FORMAT_BINARY, FORMAT_HEX)

_BITS = tuple(format(i, "08b") for i in range(256))


class ConversionError(ValueError):
    """Levée lorsqu'une conversion est impossible."""


# --------------------------------------------------------------------------- #
# Texte <-> octets
# --------------------------------------------------------------------------- #
def text_to_bytes(text: str) -> bytes:
    """Encode un texte en UTF-8 (caractères spéciaux et Unicode inclus)."""
    if not text:
        raise ConversionError("Le texte à convertir est vide.")
    try:
        return text.encode(ENCODING)
    except UnicodeEncodeError as exc:
        raise ConversionError(f"Texte non encodable en UTF-8 : {exc.reason}.") from exc


def bytes_to_text(data: bytes) -> str:
    """Décode des octets en texte UTF-8."""
    if not data:
        raise ConversionError("Aucune donnée à décoder.")
    try:
        return data.decode(ENCODING)
    except UnicodeDecodeError as exc:
        raise ConversionError(
            f"Les octets ne forment pas du UTF-8 valide (octet n°{exc.start}, "
            f"0x{data[exc.start]:02x}). Ce contenu n'est probablement pas du texte."
        ) from exc


# --------------------------------------------------------------------------- #
# Octets -> représentation
# --------------------------------------------------------------------------- #
def _wrap(groups: list[str], separator: str, per_line: int) -> str:
    if per_line <= 0:
        return separator.join(groups)
    return "\n".join(
        separator.join(groups[i : i + per_line]) for i in range(0, len(groups), per_line)
    )


def bytes_to_hex(data: bytes, separator: str = "", bytes_per_line: int = 0) -> str:
    """Hexadécimal minuscule ; `bytes_per_line` > 0 découpe en lignes."""
    if not separator:
        flat = data.hex()
        if bytes_per_line <= 0:
            return flat
        step = bytes_per_line * 2
        return "\n".join(flat[i : i + step] for i in range(0, len(flat), step))
    return _wrap([f"{b:02x}" for b in data], separator, bytes_per_line)


def bytes_to_binary(data: bytes, separator: str = " ", bytes_per_line: int = 0) -> str:
    """Suite de groupes de 8 bits ; `bytes_per_line` > 0 découpe en lignes."""
    return _wrap([_BITS[b] for b in data], separator, bytes_per_line)


# --------------------------------------------------------------------------- #
# Représentation -> octets
# --------------------------------------------------------------------------- #
def hex_to_bytes(raw: str) -> bytes:
    """Décode de l'hexadécimal (espaces, retours ligne et préfixe 0x tolérés)."""
    try:
        return bytes.fromhex(clean_hex(raw))
    except ValidationError as exc:
        raise ConversionError(str(exc)) from exc


def binary_to_bytes(raw: str) -> bytes:
    """Décode une chaîne de bits (espaces et retours ligne tolérés)."""
    try:
        bits = clean_binary(raw)
    except ValidationError as exc:
        raise ConversionError(str(exc)) from exc
    return bytes(int(bits[i : i + 8], 2) for i in range(0, len(bits), 8))


# --------------------------------------------------------------------------- #
# Raccourcis texte
# --------------------------------------------------------------------------- #
def text_to_hex(text: str, separator: str = "", bytes_per_line: int = 0) -> str:
    return bytes_to_hex(text_to_bytes(text), separator, bytes_per_line)


def text_to_binary(text: str, separator: str = " ", bytes_per_line: int = 0) -> str:
    return bytes_to_binary(text_to_bytes(text), separator, bytes_per_line)


def hex_to_text(raw: str) -> str:
    return bytes_to_text(hex_to_bytes(raw))


def binary_to_text(raw: str) -> str:
    return bytes_to_text(binary_to_bytes(raw))


def encode_text(text: str, fmt: str, bytes_per_line: int = 0) -> str:
    """Texte -> représentation (`FORMAT_BINARY` ou `FORMAT_HEX`)."""
    if fmt == FORMAT_HEX:
        return text_to_hex(text, bytes_per_line=bytes_per_line)
    if fmt == FORMAT_BINARY:
        return text_to_binary(text, bytes_per_line=bytes_per_line)
    raise ConversionError(f"Format non pris en charge : {fmt!r}.")


def decode_representation(raw: str, fmt: str) -> bytes:
    """Représentation (`FORMAT_BINARY` ou `FORMAT_HEX`) -> octets."""
    if fmt == FORMAT_HEX:
        return hex_to_bytes(raw)
    if fmt == FORMAT_BINARY:
        return binary_to_bytes(raw)
    raise ConversionError(f"Format non pris en charge : {fmt!r}.")
