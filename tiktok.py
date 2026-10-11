"""
Logica especifica de TikTok: vista previa (oEmbed) y descarga (yt-dlp).
"""
import json
import os
import urllib.request
import urllib.parse




def es_tiktok(url):
    return "tiktok.com" in url.lower()


def buscar_info(url):
    # TikTok tiene un endpoint oEmbed oficial y liviano que devuelve
    # titulo/autor sin tener que scrapear toda la pagina (que es lo que
    # hace yt-dlp con extract_info y lo que rompe seguido con el error
    # "Unable to extract universal data for rehydration"). Lo usamos
    # para la vista previa porque es mucho mas estable.
    endpoint = "https://www.tiktok.com/oembed?url=" + urllib.parse.quote(url, safe="")
    req = urllib.request.Request(endpoint, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return {
        "title": data.get("title", "(sin titulo)"),
        "uploader": data.get("author_name", "?"),
    }


def descargar(url, carpeta, ffmpeg_path=None, progress_hooks=None):
    import yt_dlp
    outtmpl = os.path.join(carpeta, "%(title).100s.%(ext)s")
    opts = {
        "outtmpl": outtmpl,
        "progress_hooks": progress_hooks or [],
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
        "retries": 10,
        "file_access_retries": 10,
        "fragment_retries": 10,
        "keep_fragments": False,
        "windows_filenames": True,
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
    }
    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
