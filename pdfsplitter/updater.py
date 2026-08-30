"""Auto-actualización sin backend propio, usando GitHub Releases como origen.

Solo la GUI invoca `apply_update`; el CLI se limita a `check_latest_release`
si se lo llama con --check-updates. No agrega dependencias: usa `urllib` de
la librería estándar.
"""

from __future__ import annotations

import json
import os
import platform
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from pdfsplitter.__version__ import __version__

GITHUB_REPO = "PabloBPafundi/script-separador-capitulos"
_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
_REQUEST_TIMEOUT_SECONDS = 10


class UpdateError(RuntimeError):
    """Indica que no se pudo consultar o aplicar una actualización."""


@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    name: str
    download_url: str
    size: int


@dataclass(frozen=True, slots=True)
class ReleaseInfo:
    version: str
    assets: list[ReleaseAsset]
    html_url: str


def current_version() -> str:
    return __version__


def _parse_version(tag: str) -> tuple[int, ...]:
    cleaned = tag.lstrip("vV")
    parts: list[int] = []
    for part in cleaned.split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def is_newer(remote_tag: str, local_version: str = __version__) -> bool:
    return _parse_version(remote_tag) > _parse_version(local_version)


def check_latest_release() -> ReleaseInfo | None:
    """Consulta la última Release pública del repo. None si no hay conexión."""
    request = urllib.request.Request(
        _API_URL, headers={"Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(request, timeout=_REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None

    assets = [
        ReleaseAsset(
            name=asset["name"],
            download_url=asset["browser_download_url"],
            size=asset["size"],
        )
        for asset in payload.get("assets", [])
    ]
    return ReleaseInfo(
        version=payload.get("tag_name", ""),
        assets=assets,
        html_url=payload.get("html_url", ""),
    )


def _asset_suffix_for_current_platform(executable_kind: str) -> str:
    """`executable_kind` es 'gui' o 'cli'. Devuelve el sufijo esperado del asset."""
    system = platform.system().lower()
    if system == "windows":
        return f"{executable_kind}-windows.exe"
    if system == "linux":
        return f"{executable_kind}-linux"
    raise UpdateError(f"Plataforma no soportada para auto-actualización: {system}")


def pick_asset(release: ReleaseInfo, executable_kind: str = "gui") -> ReleaseAsset:
    suffix = _asset_suffix_for_current_platform(executable_kind)
    for asset in release.assets:
        if asset.name.endswith(suffix):
            return asset
    raise UpdateError(f"La release {release.version} no tiene un asset para: {suffix}")


def current_executable() -> Path:
    """Ruta del binario en ejecución, que la actualización va a reemplazar."""
    return Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0]).resolve()


def staging_path(asset: ReleaseAsset) -> Path:
    """Dónde dejar la descarga antes de reemplazar el ejecutable.

    Se descarga junto al ejecutable y no en el temporal del sistema: `/tmp`
    suele ser un tmpfs aparte y `os.replace` entre sistemas de archivos
    distintos falla con EXDEV, que es justo lo que hace el reemplazo en Linux.
    """
    target_dir = current_executable().parent
    if not os.access(target_dir, os.W_OK):
        raise UpdateError(
            f"No hay permiso de escritura en {target_dir}. "
            "Reinstalá la app desde la última release para actualizarla."
        )
    return target_dir / f".{asset.name}.download"


def download_asset(asset: ReleaseAsset, destination: Path) -> Path:
    """Descarga el asset y valida su tamaño contra lo reportado por la API."""
    request = urllib.request.Request(asset.download_url)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read()
    except urllib.error.URLError as error:
        raise UpdateError(f"No se pudo descargar la actualización: {error}") from error

    if len(data) != asset.size:
        raise UpdateError(
            f"El tamaño descargado ({len(data)}) no coincide con el esperado ({asset.size})."
        )

    destination.write_bytes(data)
    if platform.system().lower() != "windows":
        destination.chmod(destination.stat().st_mode | stat.S_IEXEC)
    return destination


def apply_update(new_binary: Path) -> None:
    """Reemplaza el ejecutable en uso por `new_binary` y relanza la app.

    Termina el proceso actual: el llamador debe considerar esta función como
    un punto de no retorno (no continúa ejecución después de llamarla).
    """
    executable = current_executable()

    if platform.system().lower() == "windows":
        _apply_update_windows(new_binary, executable)
    else:
        _apply_update_linux(new_binary, executable)


def _apply_update_linux(new_binary: Path, current_executable: Path) -> None:
    os.replace(new_binary, current_executable)
    os.chmod(current_executable, current_executable.stat().st_mode | stat.S_IEXEC)
    subprocess.Popen([str(current_executable)], start_new_session=True)
    os._exit(0)


def _apply_update_windows(new_binary: Path, current_executable: Path) -> None:
    updater_script = Path(tempfile.gettempdir()) / "pdf-chapter-splitter-updater.bat"
    updater_script.write_text(
        "@echo off\r\n"
        ":wait\r\n"
        f'tasklist /FI "IMAGENAME eq {current_executable.name}" 2>NUL | find /I "{current_executable.name}" >NUL\r\n'
        "if not errorlevel 1 (\r\n"
        "  timeout /t 1 /nobreak >NUL\r\n"
        "  goto wait\r\n"
        ")\r\n"
        f'copy /Y "{new_binary}" "{current_executable}" >NUL\r\n'
        f'start "" "{current_executable}"\r\n'
        "del \"%~f0\"\r\n",
        encoding="utf-8",
    )
    subprocess.Popen(
        ["cmd", "/c", str(updater_script)],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    os._exit(0)
