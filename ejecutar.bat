@echo off
REM Interfaz de terminal para Windows 10 y Windows 11.
setlocal EnableExtensions
cd /d "%~dp0"
title PDF Chapter Splitter
cls

echo ============================================================
echo                  PDF CHAPTER SPLITTER
echo ============================================================
echo.
echo Este programa divide cada PDF de la carpeta input en
echo capitulos y guarda el resultado en output/[nombre-del-libro]/.
echo.

if not exist "input" (
    echo No existe la carpeta de entrada: input
    echo Creala y copia alli los PDFs que quieras procesar.
    pause
    exit /b 1
)

dir /b /a-d "input\*.pdf" >nul 2>&1
if errorlevel 1 (
    echo No se encontraron PDFs en la carpeta input.
    echo Copia uno o mas archivos .pdf y volve a ejecutar este lanzador.
    pause
    exit /b 0
)

set PDF_COUNT=0
echo PDFs encontrados:
for %%F in ("input\*.pdf") do (
    if exist "%%~fF" (
        set /a PDF_COUNT+=1
        echo   - %%~nxF
    )
)
echo.
set "ANSWER="
set /p ANSWER=Deseas procesarlos ahora? [S/N]: 
if /I "%ANSWER%"=="S" goto :confirmed
if /I "%ANSWER%"=="SI" goto :confirmed
echo Operacion cancelada. No se modifico ningun archivo.
pause
exit /b 0

:confirmed
echo.
echo Preparando la aplicacion...
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

echo Verificando dependencias...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
    echo No se pudieron instalar las dependencias. Verifica tu conexion a Internet.
    pause
    exit /b 1
)

echo.
echo Iniciando procesamiento. Esto puede tardar unos minutos...
echo ------------------------------------------------------------
".venv\Scripts\python.exe" -m cli.main
set EXIT_CODE=%ERRORLEVEL%
echo ------------------------------------------------------------

if %EXIT_CODE% EQU 0 (
    echo Proceso terminado correctamente.
    echo Resultados: output
) else (
    echo El proceso termino con errores.
    echo Revisa el detalle en: logs
)

pause
exit /b %EXIT_CODE%
