"""Utilidades de logging y nombres de archivo compartidas por CLI y GUI."""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

from pdfsplitter.models import Chapter
from pdfsplitter.settings import PipelineSettings


def configure_logging(log_file: Path, log_level: str = "INFO", encoding: str = "utf-8") -> logging.Logger:
    """Configura salida de log simultánea a consola y archivo."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding=encoding),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )
    return logging.getLogger("pdf_chapter_splitter")


def sanitize_filename(value: str, max_length: int = 120, fallback: str = "Sin_titulo") -> str:
    """Devuelve un nombre de archivo seguro en Windows y Linux.

    Al reemplazar los separadores de ruta y descartar puntos iniciales, el
    resultado siempre es un único componente de nombre: nada de lo que escriba
    el usuario puede escribir fuera de la carpeta de salida elegida.
    """
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', " ", value)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned[:max_length].rstrip(" .") or fallback


def build_output_path(
    chapter: Chapter, number: int, output_dir: Path, settings: PipelineSettings
) -> Path:
    """Construye la ruta de salida para un capítulo."""
    padded_number = f"{number:0{settings.chapter_number_padding}d}"
    if settings.include_title_in_filename:
        stem = f"{padded_number} - {sanitize_filename(chapter.title)}"
    else:
        prefix = sanitize_filename(settings.file_prefix, max_length=60, fallback="Capitulo")
        stem = f"{prefix}_{padded_number}"
    if settings.separate_folder_per_chapter:
        return output_dir / stem / f"{stem}.pdf"
    return output_dir / f"{stem}.pdf"
