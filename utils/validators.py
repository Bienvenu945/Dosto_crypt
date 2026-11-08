"""Validation des saisies utilisateur : données, noms de fichiers, nombres."""

from __future__ import annotations

from pathlib import Path

BINARY_CHARS = frozenset("01")
HEX_CHARS = frozenset("0123456789abcdefABCDEF")
FORBIDDEN_FILENAME_CHARS = frozenset('<>:"/\\|?*\x00')


class ValidationError(ValueError):
    """Levée lorsqu'une saisie ne respecte pas le format attendu."""


def strip_whitespace(raw: str) -> str:
    """Supprime espaces, tabulations et retours à la ligne."""
    return "".join(raw.split())


def _preview_chars(chars, limit: int = 5) -> str:
    ordered = sorted(chars)
    shown = ", ".join(repr(c) for c in ordered[:limit])
    return shown + (", …" if len(ordered) > limit else "")


def clean_binary(raw: str) -> str:
    """Retourne la chaîne de bits nettoyée ou lève ValidationError."""
    cleaned = strip_whitespace(raw)
    if not cleaned:
        raise ValidationError("Aucune donnée binaire n'a été fournie.")
    invalid = set(cleaned) - BINARY_CHARS
    if invalid:
        raise ValidationError(
            "Caractères invalides pour du binaire (seuls 0 et 1 sont admis) : "
            f"{_preview_chars(invalid)}."
        )
    if len(cleaned) % 8:
        raise ValidationError(
            f"Le binaire doit contenir un multiple de 8 bits ({len(cleaned)} reçus)."
        )
    return cleaned


def clean_hex(raw: str) -> str:
    """Retourne l'hexadécimal nettoyé (minuscules, sans espaces ni « 0x »)."""
    cleaned = strip_whitespace(raw)
    if cleaned[:2].lower() == "0x":
        cleaned = cleaned[2:]
    if not cleaned:
        raise ValidationError("Aucune donnée hexadécimale n'a été fournie.")
    invalid = set(cleaned) - HEX_CHARS
    if invalid:
        raise ValidationError(
            "Caractères invalides pour de l'hexadécimal (0-9, a-f) : "
            f"{_preview_chars(invalid)}."
        )
    if len(cleaned) % 2:
        raise ValidationError(
            "L'hexadécimal doit contenir un nombre pair de chiffres "
            f"({len(cleaned)} reçus)."
        )
    return cleaned.lower()


def is_valid_binary(raw: str) -> bool:
    try:
        clean_binary(raw)
    except ValidationError:
        return False
    return True


def is_valid_hex(raw: str) -> bool:
    try:
        clean_hex(raw)
    except ValidationError:
        return False
    return True


def validate_filename(name: str, default_extension: str = "") -> str:
    """Valide un nom de fichier (sans dossier) et ajoute l'extension si absente."""
    name = name.strip()
    if not name or name in {".", ".."}:
        raise ValidationError("Le nom de fichier est vide ou invalide.")
    invalid = FORBIDDEN_FILENAME_CHARS & set(name)
    if invalid:
        raise ValidationError(
            f"Le nom contient des caractères interdits : {_preview_chars(invalid)}."
        )
    if default_extension and not Path(name).suffix:
        name += default_extension
    return name


def parse_int(raw: str, minimum: int = 0, maximum: int | None = None) -> int:
    """Convertit une saisie (« 128 » ou « 0x80 ») en entier borné."""
    text = raw.strip().lower().replace("_", "")
    try:
        value = int(text, 0)
    except ValueError:
        try:
            value = int(text, 10)
        except ValueError:
            raise ValidationError(
                f"« {raw.strip()} » n'est pas un entier valide (ex. 128 ou 0x80)."
            ) from None
    if value < minimum or (maximum is not None and value > maximum):
        upper = "∞" if maximum is None else str(maximum)
        raise ValidationError(f"La valeur doit être comprise entre {minimum} et {upper}.")
    return value
