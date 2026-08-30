"""API Python expuesta a React vía el puente JS de pywebview."""

from __future__ import annotations

import json
import os
import sys
import threading
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import webview

from pdfsplitter.detector import ChapterDetectionError
from pdfsplitter.extractor import PDFExtractionError
from pdfsplitter.logging_utils import sanitize_filename
from pdfsplitter.models import Chapter
from pdfsplitter.pipeline import PipelineData, default_pipeline, detect_pipeline, export_pipeline
from pdfsplitter.settings import PipelineSettings
from pdfsplitter.splitter import SplitError
from pdfsplitter.updater import ReleaseInfo, UpdateError
from pdfsplitter.updater import apply_update as perform_update
from pdfsplitter.updater import (
    check_latest_release,
    current_version,
    download_asset,
    is_newer,
    pick_asset,
    staging_path,
)


# Errores de pipeline con un mensaje entendible para el usuario final.
_PIPELINE_ERRORS = (PDFExtractionError, ChapterDetectionError, SplitError, OSError)

# Los jobs terminados se conservan sólo para que la UI lea su resultado final.
_MAX_STORED_JOBS = 20


def _settings_dir() -> Path:
    """Carpeta de configuración del usuario, según el sistema operativo."""
    if sys.platform.startswith("win"):
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "pdf-chapter-splitter"


def _settings_file() -> Path:
    return _settings_dir() / "gui-settings.json"


@dataclass
class _FileStatus:
    path: str
    name: str
    status: str = "pending"  # pending | running | done | error
    chapters: int = 0
    output_dir: str = ""
    error: str | None = None


@dataclass
class _Job:
    status: str = "running"  # running | done | error
    files: list[_FileStatus] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)


@dataclass
class _PreviewFileStatus:
    name: str
    status: str = "pending"  # pending | running | done | error
    chapters: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None


@dataclass
class _PreviewJob:
    status: str = "running"  # running | done | error
    files: list[_PreviewFileStatus] = field(default_factory=list)


class JobProgressReporter:
    """Vuelca el avance del pipeline al log en memoria del job."""

    def __init__(self, job: _Job) -> None:
        self._job = job

    def stage(self, name: str) -> None:
        self._job.logs.append(name)

    def log(self, level: str, message: str) -> None:
        self._job.logs.append(f"[{level.upper()}] {message}")


