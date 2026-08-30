"""Filtro que genera un PDF por capítulo, preservando el contenido original."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pymupdf as fitz

from pdfsplitter.logging_utils import build_output_path
from pdfsplitter.models import Chapter
from pdfsplitter.settings import PipelineSettings

if TYPE_CHECKING:
    from pdfsplitter.pipeline import PipelineData


class SplitError(RuntimeError):
    """Indica un error durante la exportación de capítulos."""


def split_document(
    document: fitz.Document,
    chapters: list[Chapter],
    settings: PipelineSettings,
    output_dir: Path,
    on_chapter_exported=None,
) -> list[Path]:
    """Exporta cada capítulo en un PDF independiente con PyMuPDF."""
    if not chapters:
        raise SplitError("No se detectaron capítulos para dividir el documento.")

    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []
    total = len(chapters)

    for number, chapter in enumerate(chapters, start=1):
        destination = build_output_path(chapter, number, output_dir, settings)
        if destination.exists() and not settings.overwrite_existing_files:
            raise SplitError(
                f"El archivo ya existe: {destination}. "
                "Activa la opción de sobrescritura para reemplazarlo."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)

        try:
            with fitz.open() as output_document:
                output_document.insert_pdf(document, from_page=chapter.start_page, to_page=chapter.end_page)
                output_document.save(destination, garbage=4, deflate=True)
        except (fitz.FileDataError, RuntimeError, OSError) as error:
            raise SplitError(f"No se pudo crear '{destination.name}': {error}") from error
        generated_files.append(destination)
        if on_chapter_exported is not None:
            on_chapter_exported(number, total, chapter, destination)

    return generated_files


class SplitFilter:
    """Filtro: exporta PipelineData.chapters y setea PipelineData.generated_files."""

    name = "Exportación de capítulos"

    def process(self, data: "PipelineData") -> "PipelineData":
        data.generated_files = split_document(
            data.document, data.chapters, data.settings, data.output_dir
        )
        return data
