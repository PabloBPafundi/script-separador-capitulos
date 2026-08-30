"""Punto de entrada de la aplicación PDF Chapter Splitter (modo consola)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

if __package__ in (None, ""):
    # Permite ejecutar `python cli/main.py` directamente además de `python -m cli.main`.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cli import config
from pdfsplitter.detector import ChapterDetectionError
from pdfsplitter.extractor import PDFExtractionError
from pdfsplitter.logging_utils import configure_logging
from pdfsplitter.pipeline import PipelineData, ProgressReporter, default_pipeline
from pdfsplitter.splitter import SplitError


class LoggerProgressReporter:
    """Reporta el avance del pipeline al logger de consola/archivo."""

    def __init__(self, logger: logging.Logger) -> None:
        self._logger = logger

    def stage(self, name: str) -> None:
        self._logger.info("-> %s", name)

    def log(self, level: str, message: str) -> None:
        getattr(self._logger, level.lower(), self._logger.info)(message)


def main() -> int:
    """Procesa todos los PDFs de entrada y divide sus capítulos."""
    logger = configure_logging(config.LOG_FILE, config.LOG_LEVEL, config.TEXT_ENCODING)
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
    extension = config.INPUT_EXTENSION.casefold()
    return sorted(
        path
        for path in input_dir.iterdir()
        if path.is_file() and path.suffix.casefold() == extension
    )


def _get_book_output_dir(input_pdf: Path) -> Path:
    """Calcula la carpeta de salida asociada a un libro de entrada."""
    if config.CREATE_BOOK_OUTPUT_DIRECTORY:
        return config.OUTPUT_DIR / input_pdf.stem
    return config.OUTPUT_DIR


def _process_pdf(input_pdf: Path, logger: logging.Logger) -> bool:
    """Detecta y exporta los capítulos de un PDF individual mediante el pipeline."""
    output_dir = _get_book_output_dir(input_pdf)
    logger.info("Iniciando división del PDF: %s", input_pdf)
    report: ProgressReporter = LoggerProgressReporter(logger)
    data = PipelineData(input_pdf=input_pdf, settings=config.default_settings(), output_dir=output_dir)
    try:
        data = default_pipeline().run(data, report)
        if not data.chapters:
            logger.error("No se detectaron capítulos en '%s'.", input_pdf.name)
            return False
    except (PDFExtractionError, ChapterDetectionError, SplitError, OSError) as error:
        logger.error("No se pudo procesar '%s': %s", input_pdf.name, error)
        return False
    except Exception:
        logger.exception("Error inesperado al procesar '%s'.", input_pdf.name)
        return False
    finally:
        data.close()

    logger.info("Se detectaron %s capítulos en '%s'.", len(data.chapters), input_pdf.name)
    logger.info("PDFs generados para '%s': %s", input_pdf.name, len(data.generated_files))
    for generated_file in data.generated_files:
        logger.info("  %s", generated_file)
    return True


if __name__ == "__main__":
    sys.exit(main())
