"""Entry point de la app de escritorio (ventana pywebview + React)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import webview
from webview.dom import DOMEventHandler

try:
    # Detalle interno de pywebview, no parte de su API pública: sólo alimenta
    # el resguardo de drag&drop en GTK. Si una versión lo renombra, la app
    # tiene que seguir abriendo, así que el import va aislado.
    from webview.dom import _dnd_state
except ImportError:
    _dnd_state = None

from gui.backend.api import Api

_DEV_SERVER_URL = "http://localhost:5173"


def _frontend_url() -> str:
    """Usa el build estático empaquetado; con --dev apunta al server de Vite."""
    if "--dev" in sys.argv:
        return _DEV_SERVER_URL

    if getattr(sys, "frozen", False):
        base_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_dir = Path(__file__).resolve().parent.parent / "frontend"

    index_html = base_dir / "dist" / "index.html"
    if not index_html.is_file():
        raise SystemExit(
            f"No se encontró el build del frontend en {index_html}.\n"
            "Corré `npm --prefix gui/frontend run build` antes de iniciar la GUI, "
            "o usá `--dev` con `npm --prefix gui/frontend run dev` corriendo aparte."
        )
    return index_html.as_uri()


def _icon_path() -> str | None:
    """Resuelve el ícono de la app; devuelve None si no se lo encuentra."""
    if getattr(sys, "frozen", False):
        base_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        icon_file = base_dir / "icon.png"
    else:
        icon_file = Path(__file__).resolve().parent.parent.parent / "packaging" / "icon.png"
    return str(icon_file) if icon_file.is_file() else None


def _register_drop_handler(window: webview.Window) -> None:
    """Habilita soltar PDFs sobre la ventana y los reenvía al frontend.

    pywebview solo expone la ruta real del archivo (``pywebviewFullPath``)
    cuando hay un listener de ``drop`` registrado vía su API de DOM; por eso
    no alcanza con un `onDrop` normal del lado de React.
    """

    def _on_drop(event: dict) -> None:
        files = (event.get("dataTransfer") or {}).get("files", [])
        paths = [
            file["pywebviewFullPath"]
            for file in files
            if file.get("pywebviewFullPath", "").lower().endswith(".pdf")
        ]
        if not paths:
            paths = _native_dropped_pdfs()
        if paths:
            window.evaluate_js(
                f"window.__onPdfsDropped && window.__onPdfsDropped({json.dumps(paths)})"
            )

    try:
        window.dom.document.events.dragover += DOMEventHandler(lambda event: None, prevent_default=True)
        window.dom.document.events.drop += DOMEventHandler(_on_drop, prevent_default=True)
    except Exception:
        import traceback

        print("No se pudo registrar el listener de 'drop':", file=sys.stderr)
        traceback.print_exc()


def _native_dropped_pdfs() -> list[str]:
    """Resguardo para los WebKitGTK que entregan `dataTransfer.files` vacío.

    En esos casos el drop igual ocurrió y GTK capturó las rutas reales por una
    vía nativa separada. Se reintenta un momento corto por si la señal nativa
    todavía no llegó cuando el evento JS sí lo hizo.
    """
    if _dnd_state is None:
        return []
    for _ in range(15):
        if _dnd_state["paths"]:
            break
        time.sleep(0.03)
    native_paths = list(_dnd_state["paths"])
    _dnd_state["paths"].clear()
    return [full_path for _, full_path in native_paths if full_path.lower().endswith(".pdf")]


def main() -> int:
    api = Api()
    window = webview.create_window(
        "PDF Chapter Splitter",
        _frontend_url(),
        js_api=api,
        width=1000,
        height=720,
        min_size=(720, 480),
    )
    window.events.loaded += lambda: _register_drop_handler(window)
    try:
        webview.start(icon=_icon_path())
    except webview.errors.WebViewException:
        print(
            "\nNo se pudo abrir la ventana: falta el WebView del sistema operativo.\n"
            "En Debian/Ubuntu, instalalo una sola vez con:\n\n"
            "  sudo apt install python3-gi gir1.2-webkit2-4.1\n\n"
            "(si tu distro es más vieja, probá con gir1.2-webkit2-4.0)\n",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
