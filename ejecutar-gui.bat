@echo off
REM Lanzador de la app de escritorio (GUI) para Windows 10 y 11.
setlocal EnableExtensions
cd /d "%~dp0"
title PDF Chapter Splitter
cls

echo ============================================================
echo         PDF CHAPTER SPLITTER - APP DE ESCRITORIO
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Creando el entorno local ^(solo esta primera vez^)...
    py -3 -m venv .venv 2>nul
    if errorlevel 1 python -m venv .venv
    if errorlevel 1 (
        echo Error: no se pudo crear el entorno. Instala Python 3 y volve a intentar.
        pause
        exit /b 1
    )
)

echo Verificando dependencias de Python...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
    echo No se pudieron instalar las dependencias. Verifica tu conexion a Internet.
    pause
    exit /b 1
)

REM Con Node.js instalado se recompila en cada corrida (no solo la primera vez)
REM para que los cambios en gui\frontend\src siempre lleguen a la ventana. Sin
REM Node.js se usa la interfaz ya compilada que venga en gui\frontend\dist: asi
REM alcanza con recibir el proyecto en un zip y tener Python.
where npm >nul 2>&1
set NPM_FOUND=0
if not errorlevel 1 set NPM_FOUND=1

if %NPM_FOUND% EQU 1 (
    if not exist "gui\frontend\node_modules" (
        echo.
        echo Primera vez: instalando dependencias de la interfaz...
        pushd gui\frontend
        call npm install --silent
        popd
    )
    echo Compilando la interfaz...
    pushd gui\frontend
    call npm run build --silent
    popd
    if not exist "gui\frontend\dist\index.html" (
        echo No se pudo compilar la interfaz.
        pause
        exit /b 1
    )
) else if exist "gui\frontend\dist\index.html" (
    echo Node.js no esta instalado: se usara la interfaz ya compilada.
) else (
    echo Error: no se encontro npm y no hay una interfaz compilada.
    echo Instala Node.js ^(https://nodejs.org/^) y volve a intentar.
    pause
    exit /b 1
)

echo.
echo Iniciando la aplicacion...
echo ------------------------------------------------------------
".venv\Scripts\python.exe" -m gui.backend.app
set EXIT_CODE=%ERRORLEVEL%
echo ------------------------------------------------------------

if %EXIT_CODE% NEQ 0 (
    echo La aplicacion termino con errores.
)

pause
exit /b %EXIT_CODE%
