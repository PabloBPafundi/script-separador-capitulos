# PDF Chapter Splitter

Divide uno o más libros PDF en un archivo por capítulo, conservando el formato
original mediante PyMuPDF. Disponible como **app de escritorio** (sin
consola, sin instalar Python) y como **CLI** para uso avanzado/automatizado.
Ambas comparten el mismo núcleo, organizado como un pipeline
**Pipes and Filters** (`pdfsplitter/`).

## Usar la app de escritorio (recomendado)

Descargá el instalador de la última
[Release](https://github.com/PabloBPafundi/script-separador-capitulos/releases/latest)
según tu sistema operativo. No necesitás instalar Python ni nada más (en
Linux, el instalador te avisa si falta el WebView del sistema). Se instala
**por usuario**: no pide contraseña de administrador/sudo, y así la
auto-actualización de un clic puede reemplazar sus propios archivos sin
volver a pedir permisos.

- **Windows:** descargá y ejecutá `pdf-chapter-splitter-gui-setup.exe`.
  Se instala en tu carpeta de usuario, agrega un acceso directo al Menú
  Inicio (y al escritorio si lo tildás) y un desinstalador en
  *Configuración > Aplicaciones*.
- **Linux:** descargá y descomprimí
  `pdf-chapter-splitter-gui-linux-installer.tar.gz`, entrá a la carpeta y
  corré `./install.sh`. Instala en `~/.local` (sin sudo), agrega la app al
  menú de aplicaciones y deja un acceso de "Desinstalar PDF Chapter
  Splitter" también en el menú (o corré directamente
  `~/.local/opt/pdf-chapter-splitter/uninstall.sh`).

Si preferís no instalar nada y usar un único archivo portable, también están
disponibles `pdf-chapter-splitter-gui-windows.exe` y
`pdf-chapter-splitter-gui-linux` sueltos en la misma Release.

La app avisa sola cuando hay una versión nueva y permite actualizarse con un
clic (descarga el nuevo ejecutable y se reemplaza sola, tanto si la
instalaste con el instalador como si usás el binario portable).

### Correr la GUI desde el código fuente

Requiere Python 3.10+ y Node.js (solo para compilar la interfaz la primera
vez; el resultado final no necesita Node).

- **Linux:** `./ejecutar-gui.sh`
- **Windows:** doble clic en `ejecutar-gui.bat`

En Linux además hace falta el WebView del sistema:

```bash
sudo apt install python3-gi gir1.2-webkit2-4.1
```

## Usar la línea de comandos (CLI)

Pensado para procesar varios libros en lote o integrarlo en otro flujo de
trabajo, sin interfaz gráfica.

1. Copiá PDFs dentro de `input/`.
2. En Linux ejecutá `./ejecutar.sh`; en Windows, doble clic en `ejecutar.bat`.
3. Encontrá los resultados en `output/<nombre-del-libro>/`.

Los lanzadores muestran los PDFs detectados, piden confirmación y, solo
entonces, crean el entorno Python e instalan dependencias automáticamente la
primera vez.

Si Linux no permite ejecutar el archivo, aplica una sola vez:

```bash
chmod +x ejecutar.sh ejecutar-gui.sh
```

## Detección de capítulos

La aplicación usa este orden:

1. Índice interno del PDF (bookmarks/TOC).
2. Encabezados OCR como `CHAPTER I - TÍTULO`, incluso con errores comunes como
   `C HAPTER V`.
3. Expresiones regulares configurables.

En el modo CLI, los valores por defecto están en `cli/config.py`. En la GUI
son ajustables desde el panel "Ajustes de detección" de la interfaz. Ambos
casos usan la misma clase `PipelineSettings` (`pdfsplitter/settings.py`).

## Arquitectura

```text
pdfsplitter/   Núcleo Pipes and Filters: OpenFilter, DetectFilter, SplitFilter,
               Pipeline/Pipe, PipelineSettings, auto-actualización.
cli/           Entry point de consola (procesa todo input/ en lote).
gui/backend/   Puente Python↔JS para la app de escritorio (pywebview).
gui/frontend/  Interfaz en React + TypeScript + Vite.
packaging/     Instaladores de usuario: installer.iss (Windows/Inno Setup)
               e install.sh (Linux, ~/.local sin sudo).
tests/         Pruebas de integración y del pipeline.
```

Ver comentarios en `pdfsplitter/pipeline.py` para el diseño del patrón.

## Estructura

```text
input/       PDFs a procesar en modo CLI (no se suben a Git)
output/      Capítulos generados (no se suben a Git)
logs/        Registros de ejecución (no se suben a Git)
ejecutar.sh / ejecutar.bat          Lanzador CLI
ejecutar-gui.sh / ejecutar-gui.bat  Lanzador de la app de escritorio
```

## Desarrollo

Requiere Python 3.10+ y Node.js 20+.

```bash
.venv/bin/python -m unittest discover -s tests -v
```

### Frontend en modo desarrollo (hot-reload)

```bash
npm --prefix gui/frontend run dev          # deja el servidor de Vite corriendo
.venv/bin/python -m gui.backend.app --dev  # en otra terminal
```

### Compilar ejecutables localmente

```bash
.venv/bin/pip install pyinstaller
npm --prefix gui/frontend run build
.venv/bin/pyinstaller pdf-chapter-splitter.spec       # CLI
.venv/bin/pyinstaller pdf-chapter-splitter-gui.spec   # GUI
```

Los binarios quedan en `dist/`. El `.exe` de Windows debe generarse desde
Windows y el binario de Linux desde Linux (por eso el workflow de CI compila
ambos automáticamente, ver abajo).

### Compilar los instaladores localmente

**Windows** (requiere [Inno Setup](https://jrsoftware.org/isinfo.php)):

```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DMyAppVersion=0.1.0 packaging\windows\installer.iss
```

Genera `dist\pdf-chapter-splitter-gui-setup.exe`.

**Linux** (no requiere herramientas extra, junta los binarios ya compilados):

```bash
STAGE=pdf-chapter-splitter-installer
mkdir -p "$STAGE/bin"
cp dist/pdf-chapter-splitter-gui dist/pdf-chapter-splitter "$STAGE/bin/"
cp packaging/icon.png packaging/linux/install.sh packaging/linux/*.template "$STAGE/"
chmod +x "$STAGE/install.sh" "$STAGE/bin/"*
tar czf pdf-chapter-splitter-gui-linux-installer.tar.gz "$STAGE"
```

## Publicar una nueva versión

1. Actualizá `pdfsplitter/__version__.py`.
2. Commiteá y creá un tag: `git tag v0.2.0 && git push origin v0.2.0`.
3. El workflow `.github/workflows/release.yml` compila en runners de GitHub
   Actions —no hace falta tener una máquina Windows— y publica 6 assets en
   una GitHub Release: los binarios portables (CLI + GUI × Windows + Linux)
   y los dos instaladores de usuario (`pdf-chapter-splitter-gui-setup.exe` y
   `pdf-chapter-splitter-gui-linux-installer.tar.gz`). Antes corre los tests.
4. La app de escritorio detecta la nueva versión sola la próxima vez que se
   abra (consulta `GET /repos/.../releases/latest`, sin backend propio) y se
   actualiza reemplazando su propio binario, tanto si se instaló con el
   instalador como si es la versión portable.

Antes de anunciar una release ampliamente, conviene probar a mano en una PC
Windows y una Linux reales al menos una vez: que el instalador corra, que
aparezca el ícono en el menú, y que el desinstalador limpie todo. CI solo
verifica que compile y que los tests pasen, no interactúa con la ventana ni
con los instaladores.