class Api:
    """Superficie llamada desde React vía `window.pywebview.api.*`."""

    def __init__(self) -> None:
        self._jobs: dict[str, _Job] = {}
        self._previews: dict[str, _PreviewJob] = {}

    @staticmethod
    def _remember(store: dict[str, Any], job_id: str, job: Any) -> None:
        """Registra un job descartando los más viejos, que ya nadie consulta."""
        store[job_id] = job
        while len(store) > _MAX_STORED_JOBS:
            del store[next(iter(store))]

    def pick_pdfs(self) -> list[str]:
        window = webview.windows[0]
        result = window.create_file_dialog(
            webview.FileDialog.OPEN,
            allow_multiple=True,
            file_types=("Archivos PDF (*.pdf)", "Todos los archivos (*.*)"),
        )
        return list(result) if result else []

    def pick_output_dir(self) -> str | None:
        window = webview.windows[0]
        result = window.create_file_dialog(webview.FileDialog.FOLDER)
        return result[0] if result else None

    def get_default_settings(self) -> dict[str, Any]:
        """Ajustes con los que arranca la app: los guardados, o los de fábrica."""
        saved = self._load_saved_settings()
        return saved if saved is not None else PipelineSettings().to_dict()

    def get_factory_defaults(self) -> dict[str, Any]:
        """Ajustes de fábrica, ignorando lo guardado (para el botón "Restaurar")."""
        return PipelineSettings().to_dict()

    def save_settings(self, settings: dict[str, Any]) -> None:
        """Persiste los ajustes en disco para la próxima vez que se abra la app."""
        normalized = PipelineSettings.from_dict(settings).to_dict()
        try:
            path = _settings_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass  # No es crítico: la corrida sigue con los ajustes en memoria.

    def _load_saved_settings(self) -> dict[str, Any] | None:
        try:
            path = _settings_file()
            if not path.is_file():
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            return PipelineSettings.from_dict(data).to_dict()
        except (OSError, ValueError):
            return None

    def get_app_version(self) -> str:
        return current_version()

    def start_preview(self, pdf_paths: list[str], settings: dict[str, Any]) -> str:
        """Detecta capítulos sin exportar nada, para que el usuario los revise antes."""
        job_id = str(uuid.uuid4())
        job = _PreviewJob(files=[_PreviewFileStatus(name=Path(p).name) for p in pdf_paths])
        self._remember(self._previews, job_id, job)

        thread = threading.Thread(
            target=self._run_preview,
            args=(job, pdf_paths, PipelineSettings.from_dict(settings)),
            daemon=True,
        )
        thread.start()
        return job_id

    def _run_preview(self, job: _PreviewJob, pdf_paths: list[str], settings: PipelineSettings) -> None:
        for file_status, pdf_path in zip(job.files, pdf_paths):
            file_status.status = "running"
            data = PipelineData(input_pdf=Path(pdf_path), settings=settings, output_dir=Path("."))
            try:
                data = detect_pipeline().run(data)
                if not data.chapters:
                    raise SplitError("No se detectaron capítulos en el documento.")
                file_status.status = "done"
                file_status.chapters = [
                    {"title": c.title, "start_page": c.start_page, "end_page": c.end_page}
                    for c in data.chapters
                ]
            except _PIPELINE_ERRORS as error:
                file_status.status = "error"
                file_status.error = str(error)
            except Exception as error:
                # Un fallo imprevisto no debe dejar el job clavado en "running":
                # la UI polearía para siempre con todos los controles bloqueados.
                file_status.status = "error"
                file_status.error = f"Error inesperado: {error}"
            finally:
                data.close()

        job.status = "error" if any(f.status == "error" for f in job.files) else "done"

    def get_preview_status(self, job_id: str) -> dict[str, Any]:
        job = self._previews.get(job_id)
        if job is None:
            return {"status": "unknown", "files": []}
        return {
            "status": job.status,
            "files": [
                {"name": f.name, "status": f.status, "chapters": f.chapters, "error": f.error}
                for f in job.files
            ],
        }

    def start_job(
        self,
        pdf_paths: list[str],
        output_dir: str,
        settings: dict[str, Any],
        create_book_folder: bool = True,
        book_folder_name: str = "",
        chapters_by_file: dict[str, list[dict[str, Any]]] | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        job = _Job(files=[_FileStatus(path=p, name=Path(p).name) for p in pdf_paths])
        self._remember(self._jobs, job_id, job)

        thread = threading.Thread(
            target=self._run_job,
            args=(
                job,
                pdf_paths,
                output_dir,
                PipelineSettings.from_dict(settings),
                create_book_folder,
                book_folder_name,
                chapters_by_file or {},
            ),
            daemon=True,
        )
        thread.start()
        return job_id

    @staticmethod
    def _book_output_dirs(
        base_output: Path,
        pdf_paths: Sequence[str],
        create_book_folder: bool,
        book_folder_name: str,
    ) -> list[Path]:
        """Resuelve la carpeta de cada libro dentro de la salida elegida.

        Con un solo PDF el nombre de carpeta es personalizable; con varios,
        cada libro usa el nombre de su archivo. Dos PDF distintos pueden
        llamarse igual (``2024/libro.pdf`` y ``2025/libro.pdf``), así que los
        nombres repetidos se numeran para que el segundo no pise al primero.
        """
        if not create_book_folder:
            return [base_output] * len(pdf_paths)

        single_file = len(pdf_paths) == 1
        taken: set[str] = set()
        directories: list[Path] = []
        for pdf_path in pdf_paths:
            if single_file and book_folder_name.strip():
                name = sanitize_filename(book_folder_name.strip())
            else:
                name = sanitize_filename(Path(pdf_path).stem)
            unique_name = name
            duplicate_number = 2
            while unique_name.casefold() in taken:
                unique_name = f"{name} ({duplicate_number})"
                duplicate_number += 1
            taken.add(unique_name.casefold())
            directories.append(base_output / unique_name)
        return directories

    def _run_job(
        self,
        job: _Job,
        pdf_paths: list[str],
        output_dir: str,
        settings: PipelineSettings,
        create_book_folder: bool,
        book_folder_name: str,
        chapters_by_file: dict[str, list[dict[str, Any]]],
    ) -> None:
        book_output_dirs = self._book_output_dirs(
            Path(output_dir), pdf_paths, create_book_folder, book_folder_name
        )
        report = JobProgressReporter(job)
        for file_status, pdf_path, book_output_dir in zip(job.files, pdf_paths, book_output_dirs):
            file_status.status = "running"
            data = PipelineData(input_pdf=Path(pdf_path), settings=settings, output_dir=book_output_dir)
            # Si el usuario ya revisó y editó los capítulos en la vista previa,
            # se exportan tal cual (sin repetir la detección); si no, se detectan
            # ahora mismo como antes.
            preset_chapters = chapters_by_file.get(pdf_path)
            try:
                if preset_chapters is not None:
                    data.chapters = [
                        Chapter(title=c["title"], start_page=c["start_page"], end_page=c["end_page"])
                        for c in preset_chapters
                    ]
                    data = export_pipeline().run(data, report)
                else:
                    data = default_pipeline().run(data, report)
                if not data.chapters:
                    raise SplitError("No se detectaron capítulos en el documento.")
                file_status.status = "done"
                file_status.chapters = len(data.chapters)
                file_status.output_dir = str(book_output_dir)
            except _PIPELINE_ERRORS as error:
                file_status.status = "error"
                file_status.error = str(error)
            except Exception as error:
                # Ver _run_preview: el job siempre tiene que llegar a un estado
                # final, aunque falle algo que no previmos.
                file_status.status = "error"
                file_status.error = f"Error inesperado: {error}"
            finally:
                data.close()

        job.status = "error" if any(f.status == "error" for f in job.files) else "done"

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        job = self._jobs.get(job_id)
        if job is None:
            return {"status": "unknown", "files": [], "logs": []}
        return {
            "status": job.status,
            "files": [
                {
                    "path": f.path,
                    "name": f.name,
                    "status": f.status,
                    "chapters": f.chapters,
                    "output_dir": f.output_dir,
                    "error": f.error,
                }
                for f in job.files
            ],
            "logs": job.logs[-200:],
        }

    def open_path(self, path: str) -> None:
        import subprocess
        import sys

        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", path])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    def check_for_updates(self) -> dict[str, Any]:
        release: ReleaseInfo | None = check_latest_release()
        if release is None or not is_newer(release.version):
            return {"available": False}
        return {
            "available": True,
            "version": release.version,
            "url": release.html_url,
        }

    def apply_update(self) -> dict[str, Any]:
        release = check_latest_release()
        if release is None:
            return {"ok": False, "error": "No se pudo consultar la última versión."}
        try:
            asset = pick_asset(release, executable_kind="gui")
            downloaded = download_asset(asset, staging_path(asset))
            # Punto de no retorno: reemplaza el ejecutable y relanza la app.
            # Va dentro del try porque el reemplazo también puede fallar, y el
            # banner de la UI queda girando en "Actualizando…" si no le contestamos.
            perform_update(downloaded)
        except (UpdateError, OSError) as error:
            return {"ok": False, "error": str(error)}
        return {"ok": True}
