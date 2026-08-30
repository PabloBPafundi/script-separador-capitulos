#!/usr/bin/env bash
# Lanzador de la app de escritorio (GUI) para Linux.

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
FRONTEND_DIR="$SCRIPT_DIR/gui/frontend"

pause() {
    echo
    read -r -p "Presioná Enter para cerrar..." _
}

trap pause EXIT

clear
echo "============================================================"
echo "            PDF CHAPTER SPLITTER - APP DE ESCRITORIO"
echo "============================================================"
echo

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: no se encontró Python 3. Instalalo y volvé a ejecutar este archivo."
    exit 1
fi

echo "Verificando el WebView del sistema (WebKitGTK)..."
if ! python3 -c "import gi; gi.require_version('WebKit2', '4.1')" >/dev/null 2>&1 \
   && ! python3 -c "import gi; gi.require_version('WebKit2', '4.0')" >/dev/null 2>&1; then
    echo
    echo "Falta un componente del sistema operativo que la app necesita para"
    echo "dibujar su ventana (WebKitGTK). Instalalo una sola vez con:"
    echo
    echo "  sudo apt install python3-gi gir1.2-webkit2-4.1"
    echo
    echo "(si tu Debian/Ubuntu es más viejo, probá con gir1.2-webkit2-4.0)"
    exit 1
fi

# El entorno virtual necesita ver los paquetes del sistema (--system-site-packages)
# para poder usar el WebKitGTK que se acaba de verificar arriba; si ya existe uno
# creado sin esa opción (de una corrida anterior de este mismo repo), se recrea.
if [ -x "$VENV_DIR/bin/python" ] && ! "$VENV_DIR/bin/python" -c "import gi" >/dev/null 2>&1; then
    echo "Actualizando el entorno local para que vea las librerías del sistema..."
    rm -rf "$VENV_DIR"
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Creando el entorno local (solo esta primera vez)..."
    if ! python3 -m venv --system-site-packages "$VENV_DIR"; then
        echo "No se pudo crear el entorno virtual. En Debian/Ubuntu instalá: python3-venv"
        exit 1
    fi
fi

echo "Verificando dependencias de Python..."
if ! "$VENV_DIR/bin/python" -m pip install --disable-pip-version-check -q -r "$SCRIPT_DIR/requirements.txt"; then
    echo "No se pudieron instalar las dependencias. Verificá tu conexión a Internet."
    exit 1
fi

# Con Node.js instalado se recompila en cada corrida (no solo la primera vez)
# para que los cambios en gui/frontend/src siempre lleguen a la ventana. Sin
# Node.js se usa la interfaz ya compilada que venga en gui/frontend/dist: así
# alcanza con recibir el proyecto en un zip y tener Python.
if command -v npm >/dev/null 2>&1; then
    if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
        echo
        echo "Primera vez: instalando dependencias de la interfaz..."
        if ! (cd "$FRONTEND_DIR" && npm install --silent); then
            echo "No se pudieron instalar las dependencias de la interfaz."
            exit 1
        fi
    fi
    echo "Compilando la interfaz..."
    if ! (cd "$FRONTEND_DIR" && npm run build --silent); then
        echo "No se pudo compilar la interfaz."
        exit 1
    fi
elif [ -f "$FRONTEND_DIR/dist/index.html" ]; then
    echo "Node.js no está instalado: se usará la interfaz ya compilada."
else
    echo "Error: no se encontró npm y no hay una interfaz compilada."
    echo "Instalá Node.js (https://nodejs.org/) y volvé a intentar."
    exit 1
fi

echo
echo "Iniciando la aplicación..."
echo "------------------------------------------------------------"
(cd "$SCRIPT_DIR" && "$VENV_DIR/bin/python" -m gui.backend.app)
EXIT_CODE=$?
echo "------------------------------------------------------------"

if [ "$EXIT_CODE" -ne 0 ]; then
    echo "La aplicación terminó con errores."
    echo "Si el error menciona WebKit/GTK, en Debian/Ubuntu instalá:"
    echo "  sudo apt install python3-gi gir1.2-webkit2-4.1"
fi

exit "$EXIT_CODE"
