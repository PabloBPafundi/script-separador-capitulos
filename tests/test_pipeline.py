"""Pruebas del orquestador Pipes and Filters."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz

from pdfsplitter.extractor import PDFExtractionError
from pdfsplitter.pipeline import Pipeline, PipelineData, default_pipeline
from pdfsplitter.settings import PipelineSettings


class RecordingProgressReporter:
    def __init__(self) -> None:
        self.stages: list[str] = []

    def stage(self, name: str) -> None:
        self.stages.append(name)

    def log(self, level: str, message: str) -> None:
        pass


class PipelineTest(unittest.TestCase):
    def test_runs_filters_in_order_and_reports_each_stage(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_path = Path(temporary_directory)
            source = temp_path / "book.pdf"
            with fitz.open() as document:
                document.new_page()
                page = document.new_page()
                page.insert_text((72, 72), "Chapter Two")
                document.set_toc([[1, "First chapter", 1], [1, "Second chapter", 2]])
                document.save(source)

            data = PipelineData(
                input_pdf=source, settings=PipelineSettings(), output_dir=temp_path / "output"
            )
            report = RecordingProgressReporter()
            try:
                result = default_pipeline().run(data, report)
                self.assertEqual(len(result.chapters), 2)
                self.assertEqual(len(result.generated_files), 2)
            finally:
                data.close()

            self.assertEqual(
                report.stages,
                ["Apertura del PDF", "Detección de capítulos", "Exportación de capítulos"],
            )

    def test_propagates_open_errors_from_the_first_filter(self) -> None:
        data = PipelineData(
            input_pdf=Path("no-existe.pdf"), settings=PipelineSettings(), output_dir=Path(".")
        )
        with self.assertRaises(PDFExtractionError):
            default_pipeline().run(data)

    def test_filters_are_independently_testable(self) -> None:
        from pdfsplitter.detector import DetectFilter

        with tempfile.TemporaryDirectory() as temporary_directory:
            source = Path(temporary_directory) / "book.pdf"
            with fitz.open() as document:
                document.new_page()
                document.set_toc([[1, "Only chapter", 1]])
                document.save(source)

            with fitz.open(source) as document:
                data = PipelineData(input_pdf=source, settings=PipelineSettings(), output_dir=Path("."))
                data.document = document
                result = DetectFilter().process(data)
                self.assertEqual(len(result.chapters), 1)


if __name__ == "__main__":
    unittest.main()
