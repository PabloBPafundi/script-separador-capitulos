# PDF Chapter Splitter

Divide uno o más libros PDF en un archivo por capítulo, conservando el formato
original mediante PyMuPDF.

## Requisito

Los lanzadores requieren **Python 3.10 o superior** instalado. No necesitas
instalar ninguna librería manualmente: el script crea el entorno e instala todo
lo demás.

- **Windows:** descarga Python desde [python.org/downloads](https://www.python.org/downloads/)
  e instala la versión actual. Marca la opción **Add Python to PATH**.
- **Debian/Ubuntu:** instala `python3` y `python3-venv` desde el gestor de paquetes.

## Uso rápido

1. Copia PDFs dentro de `input/`.
2. En Linux ejecuta `./ejecutar.sh`; en Windows, haz doble clic en `ejecutar.bat`.
3. Encuentra los resultados en `output/<nombre-del-libro>/`.

Los lanzadores muestran los PDFs detectados, piden confirmación y, solo entonces,
crean el entorno Python e instalan dependencias automáticamente la primera vez.
La terminal queda abierta para mostrar el resultado.

Si Linux no permite ejecutar el archivo, aplica una sola vez:

```bash
chmod +x ejecutar.sh
```

## Detección de capítulos

La aplicación usa este orden:

1. Índice interno del PDF (bookmarks/TOC).
2. Encabezados OCR como `CHAPTER I - TÍTULO`, incluso con errores comunes como
   `C HAPTER V`.
3. Expresiones regulares configurables.

Toda la configuración está en `config.py`: nombres de archivos, reglas de
detección, reemplazo de resultados y rutas.

## Estructura

```text
input/       PDFs a procesar (no se suben a Git)
output/      Capítulos generados (no se suben a Git)
logs/        Registros de ejecución (no se suben a Git)
ejecutar.sh  Lanzador Linux
ejecutar.bat Lanzador Windows
```

## Desarrollo y ejecutable

Requiere Python 3.10+. Para ejecutar pruebas:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Para crear un ejecutable en el sistema actual:

```bash
.venv/bin/python -m pip install pyinstaller
.venv/bin/pyinstaller --onefile --name pdf-chapter-splitter main.py
```

El binario se crea en `dist/`. Debe generarse un `.exe` desde Windows y un
binario Linux desde Linux.
