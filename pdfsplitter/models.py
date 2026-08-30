"""Modelos de datos compartidos por los filtros del pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Chapter:
    """Representa un capítulo mediante su título y páginas en base cero."""

    title: str
    start_page: int
    end_page: int

    def __post_init__(self) -> None:
        if self.start_page < 0 or self.end_page < self.start_page:
            raise ValueError("El rango de páginas del capítulo no es válido.")
