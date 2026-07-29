"""Utilidades y modelos compartidos por la aplicación."""

from __future__ import annotations

import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import config


@dataclass(frozen=True, slots=True)
class Chapter:
    """Representa un capítulo mediante su título y páginas en base cero."""

    title: str
    start_page: int
    end_page: int

    def __post_init__(self) -> None:
        if self.start_page < 0 or self.end_page < self.start_page:
            raise ValueError("El rango de páginas del capítulo no es válido.")


def configure_logging() -> logging.Logger:
    """Configura salida de log simultánea a consola y archivo."""
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_FILE, encoding=config.TEXT_ENCODING),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    return logging.getLogger("pdf_chapter_splitter")


def sanitize_filename(value: str, max_length: int = 120) -> str:
    """Devuelve un nombre de archivo seguro en Windows y Linux."""
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return (cleaned[:max_length].rstrip(" .") or "Sin_titulo")


def build_output_path(chapter: Chapter, number: int, output_dir: Path) -> Path:
    """Construye la ruta de salida para un capítulo."""
    padded_number = f"{number:0{config.CHAPTER_NUMBER_PADDING}d}"
    if config.INCLUDE_TITLE_IN_FILENAME:
        filename = f"{padded_number} - {sanitize_filename(chapter.title)}.pdf"
    else:
        filename = f"{config.FILE_PREFIX}_{padded_number}.pdf"
    return output_dir / filename
