@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ====================================================
echo  COMPILANDO YTDownloader - Generador de EXE
echo ====================================================
echo.

echo [1/5] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado en el sistema.
    echo Instala Python y asegurate de que este en el PATH.
    pause
    exit /b 1
)
python --version
echo.

echo [2/5] Verificando/Instalando dependencias necesarias...
pip install pyinstaller --quiet
pip install yt-dlp --quiet
pip install static-ffmpeg --quiet
echo.

echo [3/5] Verificando que el archivo principal existe...
if not exist "ytdownloader.py" (
    echo ERROR: No se encuentra ytdownloader.py
    echo Asegurate de estar en la carpeta del proyecto.
    pause
    exit /b 1
)
echo.

echo [4/5] Generando ejecutable con PyInstaller...
echo Esto puede tomar varios minutos...

REM --onefile = un solo .exe
REM --windowed = NO muestra ventana de consola (app grafica pura)
REM --name = nombre del ejecutable
REM --clean = limpia cache de compilacion anterior
REM --noconfirm = no pregunta confirmaciones

pyinstaller --onefile ^
            --windowed ^
            --name "YTDownloader" ^
            --hidden-import static_ffmpeg ^
            --hidden-import static_ffmpeg.run ^
            --clean ^
            --noconfirm ^
            ytdownloader.py

if errorlevel 1 (
    echo.
    echo ERROR: Fallo la compilacion.
    echo Revisa los mensajes de error arriba.
    pause
    exit /b 1
)
echo.

echo [5/5] Compilacion exitosa!
echo.
echo ====================================================
echo  EJECUTABLE GENERADO:
echo  %CD%\dist\YTDownloader.exe
echo ====================================================
echo.
echo NOTAS IMPORTANTES:
echo - El .exe incluye todas las dependencias (yt-dlp, static-ffmpeg)
echo - static-ffmpeg descarga los binarios de ffmpeg/ffprobe la primera
echo   vez que se ejecuta el programa (necesita conexion a internet esa
echo   primera vez, despues quedan guardados en cache).
echo - No tiene ventana de consola (app grafica pura)
echo - El archivo pesara aproximadamente 60-80 MB
echo.
