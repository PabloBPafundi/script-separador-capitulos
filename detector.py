"""Detección de capítulos por marcadores PDF o expresiones regulares."""

from __future__ import annotations

import re
from collections.abc import Sequence

import fitz

import config
from utils import Chapter

_CHAPTER_MARKER_PATTERN = re.compile(r"^CHAPTER([IVXLCDM]+)$")


def detect_chapters(document: fitz.Document) -> list[Chapter]:
    """Detecta capítulos priorizando el índice del PDF y luego las regex."""
    if config.USE_TOC_FIRST:
        chapters = detect_from_toc(document)
        if chapters:
            return chapters
    if config.USE_TYPOGRAPHIC_CHAPTER_DETECTION:
        chapters = detect_from_chapter_headers(document)
        if chapters:
            return chapters
    return detect_from_regex(document, config.CHAPTER_REGEX_PATTERNS)


def detect_from_toc(document: fitz.Document) -> list[Chapter]:
    """Extrae capítulos del TOC de PyMuPDF para el nivel configurado."""
    toc = document.get_toc(simple=True)
    entries = [entry for entry in toc if entry[0] == config.TOC_CHAPTER_LEVEL]
    if not entries:
        return []

    starts: list[tuple[str, int]] = []
    for _, title, page_number in entries:
        start_page = max(0, page_number - 1)  # El TOC usa páginas base uno.
        if start_page < document.page_count:
            starts.append((title.strip() or "Sin título", start_page))
    return _chapters_from_starts(starts, document.page_count)


def detect_from_regex(document: fitz.Document, patterns: Sequence[str]) -> list[Chapter]:
    """Busca títulos de capítulo en cada página usando las regex configuradas."""
    compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.MULTILINE) for pattern in patterns]
    starts: list[tuple[str, int]] = []
    for page_index, page in enumerate(document):
        text = page.get_text("text")
        if config.REGEX_SCAN_CHARACTERS is not None:
            text = text[: config.REGEX_SCAN_CHARACTERS]
        matches: list[tuple[int, str]] = []
        for pattern in compiled_patterns:
            for match in pattern.finditer(text):
                title = " ".join(match.group(0).split())
                matches.append((match.start(), title or f"Capítulo {len(starts) + 1}"))
        # Permite varios capítulos en una página y evita repetir una coincidencia
        # si dos expresiones regulares alcanzan el mismo título.
        seen_matches: set[tuple[int, str]] = set()
        for match in sorted(matches):
            if match not in seen_matches:
                starts.append((match[1], page_index))
                seen_matches.add(match)
    return _chapters_from_starts(starts, document.page_count)


def detect_from_chapter_headers(document: fitz.Document) -> list[Chapter]:
    """Detecta capítulos OCR por su marcador y la tipografía del título.

    Busca un marcador ``CHAPTER`` con número romano, incluso si el OCR espació
    las letras. Las líneas consecutivas en mayúsculas y de tamaño de título se
    combinan para obtener nombres como ``CHAPTER I - THE MYTH OF THE LEFT``.
    """
    starts: list[tuple[str, int]] = []
    for page_index, page in enumerate(document):
        lines = _extract_page_lines(page)
        for line_index, (_, _, marker_text) in enumerate(lines):
            compact_marker = re.sub(r"[^A-Z0-9]", "", marker_text.upper())
            marker_match = _CHAPTER_MARKER_PATTERN.fullmatch(compact_marker)
            if marker_match is None:
                continue

            chapter_label = f"CHAPTER {marker_match.group(1)}"
            title_lines = _extract_title_lines(lines, line_index + 1)
            title = " ".join(title_lines)
            full_title = f"{chapter_label} - {title}" if title else chapter_label
            starts.append((full_title, page_index))
    return _chapters_from_starts(starts, document.page_count)


def _extract_page_lines(page: fitz.Page) -> list[tuple[float, float, str]]:
    """Devuelve líneas OCR ordenadas por posición vertical y horizontal."""
    lines: list[tuple[float, float, float, str]] = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = " ".join(span["text"] for span in line["spans"]).strip()
            if text:
                max_font_size = max(span["size"] for span in line["spans"])
                x0, y0, _, _ = line["bbox"]
                lines.append((y0, x0, max_font_size, text))
    return [(y0, font_size, text) for y0, _, font_size, text in sorted(lines)]


def _extract_title_lines(
    lines: Sequence[tuple[float, float, str]], start_index: int
) -> list[str]:
    """Recupera las líneas tipográficas que componen el título del capítulo."""
    title_lines: list[str] = []
    for _, font_size, text in lines[start_index : start_index + config.CHAPTER_TITLE_MAX_LINES]:
        normalized = " ".join(text.split())
        is_uppercase_heading = len(normalized) > 1 and normalized.upper() == normalized
        if font_size < config.CHAPTER_TITLE_MIN_FONT_SIZE or not is_uppercase_heading:
            break
        title_lines.append(normalized)
    return title_lines


def _chapters_from_starts(starts: Sequence[tuple[str, int]], page_count: int) -> list[Chapter]:
    """Convierte páginas iniciales en rangos de capítulos.

    Si dos títulos comienzan en la misma página, esa página se incluye en ambos
    PDFs. Es la única forma de conservar el PDF original sin recortar contenido.
    """
    chapters: list[Chapter] = []
    for index, (title, start_page) in enumerate(starts):
        is_last = index == len(starts) - 1
        next_page = page_count if is_last else starts[index + 1][1]
        # Los PDF solo se pueden dividir por páginas. Dos inicios en la misma
        # página requieren compartirla entre los capítulos consecutivos.
        end_page = start_page if next_page == start_page else next_page - 1
        chapters.append(Chapter(title=title, start_page=start_page, end_page=end_page))
    return chapters
