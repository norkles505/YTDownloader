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
pip install -U pyinstaller --quiet
pip install -U yt-dlp --quiet
pip install -U static-ffmpeg --quiet
pip install -U "curl_cffi>=0.13" --quiet
echo.

echo [3/5] Verificando que el archivo principal existe...
if not exist "manage.py" (
    echo ERROR: No se encuentra manage.py
    echo Asegurate de estar en la carpeta del proyecto.
    pause
    exit /b 1
)
if not exist "icon\logo.ico" (
    echo ERROR: No se encuentra icon\logo.ico
    echo Corre icono.bat primero para generarlo desde icon\logo.png
    pause
    exit /b 1
)
echo.

echo [4/5] Generando ejecutable con PyInstaller...
echo Esto puede tomar varios minutos...

REM Se borra dist\ entero antes de compilar. --clean de PyInstaller solo
REM limpia su propia cache interna, NO borra archivos viejos que hayan
REM quedado sueltos en dist\ de compilaciones anteriores (por ejemplo,
REM un .exe de una build --onefile vieja que confunde cual es el actual).
if exist "dist" (
    rmdir /s /q "dist"
)

REM --onedir = carpeta con el .exe y sus dependencias sueltas (arranca
REM            rapido: --onefile tiene que descomprimir todo a una carpeta
REM            temporal en CADA apertura, por eso tardaba en abrir)
REM --windowed = NO muestra ventana de consola (app grafica pura)
REM --icon = icono del .exe (generado con icono.bat)
REM --name = nombre del ejecutable
REM --clean = limpia cache de compilacion anterior
REM --noconfirm = no pregunta confirmaciones
REM --hidden-import curl_cffi... = TikTok ahora exige "impersonar" un
REM     navegador real (impersonation) para pasar su verificacion anti-bot;
REM     yt-dlp usa curl_cffi para eso. Sin empaquetarlo, el .exe compilado
REM     falla al descargar de TikTok aunque en la PC de desarrollo funcione.

pyinstaller --onedir ^
            --windowed ^
            --icon "icon\logo.ico" ^
            --name "YTDownloader" ^
            --hidden-import static_ffmpeg ^
            --hidden-import static_ffmpeg.run ^
            --hidden-import curl_cffi ^
            --hidden-import curl_cffi.requests ^
            --collect-all curl_cffi ^
            --clean ^
            --noconfirm ^
            manage.py

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
echo  %CD%\dist\YTDownloader\YTDownloader.exe
echo ====================================================
echo.
echo NOTAS IMPORTANTES:
echo - Ahora es una CARPETA (dist\YTDownloader\), no un solo .exe suelto.
echo   Hay que entregar/copiar la carpeta entera, no solo el .exe.
echo - Si queres seguir compartiendo un unico archivo, zippea la carpeta
echo   dist\YTDownloader antes de enviarla.
echo - El .exe incluye todas las dependencias (yt-dlp, static-ffmpeg, curl_cffi)
echo - static-ffmpeg descarga los binarios de ffmpeg/ffprobe la primera
echo   vez que se ejecuta el programa (necesita conexion a internet esa
echo   primera vez, despues quedan guardados en cache).
echo - No tiene ventana de consola (app grafica pura)
echo - El .exe pesa poco (unos KB); las dependencias van sueltas en la carpeta
echo.
