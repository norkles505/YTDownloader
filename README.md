# YT Downloader

Aplicación de escritorio (Tkinter) para descargar videos y audio de **YouTube** y **TikTok**, con opción de recortar fragmentos. Usa [yt-dlp](https://github.com/yt-dlp/yt-dlp) y FFmpeg (descargado automáticamente con `static-ffmpeg`).

## Características

- Descarga de video en MP4 (mejor calidad, 1080p, 720p, 480p, 360p).
- Extracción de audio en MP3, AAC, FLAC, WAV u OGG, con bitrate configurable.
- Recorte de un fragmento (inicio y fin) en MP4 o MP3.
- Descarga de videos de TikTok en MP4.
- Barra de progreso con velocidad y tiempo restante.

## Requisitos

- Python 3.10 o superior (con Tkinter).
- Conexión a internet (FFmpeg se descarga la primera vez que se ejecuta).

En Debian/Ubuntu/Mint, si falta Tkinter o venv:

```bash
sudo apt install python3-tk python3-venv binutils
```

## Ejecutar desde el código fuente

```bash
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py
```

## Compilar un ejecutable

### Linux

```bash
./iniciar.sh
```

Genera la carpeta `dist-linux/YTDownloader/` y crea automáticamente un acceso directo con icono en el menú de aplicaciones y en el escritorio.

### Windows

1. Ejecuta `icono.bat` para generar `icon\logo.ico` a partir de `icon\logo.png` (solo si cambias el logo).
2. Ejecuta `compilar.bat`.

El resultado queda en `dist\YTDownloader\YTDownloader.exe`.

> El ejecutable es una **carpeta**: hay que copiarla o comprimirla completa, no solo el binario.

## Estructura del proyecto

| Archivo | Descripción |
|---|---|
| `manage.py` | Punto de entrada. |
| `visual.py` | Interfaz gráfica. |
| `youtube.py` | Lógica de descarga de YouTube y recorte. |
| `tiktok.py` | Lógica de descarga de TikTok. |
| `iniciar.sh` | Compilación en Linux. |
| `compilar.bat` / `icono.bat` | Compilación y generación de icono en Windows. |
| `icon/` | Logo de la aplicación. |

## Aviso

Descarga solo contenido del que tengas derechos o permiso para hacerlo y respeta los términos de servicio de cada plataforma.
