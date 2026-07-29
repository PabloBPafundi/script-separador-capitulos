"""Configuración central de la aplicación.

Modifica los valores de este archivo según el libro PDF que quieras procesar.
"""

import sys
from pathlib import Path

# Rutas del proyecto
# En modo PyInstaller --onefile, los archivos de trabajo deben quedar junto al
# ejecutable y no dentro de su directorio temporal de extracción.
BASE_DIR: Path = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)

# Carpeta que contiene uno o más PDFs a procesar.
INPUT_DIR: Path = BASE_DIR / "input"

# Patrón de archivos que se procesarán dentro de INPUT_DIR.
INPUT_GLOB: str = "*.pdf"

# Directorio donde se guardarán los capítulos generados.
OUTPUT_DIR: Path = BASE_DIR / "output"

# Crea una carpeta por libro dentro de OUTPUT_DIR. Ejemplo:
# output/prueba-marce/001 - CHAPTER I - ....pdf
CREATE_BOOK_OUTPUT_DIRECTORY: bool = True

# Directorio destinado a los archivos de log.
LOG_DIR: Path = BASE_DIR / "logs"

# Nombre del archivo principal de log.
LOG_FILE: Path = LOG_DIR / "pdf_chapter_splitter.log"

# Prefijo de los PDF generados.
# Ejemplo con INCLUDE_TITLE_IN_FILENAME=True: 001 - Introducción.pdf
# Ejemplo con INCLUDE_TITLE_IN_FILENAME=False: Capitulo_001.pdf
FILE_PREFIX: str = "Capitulo"

# Incluye el título del capítulo en el nombre de cada archivo.
INCLUDE_TITLE_IN_FILENAME: bool = True

# Cantidad de dígitos para numerar los capítulos. Con 3: 001, 002, 003...
CHAPTER_NUMBER_PADDING: int = 3

# Si el PDF contiene bookmarks/TOC, se usarán primero.
USE_TOC_FIRST: bool = True

# Nivel de bookmarks que se considerará como capítulo principal.
TOC_CHAPTER_LEVEL: int = 1

# Detecta encabezados del tipo "CHAPTER I" en PDFs con OCR. También reconoce
# variantes con letras espaciadas, por ejemplo "C HAPTER V".
USE_TYPOGRAPHIC_CHAPTER_DETECTION: bool = True

# Tamaño mínimo de fuente de las líneas que componen el título tras el marcador
# de capítulo. Ajústalo si el OCR de otro libro utiliza una tipografía menor.
CHAPTER_TITLE_MIN_FONT_SIZE: float = 12.0

# Máximo de líneas consecutivas que se unirán para construir el título completo.
CHAPTER_TITLE_MAX_LINES: int = 3

# Expresiones regulares de respaldo si el PDF no tiene TOC/bookmarks.
# Se evalúan sobre el texto de cada página, sin distinguir mayúsculas/minúsculas.
CHAPTER_REGEX_PATTERNS: list[str] = [
    r"^\s*cap[ií]tulo\s+\d+\b.*$",
    r"^\s*chapter\s+\d+\b.*$",
    r"^\s*[IVXLCDM]+\s*$",
    r"^\s*\d+\.\s+[A-ZÁÉÍÓÚÑ].*$",
]

# Cantidad máxima de caracteres por página que se examinan con regex.
# None analiza la página completa, útil para libros cuyos encabezados aparecen
# después de un bloque de texto. Usa un entero positivo para limitarlo.
REGEX_SCAN_CHARACTERS: int | None = None

# Sobrescribe PDFs de capítulo existentes con el mismo nombre. Está activado
# para permitir que los lanzadores de un clic vuelvan a procesar un libro.
OVERWRITE_EXISTING_FILES: bool = True

# Nivel de logging: DEBUG, INFO, WARNING, ERROR o CRITICAL.
LOG_LEVEL: str = "INFO"

# Codificación utilizada para archivos de texto auxiliares y logs.
TEXT_ENCODING: str = "utf-8"
