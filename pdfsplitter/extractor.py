"""Filtro que abre y valida el documento PDF (primer paso del pipeline)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pymupdf as fitz

if TYPE_CHECKING:
    from pdfsplitter.pipeline import PipelineData


class PDFExtractionError(RuntimeError):
    """Indica que un PDF no pudo abrirse o leerse correctamente."""


def open_pdf(pdf_path: Path) -> fitz.Document:
    """Abre y valida un PDF antes de procesarlo.

    El llamador es responsable de cerrar el documento mediante ``document.close()``
    o usando el documento como gestor de contexto.
    """
    if not pdf_path.is_file():
        raise PDFExtractionError(f"No se encontró el PDF de entrada: {pdf_path}")

    try:
        document = fitz.open(pdf_path)
    except (fitz.FileDataError, RuntimeError) as error:
        raise PDFExtractionError(f"No se pudo abrir el PDF: {error}") from error

    if document.page_count == 0:
        document.close()
        raise PDFExtractionError("El PDF no contiene páginas.")
    if document.needs_pass:
        document.close()
        raise PDFExtractionError("El PDF está protegido con contraseña.")
    return document


class OpenFilter:
    """Filtro: abre PipelineData.input_pdf y setea PipelineData.document."""

    name = "Apertura del PDF"

    def process(self, data: "PipelineData") -> "PipelineData":
        data.document = open_pdf(data.input_pdf)
        return data
