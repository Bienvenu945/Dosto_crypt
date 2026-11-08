"""Hex Viewer : offsets, octets en hexadécimal et représentation ASCII."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

DEFAULT_WIDTH = 16


def ascii_repr(chunk: bytes) -> str:
    """ASCII imprimable ; les autres octets sont affichés par un point."""
    return "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)


@dataclass(frozen=True)
class HexLine:
    offset: int
    data: bytes
    width: int = DEFAULT_WIDTH

    @property
    def hex(self) -> str:
        """Octets en hexadécimal, complétés pour garder l'alignement."""
        cells = [f"{b:02x}" for b in self.data] + ["  "] * (self.width - len(self.data))
        half = self.width // 2
        return " ".join(cells[:half]) + "  " + " ".join(cells[half:])

    @property
    def ascii(self) -> str:
        return ascii_repr(self.data)

    def __str__(self) -> str:
        return f"{self.offset:08x}  {self.hex}  |{self.ascii}|"


def iter_hexlines(
    data: bytes, start_offset: int = 0, width: int = DEFAULT_WIDTH
) -> Iterator[HexLine]:
    if width < 1:
        raise ValueError("La largeur doit être >= 1.")
    for i in range(0, len(data), width):
        yield HexLine(start_offset + i, data[i : i + width], width)


def format_hexdump(data: bytes, start_offset: int = 0, width: int = DEFAULT_WIDTH) -> str:
    return "\n".join(str(line) for line in iter_hexlines(data, start_offset, width))


def preview(data: bytes, count: int = 64, width: int = DEFAULT_WIDTH) -> list[HexLine]:
    """Aperçu des `count` premiers octets."""
    return list(iter_hexlines(data[:count], 0, width))
