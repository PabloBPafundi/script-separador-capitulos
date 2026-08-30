"""Pruebas de la API que la GUI expone a React.

Cubren fallos que sólo se manifiestan del lado de la ventana: un job que nunca
llega a un estado final deja la interfaz poleando para siempre, y dos libros
que comparten carpeta de salida se pisan los capítulos sin avisar.
"""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

import pymupdf as fitz

from gui.backend.api import Api
from pdfsplitter.settings import PipelineSettings


def _write_book(path: Path, page_texts: tuple[str, ...] = ("Capitulo 1 Inicio",)) -> Path:
    with fitz.open() as document:
        for text in page_texts:
            document.new_page().insert_text((72, 72), text)
        document.save(path)
    return path


def _wait_until_finished(api: Api, job_id: str, timeout_seconds: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        status = api.get_job_status(job_id)
        if status["status"] != "running":
            return status
        time.sleep(0.02)
    raise AssertionError(f"El job quedó en 'running' más de {timeout_seconds}s.")


class JobTest(unittest.TestCase):
    def test_invalid_regex_fails_the_job_instead_of_hanging_it(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_path = Path(temporary_directory)
            source = _write_book(temp_path / "book.pdf")
            settings = PipelineSettings(
                use_toc_first=False,
                use_typographic_chapter_detection=False,
                chapter_regex_patterns=["Capitulo ("],
            )

            api = Api()
            job_id = api.start_job([str(source)], str(temp_path / "output"), settings.to_dict())
            status = _wait_until_finished(api, job_id)

            self.assertEqual(status["status"], "error")
            self.assertEqual(status["files"][0]["status"], "error")
            self.assertIn("no es válida", status["files"][0]["error"])

    def test_books_with_the_same_filename_get_separate_output_folders(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_path = Path(temporary_directory)
            first_dir = temp_path / "2024"
            second_dir = temp_path / "2025"
            first_dir.mkdir()
            second_dir.mkdir()
            first = _write_book(first_dir / "libro.pdf", ("Capitulo 1 Uno", "Capitulo 2 Dos"))
            second = _write_book(second_dir / "libro.pdf", ("Capitulo 1 Tres", "Capitulo 2 Cuatro"))
            output = temp_path / "output"

            api = Api()
            job_id = api.start_job(
                [str(first), str(second)],
                str(output),
                PipelineSettings(use_toc_first=False).to_dict(),
            )
            status = _wait_until_finished(api, job_id)

            self.assertEqual(status["status"], "done")
            output_dirs = [file["output_dir"] for file in status["files"]]
            self.assertNotEqual(output_dirs[0], output_dirs[1])
            self.assertEqual(sorted(p.name for p in output.iterdir()), ["libro", "libro (2)"])

    def test_forgets_the_oldest_jobs_instead_of_growing_without_limit(self) -> None:
        api = Api()
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp_path = Path(temporary_directory)
            source = _write_book(temp_path / "book.pdf")
            job_ids = [
                api.start_job([str(source)], str(temp_path / f"output-{index}"), PipelineSettings().to_dict())
                for index in range(25)
            ]
            for job_id in job_ids[-5:]:
                _wait_until_finished(api, job_id)

            self.assertEqual(api.get_job_status(job_ids[0])["status"], "unknown")
            self.assertNotEqual(api.get_job_status(job_ids[-1])["status"], "unknown")


class BookOutputDirTest(unittest.TestCase):
    def test_uses_the_custom_folder_name_only_for_a_single_book(self) -> None:
        base = Path("/salida")
        self.assertEqual(
            Api._book_output_dirs(base, ["/libros/a.pdf"], True, " Mi libro "),
            [base / "Mi libro"],
        )
        self.assertEqual(
            Api._book_output_dirs(base, ["/libros/a.pdf", "/libros/b.pdf"], True, "Mi libro"),
            [base / "a", base / "b"],
        )

    def test_shares_the_base_folder_when_grouping_is_disabled(self) -> None:
        base = Path("/salida")
        self.assertEqual(
            Api._book_output_dirs(base, ["/x/a.pdf", "/y/a.pdf"], False, ""),
            [base, base],
        )


if __name__ == "__main__":
    unittest.main()
