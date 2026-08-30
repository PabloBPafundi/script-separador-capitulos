"""Pruebas del modo consola y de la auto-actualización.

Ambos cruzan la frontera con el sistema operativo, donde vive lo que más
fácilmente se rompe según la máquina: mayúsculas en los nombres de archivo y
sistemas de archivos distintos entre la descarga y el ejecutable.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from cli.main import _find_input_pdfs
from pdfsplitter.updater import ReleaseAsset, UpdateError, staging_path


class FindInputPdfsTest(unittest.TestCase):
    def test_finds_pdfs_whatever_the_case_of_the_extension(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_dir = Path(temporary_directory)
            for name in ("a.pdf", "b.PDF", "c.Pdf", "notas.txt"):
                (input_dir / name).touch()

            found = _find_input_pdfs(input_dir)

            self.assertEqual([path.name for path in found], ["a.pdf", "b.PDF", "c.Pdf"])

    def test_ignores_directories_that_look_like_pdfs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            input_dir = Path(temporary_directory)
            (input_dir / "carpeta.pdf").mkdir()

            self.assertEqual(_find_input_pdfs(input_dir), [])

    def test_returns_nothing_when_the_input_folder_is_missing(self) -> None:
        self.assertEqual(_find_input_pdfs(Path("/no/existe")), [])


class StagingPathTest(unittest.TestCase):
    """`os.replace` falla con EXDEV entre sistemas de archivos distintos.

    Descargar junto al ejecutable (y no en /tmp, que suele ser un tmpfs aparte)
    es lo que mantiene el reemplazo en un único sistema de archivos.
    """

    ASSET = ReleaseAsset(name="app-linux", download_url="https://example/app", size=1)

    def test_downloads_next_to_the_executable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            executable = Path(temporary_directory) / "pdf-chapter-splitter-gui"
            with mock.patch("pdfsplitter.updater.current_executable", return_value=executable):
                destination = staging_path(self.ASSET)

            self.assertEqual(destination.parent, executable.parent)

    def test_explains_the_problem_when_the_install_folder_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            executable = Path(temporary_directory) / "pdf-chapter-splitter-gui"
            with mock.patch("pdfsplitter.updater.current_executable", return_value=executable):
                with mock.patch("pdfsplitter.updater.os.access", return_value=False):
                    with self.assertRaises(UpdateError) as raised:
                        staging_path(self.ASSET)

            self.assertIn("Reinstalá", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
