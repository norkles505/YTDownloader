#!/usr/bin/env bash
# Compila YTDownloader a un ejecutable de Linux con PyInstaller.
# Equivalente al compilar.bat de Windows. La salida va a dist-linux/ para no
# tocar el dist/ de Windows.
cd "$(dirname "$0")" || exit 1
RAIZ="$PWD"

salir() { read -rp "Presiona Enter para salir..." _; exit 1; }

echo "===================================================="
echo " COMPILANDO YTDownloader - Generador de ejecutable"
echo "===================================================="
echo

echo "[1/5] Verificando Python..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: Python no encontrado. Instala python3 con el gestor de paquetes."
  salir
fi
python3 --version
echo

echo "[2/5] Preparando entorno virtual y dependencias..."
if [ ! -x .venv/bin/python ]; then
  if ! python3 -m venv .venv; then
    rm -rf .venv
    echo "ERROR: No se pudo crear el entorno virtual."
    echo "En Debian/Ubuntu/Mint instala: sudo apt install python3-venv"
    salir
  fi
fi
if ! .venv/bin/python -m pip install -U pyinstaller yt-dlp static-ffmpeg "curl_cffi>=0.13" --quiet; then
  echo "ERROR: Falló la instalación de dependencias."
  salir
fi
echo

echo "[3/5] Verificando que el archivo principal existe..."
if [ ! -f manage.py ]; then
  echo "ERROR: No se encuentra manage.py. Asegúrate de estar en la carpeta del proyecto."
  salir
fi
echo

echo "[4/5] Generando ejecutable con PyInstaller..."
echo "Esto puede tomar varios minutos..."
# --onedir   = carpeta con el ejecutable y sus dependencias (arranca rápido)
# --windowed = sin ventana de consola (app gráfica)
# curl_cffi  = necesario para que yt-dlp pase la verificación anti-bot de TikTok
rm -rf dist-linux build-linux
if ! .venv/bin/pyinstaller --onedir \
      --windowed \
      --name "YTDownloader" \
      --distpath dist-linux \
      --workpath build-linux \
      --specpath build-linux \
      --hidden-import static_ffmpeg \
      --hidden-import static_ffmpeg.run \
      --hidden-import curl_cffi \
      --hidden-import curl_cffi.requests \
      --collect-all curl_cffi \
      --add-data "$RAIZ/icon/logo.png:icon" \
      --clean \
      --noconfirm \
      "$RAIZ/manage.py"; then
  echo
  echo "ERROR: Falló la compilación. Revisa los mensajes de arriba."
  echo "Si dice que falta objdump, instala binutils: sudo apt install binutils"
  salir
fi
echo

echo "[5/5] Compilación exitosa!"
echo

# --- Acceso directo con icono (Linux asigna el icono desde el .desktop) ---
DESTINO="$RAIZ/dist-linux/YTDownloader"
ICONO="$DESTINO/logo.png"
if [ -f "$RAIZ/icon/logo.png" ]; then
  cp "$RAIZ/icon/logo.png" "$ICONO"
  DESKTOP_FILE="$DESTINO/YTDownloader.desktop"
  cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=YTDownloader
Comment=Descargador de YouTube y TikTok
Exec="$DESTINO/YTDownloader"
Path=$DESTINO
Icon=$ICONO
Terminal=false
Categories=AudioVideo;Utility;
StartupWMClass=YTDownloader
EOF
  chmod +x "$DESKTOP_FILE"

  # Menú de aplicaciones
  mkdir -p "$HOME/.local/share/applications"
  cp "$DESKTOP_FILE" "$HOME/.local/share/applications/YTDownloader.desktop"
  command -v update-desktop-database >/dev/null 2>&1 && \
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null

  # Escritorio
  ESCRITORIO="$(xdg-user-dir DESKTOP 2>/dev/null)"
  [ -z "$ESCRITORIO" ] && ESCRITORIO="$HOME/Desktop"
  if [ -d "$ESCRITORIO" ]; then
    cp "$DESKTOP_FILE" "$ESCRITORIO/YTDownloader.desktop"
    chmod +x "$ESCRITORIO/YTDownloader.desktop"
    # En GNOME hay que marcarlo como confiable (si no, pide "Permitir lanzar")
    command -v gio >/dev/null 2>&1 && \
      gio set "$ESCRITORIO/YTDownloader.desktop" metadata::trusted true 2>/dev/null
  fi
  echo "Acceso directo creado (menú de aplicaciones y escritorio)."
  echo
fi

echo "===================================================="
echo " EJECUTABLE GENERADO:"
echo " $RAIZ/dist-linux/YTDownloader/YTDownloader"
echo "===================================================="
echo
echo "NOTAS:"
echo "- Es una CARPETA (dist-linux/YTDownloader/): hay que copiarla entera."
echo "- static-ffmpeg descarga ffmpeg la primera vez que se ejecuta (necesita internet)."
