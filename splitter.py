"""Generación de un PDF por capítulo, preservando el contenido original."""

from __future__ import annotations

import logging
from pathlib import Path

import fitz

import config
from utils import Chapter, build_output_path


class SplitError(RuntimeError):
    """Indica un error durante la exportación de capítulos."""


def split_document(
    document: fitz.Document,
    chapters: list[Chapter],
    logger: logging.Logger,
    output_dir: Path,
) -> list[Path]:
    """Exporta cada capítulo en un PDF independiente con PyMuPDF."""
    if not chapters:
        raise SplitError("No se detectaron capítulos para dividir el documento.")

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []
    total = len(chapters)

    for number, chapter in enumerate(chapters, start=1):
        destination = build_output_path(chapter, number, output_dir)
        if destination.exists() and not config.OVERWRITE_EXISTING_FILES:
            raise SplitError(
                f"El archivo ya existe: {destination}. "
                "Activa OVERWRITE_EXISTING_FILES en config.py para reemplazarlo."
            )

        logger.info("[%s/%s] Exportando: %s", number, total, chapter.title)
        try:
            with fitz.open() as output_document:
                output_document.insert_pdf(document, from_page=chapter.start_page, to_page=chapter.end_page)
                output_document.save(destination, garbage=4, deflate=True)
        except (fitz.FileDataError, RuntimeError, OSError) as error:
            raise SplitError(f"No se pudo crear '{destination.name}': {error}") from error
        generated_files.append(destination)

    return generated_files
