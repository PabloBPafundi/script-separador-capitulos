"""Punto de entrada de la aplicación PDF Chapter Splitter."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import config
from detector import detect_chapters
from extractor import PDFExtractionError, open_pdf
from splitter import SplitError, split_document
from utils import configure_logging


def main() -> int:
    """Procesa todos los PDFs de entrada y divide sus capítulos."""
    logger = configure_logging()
    input_files = _find_input_pdfs(config.INPUT_DIR)
    if not input_files:
        logger.error("No se encontraron PDFs en: %s", config.INPUT_DIR)
        return 2

    successful_books = 0
    failed_books = 0
    for input_pdf in input_files:
        if _process_pdf(input_pdf, logger):
            successful_books += 1
        else:
            failed_books += 1

    logger.info("Proceso finalizado. Libros correctos: %s; con errores: %s.", successful_books, failed_books)
    return 0 if failed_books == 0 else 1


def _find_input_pdfs(input_dir: Path) -> list[Path]:
    """Obtiene los PDFs de entrada ordenados para resultados reproducibles."""
    if not input_dir.is_dir():
        return []
    return sorted(path for path in input_dir.glob(config.INPUT_GLOB) if path.is_file())


def _get_book_output_dir(input_pdf: Path) -> Path:
    """Calcula la carpeta de salida asociada a un libro de entrada."""
    if config.CREATE_BOOK_OUTPUT_DIRECTORY:
        return config.OUTPUT_DIR / input_pdf.stem
    return config.OUTPUT_DIR


def _process_pdf(input_pdf: Path, logger: logging.Logger) -> bool:
    """Detecta y exporta los capítulos de un PDF individual."""
    output_dir = _get_book_output_dir(input_pdf)
    logger.info("Iniciando división del PDF: %s", input_pdf)
    try:
        with open_pdf(input_pdf) as document:
            chapters = detect_chapters(document)
            if not chapters:
                logger.error("No se detectaron capítulos en '%s'.", input_pdf.name)
                return False

            logger.info("Se detectaron %s capítulos en '%s'.", len(chapters), input_pdf.name)
            generated_files = split_document(document, chapters, logger, output_dir)
    except (PDFExtractionError, SplitError, OSError) as error:
        logger.error("No se pudo procesar '%s': %s", input_pdf.name, error)
        return False
    except Exception:
        logger.exception("Error inesperado al procesar '%s'.", input_pdf.name)
        return False

    logger.info("PDFs generados para '%s': %s", input_pdf.name, len(generated_files))
    for generated_file in generated_files:
        logger.info("  %s", generated_file)
    return True


if __name__ == "__main__":
    sys.exit(main())
