"""Prueba de integración para detección por TOC y división de PDF."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import fitz

import config
from detector import detect_chapters
from extractor import open_pdf
from splitter import split_document
from utils import configure_logging


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

            original_output = config.OUTPUT_DIR
            original_overwrite = config.OVERWRITE_EXISTING_FILES
            config.OUTPUT_DIR = output
            config.OVERWRITE_EXISTING_FILES = False
            try:
                with open_pdf(source) as document:
                    chapters = detect_chapters(document)
                    files = split_document(document, chapters, configure_logging(), output)
            finally:
                config.OUTPUT_DIR = original_output
                config.OVERWRITE_EXISTING_FILES = original_overwrite

            self.assertEqual([chapter.start_page for chapter in chapters], [0, 2])
            self.assertEqual([chapter.end_page for chapter in chapters], [1, 2])
            self.assertEqual(len(files), 2)
            with fitz.open(files[0]) as first_chapter, fitz.open(files[1]) as second_chapter:
                self.assertEqual(first_chapter.page_count, 2)
                self.assertEqual(second_chapter.page_count, 1)

    def test_detects_chapters_using_regex_without_toc(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "book.pdf"
            with fitz.open() as document:
                for text in ("Capítulo 1 Inicio", "Contenido", "Capítulo 2 Final"):
                    page = document.new_page()
                    page.insert_text((72, 72), text)
                document.save(source)

            original_toc_preference = config.USE_TOC_FIRST
            config.USE_TOC_FIRST = False
            try:
                with open_pdf(source) as document:
                    chapters = detect_chapters(document)
            finally:
                config.USE_TOC_FIRST = original_toc_preference

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

            original_toc_preference = config.USE_TOC_FIRST
            config.USE_TOC_FIRST = False
            try:
                with open_pdf(source) as document:
                    chapters = detect_chapters(document)
            finally:
                config.USE_TOC_FIRST = original_toc_preference

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

            original_toc_preference = config.USE_TOC_FIRST
            config.USE_TOC_FIRST = False
            try:
                with open_pdf(source) as document:
                    chapters = detect_chapters(document)
            finally:
                config.USE_TOC_FIRST = original_toc_preference

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

            original_toc_preference = config.USE_TOC_FIRST
            config.USE_TOC_FIRST = False
            try:
                with open_pdf(source) as document:
                    chapters = detect_chapters(document)
            finally:
                config.USE_TOC_FIRST = original_toc_preference

            self.assertEqual(chapters[0].title, "CHAPTER V - THE MEANING OF HISTORY")


if __name__ == "__main__":
    unittest.main()
