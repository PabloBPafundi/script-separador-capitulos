"""Prueba de integración para detección por TOC y división de PDF."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz

from pdfsplitter.detector import ChapterDetectionError, detect_chapters
from pdfsplitter.extractor import open_pdf
from pdfsplitter.logging_utils import build_output_path
from pdfsplitter.models import Chapter
from pdfsplitter.settings import PipelineSettings
from pdfsplitter.splitter import split_document


class PDFSplitterIntegrationTest(unittest.TestCase):
    """Verifica que se conserven los rangos de cada capítulo."""

    def test_splits_pdf_using_toc(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_path = Path(temporary_directory)
            source = temp_path / "book.pdf"
            output = temp_path / "output"

            with fitz.open() as document:
                for text in ("Chapter One", "Content One", "Chapter Two"):
                    page = document.new_page()
                    page.insert_text((72, 72), text)
                document.set_toc([[1, "First chapter", 1], [1, "Second chapter", 3]])
                document.save(source)

            settings = PipelineSettings(overwrite_existing_files=False)
            with open_pdf(source) as document:
                chapters = detect_chapters(document, settings)
                files = split_document(document, chapters, settings, output)

            self.assertEqual([chapter.start_page for chapter in chapters], [0, 2])
            self.assertEqual([chapter.end_page for chapter in chapters], [1, 2])
            self.assertEqual(len(files), 2)
            with fitz.open(files[0]) as first_chapter, fitz.open(files[1]) as second_chapter:
                self.assertEqual(first_chapter.page_count, 2)
                self.assertEqual(second_chapter.page_count, 1)

    def test_splits_into_one_folder_per_chapter_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_path = Path(temporary_directory)
            source = temp_path / "book.pdf"
            output = temp_path / "output"

            with fitz.open() as document:
                for text in ("Chapter One", "Chapter Two"):
                    page = document.new_page()
                    page.insert_text((72, 72), text)
                document.set_toc([[1, "First chapter", 1], [1, "Second chapter", 2]])
                document.save(source)

            settings = PipelineSettings(separate_folder_per_chapter=True)
            with open_pdf(source) as document:
                chapters = detect_chapters(document, settings)
                files = split_document(document, chapters, settings, output)

            self.assertEqual(len(files), 2)
            for generated_file in files:
                self.assertEqual(generated_file.parent.parent, output)
                self.assertEqual(generated_file.parent.name, generated_file.stem)

    def test_detects_chapters_using_regex_without_toc(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "book.pdf"
            with fitz.open() as document:
                for text in ("Capítulo 1 Inicio", "Contenido", "Capítulo 2 Final"):
                    page = document.new_page()
                    page.insert_text((72, 72), text)
                document.save(source)

            settings = PipelineSettings(use_toc_first=False)
            with open_pdf(source) as document:
                chapters = detect_chapters(document, settings)

            self.assertEqual(len(chapters), 2)
            self.assertEqual([chapter.start_page for chapter in chapters], [0, 2])

    def test_detects_roman_numeral_chapters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "book.pdf"
            with fitz.open() as document:
                for text in ("Prólogo\n\nI", "Contenido\n\nII"):
                    page = document.new_page()
                    page.insert_text((72, 72), text)
                document.save(source)

            settings = PipelineSettings(use_toc_first=False)
            with open_pdf(source) as document:
                chapters = detect_chapters(document, settings)

            self.assertEqual([chapter.title for chapter in chapters], ["I", "II"])

    def test_keeps_two_chapters_that_start_on_the_same_page(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "book.pdf"
            with fitz.open() as document:
                page = document.new_page()
                page.insert_text((72, 72), "I")
                page.insert_text((72, 100), "Contenido")
                page.insert_text((72, 128), "II")
                document.new_page()
                document.save(source)

            settings = PipelineSettings(use_toc_first=False)
            with open_pdf(source) as document:
                chapters = detect_chapters(document, settings)

            self.assertEqual([chapter.title for chapter in chapters], ["I", "II"])
            self.assertEqual([(chapter.start_page, chapter.end_page) for chapter in chapters], [(0, 0), (0, 1)])

    def test_builds_complete_title_from_ocr_chapter_header(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "book.pdf"
            with fitz.open() as document:
                page = document.new_page()
                page.insert_text((72, 72), "C HAPTER V", fontsize=11)
                page.insert_text((72, 100), "THE MEANING OF HISTORY", fontsize=16)
                page.insert_text((72, 140), "Beginning of the body text.", fontsize=9)
                document.new_page()
                document.save(source)

            settings = PipelineSettings(use_toc_first=False)
            with open_pdf(source) as document:
                chapters = detect_chapters(document, settings)

            self.assertEqual(chapters[0].title, "CHAPTER V - THE MEANING OF HISTORY")


class ChapterDetectionSettingsTest(unittest.TestCase):
    """Ajustes que el usuario puede escribir a mano desde la GUI."""

    def _book(self, directory: Path, *page_texts: str) -> Path:
        source = directory / "book.pdf"
        with fitz.open() as document:
            for text in page_texts:
                document.new_page().insert_text((72, 72), text)
            document.save(source)
        return source

    def _regex_settings(self, patterns: list[str]) -> PipelineSettings:
        return PipelineSettings(
            use_toc_first=False,
            use_typographic_chapter_detection=False,
            chapter_regex_patterns=patterns,
        )

    def test_ignores_blank_patterns_left_by_a_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = self._book(Path(temporary_directory), "Capítulo 1 Inicio", "Prosa", "Más prosa")
            settings = self._regex_settings([r"(?i)^\s*cap[ií]tulo\s+\d+\b.*$", ""])

            with open_pdf(source) as document:
                chapters = detect_chapters(document, settings)

            self.assertEqual([chapter.title for chapter in chapters], ["Capítulo 1 Inicio"])

    def test_reports_an_invalid_pattern_with_its_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = self._book(Path(temporary_directory), "Capítulo 1 Inicio")

            with open_pdf(source) as document:
                with self.assertRaises(ChapterDetectionError) as raised:
                    detect_chapters(document, self._regex_settings(["Capitulo ("]))

            self.assertIn("Capitulo (", str(raised.exception))

    def test_default_patterns_do_not_take_lowercase_prose_as_a_title(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = self._book(
                Path(temporary_directory), "1. hola minuscula", "CAPÍTULO 2 EN MAYÚSCULAS"
            )
            settings = PipelineSettings(use_toc_first=False, use_typographic_chapter_detection=False)

            with open_pdf(source) as document:
                chapters = detect_chapters(document, settings)

            self.assertEqual([chapter.title for chapter in chapters], ["CAPÍTULO 2 EN MAYÚSCULAS"])


class OutputPathTest(unittest.TestCase):
    def test_file_prefix_cannot_escape_the_chosen_output_folder(self) -> None:
        chapter = Chapter(title="Cap uno", start_page=0, end_page=1)
        settings = PipelineSettings(
            include_title_in_filename=False, file_prefix="../../otra-carpeta/Cap"
        )
        output_dir = Path("/salida/elegida")

        destination = build_output_path(chapter, 1, output_dir, settings)

        self.assertEqual(destination.parent, output_dir)

    def test_chapter_title_cannot_escape_the_chosen_output_folder(self) -> None:
        chapter = Chapter(title="../../otra-carpeta/Cap", start_page=0, end_page=1)
        output_dir = Path("/salida/elegida")

        destination = build_output_path(chapter, 1, output_dir, PipelineSettings())

        self.assertEqual(destination.parent, output_dir)

    def test_falls_back_to_a_usable_prefix_when_the_user_clears_it(self) -> None:
        chapter = Chapter(title="Cap uno", start_page=0, end_page=1)
        settings = PipelineSettings(include_title_in_filename=False, file_prefix="")

        destination = build_output_path(chapter, 1, Path("/salida"), settings)

        self.assertEqual(destination.name, "Capitulo_001.pdf")


if __name__ == "__main__":
    unittest.main()
