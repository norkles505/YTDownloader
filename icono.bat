@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ====================================================
echo  GENERANDO ICONO - icon\logo.png a icon\logo.ico
echo ====================================================
echo.

echo [1/3] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado en el sistema.
    echo Instala Python y asegurate de que este en el PATH.
    pause
    exit /b 1
)
python --version
echo.

echo [2/3] Verificando/Instalando Pillow...
pip install pillow --quiet
echo.

echo [3/3] Convirtiendo icon\logo.png a icon\logo.ico...
if not exist "icon\logo.png" (
    echo ERROR: No se encuentra icon\logo.png
    echo Asegurate de que la imagen este en la carpeta icon.
    pause
    exit /b 1
)

python -c "from PIL import Image; img = Image.open('icon/logo.png').convert('RGBA'); img.save('icon/logo.ico', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"

if errorlevel 1 (
    echo.
    echo ERROR: Fallo la conversion.
    echo Revisa que icon\logo.png sea una imagen valida.
    pause
    exit /b 1
)

echo.
echo ====================================================
echo  ICONO GENERADO: icon\logo.ico
echo ====================================================
echo.
echo Ahora podes correr compilar.bat: YTDownloader.spec ya
echo esta configurado para usar icon\logo.ico como icono del exe.
echo.
pause
