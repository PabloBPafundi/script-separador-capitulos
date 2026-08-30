"""Configuración del modo consola: rutas y valores por defecto del pipeline.

Modifica los valores de este archivo según el libro PDF que quieras procesar.
"""

from __future__ import annotations

import sys
from pathlib import Path

from pdfsplitter.settings import PipelineSettings

# Rutas del proyecto
# En modo PyInstaller --onefile, los archivos de trabajo deben quedar junto al
# ejecutable y no dentro de su directorio temporal de extracción.
BASE_DIR: Path = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent.parent
)

# Carpeta que contiene uno o más PDFs a procesar.
INPUT_DIR: Path = BASE_DIR / "input"

# Extensión de los archivos que se procesarán dentro de INPUT_DIR. La
# comparación no distingue mayúsculas, igual que los lanzadores: así el CLI
# encuentra los mismos archivos que `ejecutar.sh` lista antes de confirmar.
INPUT_EXTENSION: str = ".pdf"

# Directorio donde se guardarán los capítulos generados.
OUTPUT_DIR: Path = BASE_DIR / "output"

# Crea una carpeta por libro dentro de OUTPUT_DIR. Ejemplo:
# output/prueba-marce/001 - CHAPTER I - ....pdf
CREATE_BOOK_OUTPUT_DIRECTORY: bool = True

# Directorio y archivo de logs.
LOG_DIR: Path = BASE_DIR / "logs"
LOG_FILE: Path = LOG_DIR / "pdf_chapter_splitter.log"
LOG_LEVEL: str = "INFO"
TEXT_ENCODING: str = "utf-8"


def default_settings() -> PipelineSettings:
    """Ajustes de detección/exportación para el modo consola.

    Ver pdfsplitter/settings.py para el significado de cada campo; los
    valores por defecto reproducen el comportamiento histórico del script.
    """
    return PipelineSettings()
