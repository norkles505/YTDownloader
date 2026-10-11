"""
Logica de YouTube: vista previa, FFmpeg y descarga (video/audio/recorte).
"""
import os

ERROR_FFMPEG = None  # guarda el motivo real si falla la obtencion de ffmpeg

# FFMPEG_PATH arranca en None: se resuelve en segundo plano despues de
# mostrar la ventana (ver inicializar_ffmpeg), para no bloquear el arranque
# del exe con la busqueda/descarga de ffmpeg.
FFMPEG_PATH = None


def obtener_ffmpeg():
    global ERROR_FFMPEG
    # Import diferido: static_ffmpeg no hace falta hasta que se resuelve
    # ffmpeg, asi no suma tiempo al arranque del exe.
    from static_ffmpeg import run as _ffmpeg_run
    # static_ffmpeg trae ffmpeg Y ffprobe juntos en la misma carpeta.
    # yt-dlp necesita AMBOS binarios para poder recortar (download_ranges);
    # con solo ffmpeg (como traia imageio_ffmpeg) el recorte falla con
    # "ffmpeg is not installed" aunque ffmpeg si este presente.
    try:
        ffmpeg_path, ffprobe_path = _ffmpeg_run.get_or_fetch_platform_executables_else_raise()
        if ffmpeg_path and os.path.isfile(ffmpeg_path):
            return ffmpeg_path
    except Exception as e:
        ERROR_FFMPEG = f"{type(e).__name__}: {e}"
    for nombre in ("ffmpeg", "ffmpeg.exe"):
        for carpeta in os.environ.get("PATH", "").split(os.pathsep):
            ruta = os.path.join(carpeta, nombre)
            if os.path.isfile(ruta):
                return ruta
    return None


def inicializar_ffmpeg():
    """Busca ffmpeg/ffprobe y deja el resultado en FFMPEG_PATH.
    Pensado para llamarse desde un hilo (ver visual.py), no bloquea la UI."""
    global FFMPEG_PATH
    FFMPEG_PATH = obtener_ffmpeg()
    if FFMPEG_PATH:
        # yt-dlp, al usar recortes (download_ranges), tambien verifica si
        # ffmpeg/ffprobe estan disponibles buscandolos en el PATH del sistema,
        # sin depender solo de la opcion "ffmpeg_location". Agregamos su
        # carpeta al PATH para que esa verificacion los encuentre siempre.
        _ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
        if _ffmpeg_dir not in os.environ.get("PATH", "").split(os.pathsep):
            os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
    return FFMPEG_PATH


def buscar_info(url):
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    if FFMPEG_PATH:
        opts["ffmpeg_location"] = FFMPEG_PATH
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


def _ts(s):
    parts = [int(x) for x in s.split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return int(parts[0])


def timestamp_a_segundos(s):
    return _ts(s)


def descargar(url, modo, carpeta, progress_hooks=None,
              calidad="best", fmt="mp3", bitrate="192",
              inicio="0:00", fin="1:00", clip_fmt="mp4"):
    """
    modo: "video" | "audio" | "recorte"
    """
    import yt_dlp
    outtmpl_normal = os.path.join(carpeta, "%(title).100s.%(ext)s")
    outtmpl_recorte = os.path.join(carpeta, "%(title).100s_recorte.%(ext)s")

    base_opts = {
        "outtmpl": outtmpl_normal,
        "progress_hooks": progress_hooks or [],
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
        "retries": 10,
        "file_access_retries": 10,
        "fragment_retries": 10,
        "keep_fragments": False,
        "windows_filenames": True,
    }
    if FFMPEG_PATH:
        base_opts["ffmpeg_location"] = FFMPEG_PATH

    if modo == "video":
        if calidad == "best":
            fmt_str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
        else:
            fmt_str = (f"bestvideo[height<={calidad}][ext=mp4]+bestaudio[ext=m4a]"
                       f"/best[height<={calidad}][ext=mp4]/best[height<={calidad}]")
        opts = {**base_opts, "format": fmt_str, "merge_output_format": "mp4"}

    elif modo == "audio":
        opts = {
            **base_opts,
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": fmt,
                "preferredquality": bitrate,
            }],
        }

    elif modo == "recorte":
        t0 = _ts(inicio)
        t1 = _ts(fin)

        if clip_fmt == "mp4":
            opts = {
                **base_opts,
                "outtmpl": outtmpl_recorte,
                "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "merge_output_format": "mp4",
                "download_ranges": yt_dlp.utils.download_range_func(None, [(t0, t1)]),
                "force_keyframes_at_cuts": True,
                "postprocessor_args": {
                    "ffmpeg": ["-avoid_negative_ts", "make_zero"]
                },
            }
        else:
            opts = {
                **base_opts,
                "outtmpl": outtmpl_recorte,
                "format": "bestaudio/best",
                "download_ranges": yt_dlp.utils.download_range_func(None, [(t0, t1)]),
                "force_keyframes_at_cuts": True,
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
    else:
        raise ValueError(f"Modo desconocido: {modo}")

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
