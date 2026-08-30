#!/usr/bin/env bash
# Interfaz de terminal para Linux.

set -u

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"
INPUT_DIR="$SCRIPT_DIR/input"
OUTPUT_DIR="$SCRIPT_DIR/output"

pause() {
    echo
    read -r -p "Presioná Enter para cerrar..." _
}

trap pause EXIT

clear
echo "============================================================"
echo "                 PDF CHAPTER SPLITTER"
echo "============================================================"
echo
echo "Este programa divide cada PDF de la carpeta input/ en"
echo "capítulos y guarda el resultado en output/<nombre-del-libro>/"
echo

if [ ! -d "$INPUT_DIR" ]; then
    echo "No existe la carpeta de entrada: $INPUT_DIR"
    echo "Creala y copiá allí los PDFs que quieras procesar."
    exit 1
fi

mapfile -d '' PDF_FILES < <(find "$INPUT_DIR" -maxdepth 1 -type f -iname '*.pdf' -print0 | sort -z)
if [ "${#PDF_FILES[@]}" -eq 0 ]; then
    echo "No se encontraron PDFs en: $INPUT_DIR"
    echo "Copiá uno o más archivos .pdf y volvé a ejecutar este lanzador."
    exit 0
fi

echo "PDFs encontrados (${#PDF_FILES[@]}):"
for pdf_file in "${PDF_FILES[@]}"; do
    echo "  - $(basename "$pdf_file")"
done

echo
read -r -p "¿Deseás procesarlos ahora? [s/N]: " ANSWER
case "${ANSWER,,}" in
    s|si|sí) ;;
    *)
        echo "Operación cancelada. No se modificó ningún archivo."
        exit 0
        ;;
esac

echo
echo "Preparando la aplicación..."
if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: no se encontró Python 3. Instalalo y volvé a ejecutar este archivo."
    exit 1
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
    echo "Creando el entorno local (solo esta primera vez)..."
    if ! python3 -m venv "$VENV_DIR"; then
        echo "No se pudo crear el entorno virtual. En Debian/Ubuntu instalá: python3-venv"
        exit 1
    fi
fi

echo "Verificando dependencias..."
if ! "$VENV_DIR/bin/python" -m pip install --disable-pip-version-check -q -r "$SCRIPT_DIR/requirements.txt"; then
    echo "No se pudieron instalar las dependencias. Verificá tu conexión a Internet."
    exit 1
fi

echo
echo "Iniciando procesamiento. Esto puede tardar unos minutos..."
echo "------------------------------------------------------------"
(cd "$SCRIPT_DIR" && "$VENV_DIR/bin/python" -m cli.main)
EXIT_CODE=$?
echo "------------------------------------------------------------"

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "Proceso terminado correctamente."
    echo "Resultados: $OUTPUT_DIR"
else
    echo "El proceso terminó con errores."
    echo "Revisá el detalle en: $SCRIPT_DIR/logs"
fi

exit "$EXIT_CODE"
