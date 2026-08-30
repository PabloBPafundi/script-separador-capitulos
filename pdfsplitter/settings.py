"""Ajustes explícitos del pipeline (reemplaza el módulo global config.py).

Cada campo corresponde a una opción que antes vivía como constante global en
config.py. Viajan dentro de PipelineData en vez de leerse de un módulo, para
que la GUI pueda variarlos por corrida sin mutar estado compartido.
"""

from __future__ import annotations

from dataclasses import dataclass, field


def _default_regex_patterns() -> list[str]:
    """Patrones de respaldo. `(?i)` marca los que ignoran mayúsculas.

    Los dos últimos dependen de que el texto esté en mayúsculas para no
    confundir prosa con títulos ("mi", "civil" o "1. hola" no son capítulos),
    así que deben compilarse distinguiendo mayúsculas de minúsculas.
    """
    return [
        r"(?i)^\s*cap[ií]tulo\s+\d+\b.*$",
        r"(?i)^\s*chapter\s+\d+\b.*$",
        r"^\s*[IVXLCDM]+\s*$",
        r"^\s*\d+\.\s+[A-ZÁÉÍÓÚÑ].*$",
    ]


@dataclass(slots=True)
class PipelineSettings:
    """Opciones de detección y exportación de capítulos."""

    # Nombre de archivos generados.
    file_prefix: str = "Capitulo"
    include_title_in_filename: bool = True
    chapter_number_padding: int = 3

    # Detección por TOC/bookmarks.
    use_toc_first: bool = True
    toc_chapter_level: int = 1

    # Detección tipográfica de encabezados OCR ("CHAPTER I").
    use_typographic_chapter_detection: bool = True
    chapter_title_min_font_size: float = 12.0
    chapter_title_max_lines: int = 3

    # Detección por expresiones regulares (respaldo).
    chapter_regex_patterns: list[str] = field(default_factory=_default_regex_patterns)
    regex_scan_characters: int | None = None

    # Exportación.
    overwrite_existing_files: bool = True
    separate_folder_per_chapter: bool = False

    def to_dict(self) -> dict:
        return {
            "file_prefix": self.file_prefix,
            "include_title_in_filename": self.include_title_in_filename,
            "chapter_number_padding": self.chapter_number_padding,
            "use_toc_first": self.use_toc_first,
            "toc_chapter_level": self.toc_chapter_level,
            "use_typographic_chapter_detection": self.use_typographic_chapter_detection,
            "chapter_title_min_font_size": self.chapter_title_min_font_size,
            "chapter_title_max_lines": self.chapter_title_max_lines,
            "chapter_regex_patterns": list(self.chapter_regex_patterns),
            "regex_scan_characters": self.regex_scan_characters,
            "overwrite_existing_files": self.overwrite_existing_files,
            "separate_folder_per_chapter": self.separate_folder_per_chapter,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineSettings":
        defaults = cls()
        return cls(
            file_prefix=data.get("file_prefix", defaults.file_prefix),
            include_title_in_filename=data.get(
                "include_title_in_filename", defaults.include_title_in_filename
            ),
            chapter_number_padding=data.get(
                "chapter_number_padding", defaults.chapter_number_padding
            ),
            use_toc_first=data.get("use_toc_first", defaults.use_toc_first),
            toc_chapter_level=data.get("toc_chapter_level", defaults.toc_chapter_level),
            use_typographic_chapter_detection=data.get(
                "use_typographic_chapter_detection",
                defaults.use_typographic_chapter_detection,
            ),
            chapter_title_min_font_size=data.get(
                "chapter_title_min_font_size", defaults.chapter_title_min_font_size
            ),
            chapter_title_max_lines=data.get(
                "chapter_title_max_lines", defaults.chapter_title_max_lines
            ),
            chapter_regex_patterns=list(
                data.get("chapter_regex_patterns", defaults.chapter_regex_patterns)
            ),
            regex_scan_characters=data.get(
                "regex_scan_characters", defaults.regex_scan_characters
            ),
            overwrite_existing_files=data.get(
                "overwrite_existing_files", defaults.overwrite_existing_files
            ),
            separate_folder_per_chapter=data.get(
                "separate_folder_per_chapter", defaults.separate_folder_per_chapter
            ),
        )
