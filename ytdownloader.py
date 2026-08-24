import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import subprocess
import sys
import os
import re
import time

# Al compilar con --windowed (sin consola), sys.stdout y sys.stderr quedan
# en None. Cualquier libreria que intente hacer print()/.write() ahi
# (como static_ffmpeg al mostrar progreso de descarga) revienta con
# "AttributeError: 'NoneType' object has no attribute 'write'". Les damos
# un destino valido y vacio para evitarlo.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

def instalar_si_falta(paquete, nombre_pip=None):
    try:
        __import__(paquete)
    except ImportError:
        if getattr(sys, "frozen", False):
            # Empaquetado como .exe: no se puede hacer pip install en runtime
            # (sys.executable es el propio .exe, no python.exe). Si el modulo
            # falta aca, es un problema de empaquetado (falta bundlear la
            # dependencia), no algo arreglable en tiempo de ejecucion.
            import tkinter as _tk
            from tkinter import messagebox as _mb
            _root = _tk.Tk()
            _root.withdraw()
            _mb.showerror(
                "Falta un componente",
                f"Falta el modulo '{paquete}' dentro del ejecutable.\n\n"
                "Este .exe fue compilado sin incluir esta dependencia.\n"
                "Volve a generar el .exe asegurandote de tener "
                f"'{nombre_pip or paquete}' instalado con pip en el "
                "mismo entorno de Python donde corres PyInstaller."
            )
            _root.destroy()
            sys.exit(1)
        else:
            subprocess.check_call([sys.executable, "-m", "pip", "install",
                                   nombre_pip or paquete, "--quiet"])

instalar_si_falta("yt_dlp")
instalar_si_falta("static_ffmpeg", "static-ffmpeg")

import yt_dlp
from static_ffmpeg import run as _ffmpeg_run

ERROR_FFMPEG = None  # guarda el motivo real si falla la obtencion de ffmpeg

def obtener_ffmpeg():
    global ERROR_FFMPEG
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

FFMPEG_PATH = obtener_ffmpeg()

if FFMPEG_PATH:
    # yt-dlp, al usar recortes (download_ranges), tambien verifica si
    # ffmpeg/ffprobe estan disponibles buscandolos en el PATH del sistema,
    # sin depender solo de la opcion "ffmpeg_location". Agregamos su
    # carpeta al PATH para que esa verificacion los encuentre siempre.
    _ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
    if _ffmpeg_dir not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = _ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")


class VentanaProgreso(tk.Toplevel):
    def __init__(self, parent, titulo="Descargando..."):
        super().__init__(parent)
        self.title(titulo)
        self.geometry("480x280")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)
        self._destruida = False

        BG = "#1a1a2e"; ACC = "#e94560"; FG = "#eaeaea"; GR = "#a0a0b0"

        tk.Label(self, text=titulo, font=("Segoe UI", 13, "bold"),
                 bg=BG, fg=FG).pack(pady=(22, 6))

        self.lbl_fase = tk.Label(self,
            text="Analizando video... (puede tardar unos segundos)",
            font=("Segoe UI", 10), bg=BG, fg=GR)
        self.lbl_fase.pack()

        self.barra = ttk.Progressbar(self, mode="indeterminate", maximum=100, length=400)
        self.barra.pack(pady=14)
        self.barra.start(12)

        self.lbl_pct = tk.Label(self, text="...",
                                font=("Segoe UI", 26, "bold"), bg=BG, fg=ACC)
        self.lbl_pct.pack()

        self.lbl_vel = tk.Label(self, text="", font=("Consolas", 10), bg=BG, fg=GR)
        self.lbl_vel.pack(pady=4)

        self.lbl_archivo = tk.Label(self, text="", font=("Segoe UI", 8),
                                    bg=BG, fg="#555577", wraplength=440)
        self.lbl_archivo.pack(pady=(6, 0))

    def _pasar_a_determinado(self):
        try:
            self.barra.stop()
            self.barra.config(mode="determinate", maximum=100)
            self.barra["value"] = 0
        except tk.TclError:
            pass

    def actualizar(self, pct, fase="", vel="", eta="", archivo=""):
        if self._destruida:
            return
        try:
            if self.barra["mode"] == "indeterminate":
                self._pasar_a_determinado()
            self.barra["value"] = pct
            self.lbl_pct.config(text=f"{int(pct)}%")
            if fase:
                self.lbl_fase.config(text=fase)
            linea = ""
            if vel: linea += f"Velocidad: {vel}"
            if eta: linea += f"   -   Tiempo restante: {eta}"
            self.lbl_vel.config(text=linea)
            if archivo:
                self.lbl_archivo.config(text=archivo)
            self.update_idletasks()
        except tk.TclError:
            pass

    def completado(self):
        if self._destruida:
            return
        try:
            if self.barra["mode"] == "indeterminate":
                self._pasar_a_determinado()
            self.barra["value"] = 100
            self.lbl_pct.config(text="100%")
            self.lbl_fase.config(text="Completado!")
            self.lbl_vel.config(text="")
            self.update_idletasks()
        except tk.TclError:
            pass

    def destruir_seguro(self):
        if not self._destruida:
            self._destruida = True
            try:
                self.grab_release()
                self.destroy()
            except tk.TclError:
                pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YT Downloader")
        self.geometry("700x620")
        self.minsize(700, 620)
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self.carpeta = os.path.join(os.path.expanduser("~"), "Desktop")
        self.info_video = {}
        self.vprog = None
        self._construir_ui()
        self._centrar_ventana()

    def _centrar_ventana(self):
        self.update_idletasks()
        ancho = self.winfo_width()
        alto = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

    def _construir_ui(self):
        BG="#1a1a2e"; CARD="#16213e"; ACC="#e94560"; FG="#eaeaea"; GR="#a0a0b0"
        self.BG=BG; self.CARD=CARD; self.ACC=ACC; self.FG=FG; self.GR=GR

        header = tk.Frame(self, bg=ACC, height=56)
        header.pack(fill="x"); header.pack_propagate(False)
        tk.Label(header, text="YT Downloader", font=("Segoe UI",16,"bold"),
                 bg=ACC, fg="white").pack(side="left", padx=18, pady=14)
        tk.Label(header, text="Videos - Audio - Recortes",
                 font=("Segoe UI",9), bg=ACC, fg="#ffd0d0").pack(side="left", padx=4, pady=18)

        ffmpeg_ok = FFMPEG_PATH is not None
        ffmpeg_txt = "FFmpeg incluido" if ffmpeg_ok else "FFmpeg NO encontrado"
        ffmpeg_color = "#90ee90" if ffmpeg_ok else "#ff8080"
        tk.Label(header, text=ffmpeg_txt,
                 font=("Segoe UI",8,"bold"), bg=ACC, fg=ffmpeg_color).pack(side="right", padx=14)

        url_frame = tk.Frame(self, bg=BG, pady=14)
        url_frame.pack(fill="x", padx=20)
        tk.Label(url_frame, text="Enlace de YouTube:", font=("Segoe UI",10),
                 bg=BG, fg=GR).pack(anchor="w")
        row = tk.Frame(url_frame, bg=BG)
        row.pack(fill="x", pady=4)
        self.url_var = tk.StringVar()
        entry = tk.Entry(row, textvariable=self.url_var, font=("Consolas",11),
                         bg=CARD, fg=FG, insertbackground=FG,
                         relief="flat", bd=0, highlightthickness=1,
                         highlightcolor=ACC, highlightbackground="#333355")
        entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0,8))
        entry.bind("<Return>", lambda e: self._buscar())
        self._btn(row, "Buscar", self._buscar, ACC).pack(side="left")

        info_fr = tk.Frame(self, bg=CARD, bd=0, highlightthickness=1,
                           highlightbackground="#2a2a4a")
        info_fr.pack(fill="x", padx=20, pady=(0,12))
        self.lbl_titulo = tk.Label(info_fr, text="Pega un enlace y presiona Buscar",
                                   font=("Segoe UI",10,"bold"), bg=CARD, fg=FG,
                                   wraplength=580, justify="left")
        self.lbl_titulo.pack(anchor="w", padx=14, pady=(10,2))
        self.lbl_meta = tk.Label(info_fr, text="", font=("Segoe UI",9), bg=CARD, fg=GR)
        self.lbl_meta.pack(anchor="w", padx=14, pady=(0,10))

        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0, tabmargins=0)
        style.configure("TNotebook.Tab", background="#0f3460", foreground=GR,
                        font=("Segoe UI",10), padding=[16,8], borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", CARD)], foreground=[("selected", FG)])
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="x", padx=20)

        self.tab_video   = tk.Frame(self.nb, bg=CARD)
        self.tab_audio   = tk.Frame(self.nb, bg=CARD)
        self.tab_recorte = tk.Frame(self.nb, bg=CARD)
        self.nb.add(self.tab_video,   text="Video")
        self.nb.add(self.tab_audio,   text="Solo Audio")
        self.nb.add(self.tab_recorte, text="Recortar")

        self._tab_video()
        self._tab_audio()
        self._tab_recorte()

        separador = tk.Frame(self, bg="#333355", height=1)
        separador.pack(fill="x", padx=20, pady=(10,0))

        bot = tk.Frame(self, bg=BG, pady=16)
        bot.pack(fill="x", padx=20)
        row2 = tk.Frame(bot, bg=BG)
        row2.pack(fill="x")
        tk.Label(row2, text="Guardar en:", font=("Segoe UI",9,"bold"), bg=BG, fg=GR).pack(side="left")
        self.lbl_carpeta = tk.Label(row2, text=self.carpeta,
                                    font=("Segoe UI",9), bg=BG, fg=ACC, cursor="hand2")
        self.lbl_carpeta.pack(side="left", padx=10)
        self.lbl_carpeta.bind("<Button-1>", lambda e: self._elegir_carpeta())
        self._btn(row2, "Cambiar carpeta", self._elegir_carpeta, "#0f3460").pack(side="left", ipady=6, ipadx=12)

        self.lbl_estado = tk.Label(bot, text="Esperando...",
                                   font=("Segoe UI",9), bg=BG, fg=GR)
        self.lbl_estado.pack(anchor="w", pady=(6,0))

    def _tab_video(self):
        C=self.CARD; F=self.FG; G=self.GR; A=self.ACC
        fr = self.tab_video
        tk.Label(fr, text="Calidad:", font=("Segoe UI",10), bg=C, fg=G
                 ).pack(anchor="w", padx=16, pady=(14,4))
        self.calidad_var = tk.StringVar(value="best")
        for texto, val in [("Mejor calidad disponible","best"),("1080p Full HD","1080"),
                           ("720p HD","720"),("480p","480"),("360p","360")]:
            tk.Radiobutton(fr, text=texto, variable=self.calidad_var, value=val,
                           font=("Segoe UI",10), bg=C, fg=F, selectcolor=A,
                           activebackground=C, activeforeground=F).pack(anchor="w", padx=28)
        self._btn(fr, "Descargar Video (MP4)",
                  lambda: self._descargar("video"), A).pack(pady=18, ipadx=16, ipady=6)

    def _tab_audio(self):
        C=self.CARD; F=self.FG; G=self.GR; A=self.ACC
        fr = self.tab_audio
        tk.Label(fr, text="Formato:", font=("Segoe UI",10), bg=C, fg=G
                 ).pack(anchor="w", padx=16, pady=(18,6))
        fila_fmt = tk.Frame(fr, bg=C)
        fila_fmt.pack(anchor="w", padx=28)
        self.fmt_var = tk.StringVar(value="mp3")
        for fmt in ["mp3","aac","flac","wav","ogg"]:
            tk.Radiobutton(fila_fmt, text=fmt.upper(), variable=self.fmt_var, value=fmt,
                           font=("Segoe UI",10), bg=C, fg=F, selectcolor=A,
                           activebackground=C, activeforeground=F).pack(side="left", padx=(0,18))

        tk.Label(fr, text="Calidad (kbps):", font=("Segoe UI",10), bg=C, fg=G
                 ).pack(anchor="w", padx=16, pady=(24,6))
        fila_kbps = tk.Frame(fr, bg=C)
        fila_kbps.pack(anchor="w", padx=28)
        self.bitrate_var = tk.StringVar(value="192")
        for k in ["128","192","256","320"]:
            tk.Radiobutton(fila_kbps, text=k, variable=self.bitrate_var, value=k,
                           font=("Segoe UI",10), bg=C, fg=F, selectcolor=A,
                           activebackground=C, activeforeground=F).pack(side="left", padx=(0,18))

        self._btn(fr, "Extraer y Descargar Audio",
                  lambda: self._descargar("audio"), "#1a6b8a").pack(pady=(40,18), ipadx=16, ipady=6)

    def _tab_recorte(self):
        C=self.CARD; F=self.FG; G=self.GR; A=self.ACC
        fr = self.tab_recorte

        if FFMPEG_PATH:
            tk.Label(fr,
                text="FFmpeg incluido automaticamente - listo para recortar",
                font=("Segoe UI",9), bg="#0a3d0a", fg="#90ee90").pack(fill="x", padx=16, pady=(12,8))
        else:
            tk.Label(fr,
                text="FFmpeg no encontrado - el recorte puede no funcionar",
                font=("Segoe UI",9), bg="#3d0a0a", fg="#ff9090").pack(fill="x", padx=16, pady=(12,8))
            if ERROR_FFMPEG:
                tk.Label(fr,
                    text=f"Detalle: {ERROR_FFMPEG}",
                    font=("Consolas",8), bg=C, fg="#ff9090",
                    wraplength=580, justify="left").pack(fill="x", padx=16, pady=(0,8))

        fila = tk.Frame(fr, bg=C)
        fila.pack(anchor="w", padx=16, pady=(4,0))

        tk.Label(fila, text="Inicio:", font=("Segoe UI",10), bg=C, fg=G).pack(side="left")
        self.inicio_var = tk.StringVar(value="0:00")
        tk.Entry(fila, textvariable=self.inicio_var, font=("Consolas",13),
                 bg="#0f3460", fg=F, insertbackground=F,
                 relief="flat", width=8).pack(side="left", padx=(4,16), ipady=4)

        tk.Label(fila, text="Fin:", font=("Segoe UI",10), bg=C, fg=G).pack(side="left")
        self.fin_var = tk.StringVar(value="1:00")
        tk.Entry(fila, textvariable=self.fin_var, font=("Consolas",13),
                 bg="#0f3460", fg=F, insertbackground=F,
                 relief="flat", width=8).pack(side="left", padx=(4,0), ipady=4)

        tk.Label(fr, text="Formato: hh:mm:ss o mm:ss    Ejemplo: inicio 1:30  fin 2:45",
            font=("Segoe UI",8), bg=C, fg="#666688").pack(anchor="w", padx=16, pady=(4,10))

        row = tk.Frame(fr, bg=C)
        row.pack(anchor="w", padx=16, pady=(0,4))
        tk.Label(row, text="Guardar como:", font=("Segoe UI",10), bg=C, fg=G).pack(side="left")
        self.clip_fmt_var = tk.StringVar(value="mp4")
        for fmt in ["mp4","mp3"]:
            tk.Radiobutton(row, text=fmt.upper(), variable=self.clip_fmt_var, value=fmt,
                           font=("Segoe UI",10), bg=C, fg=F, selectcolor=A,
                           activebackground=C, activeforeground=F).pack(side="left", padx=8)

        self._btn(fr, "Recortar y Descargar",
                  lambda: self._descargar("recorte"), "#3b6d11").pack(pady=14, ipadx=16, ipady=6)

    def _btn(self, parent, texto, cmd, color):
        return tk.Button(parent, text=texto, command=cmd,
                         font=("Segoe UI",10,"bold"),
                         bg=color, fg="white", activebackground=color,
                         activeforeground="white", relief="flat", cursor="hand2", bd=0)

    def _elegir_carpeta(self):
        d = filedialog.askdirectory(initialdir=self.carpeta)
        if d:
            self.carpeta = d
            self.lbl_carpeta.config(text=d)

    def _estado(self, texto):
        try:
            self.lbl_estado.config(text=texto)
            self.update_idletasks()
        except tk.TclError:
            pass

    def _buscar(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Primero pega el enlace del video.")
            return
        self._estado("Buscando informacion del video...")
        threading.Thread(target=self._buscar_hilo, args=(url,), daemon=True).start()

    def _buscar_hilo(self, url):
        try:
            opts = {"quiet":True, "no_warnings":True, "skip_download":True}
            if FFMPEG_PATH:
                opts["ffmpeg_location"] = FFMPEG_PATH
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
            self.info_video = info
            dur = info.get("duration", 0)
            m, s = divmod(int(dur), 60)
            h, m = divmod(m, 60)
            dur_str = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
            self.lbl_titulo.config(text=info.get("title","(sin titulo)"))
            self.lbl_meta.config(
                text=f"Canal: {info.get('uploader','?')}   -   Duracion: {dur_str}")
            self._estado("Video encontrado. Elige una pestana y descarga.")
        except Exception as e:
            self._estado("Error buscando el video.")
            messagebox.showerror("Error", f"No se pudo obtener info:\n{e}")

    def _descargar(self, modo):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Primero pega el enlace del video.")
            return

        if modo == "recorte":
            try:
                t0 = self._ts(self.inicio_var.get().strip())
                t1 = self._ts(self.fin_var.get().strip())
                if t1 <= t0:
                    raise ValueError
            except:
                messagebox.showerror("Error de tiempo",
                    "Los tiempos no son validos.\n\n"
                    "Ejemplos correctos:\n"
                    "  0:30  a  1:45\n"
                    "  1:05:20  a  1:08:00")
                return

        titulos = {"video":"Descargando video...","audio":"Extrayendo audio...","recorte":"Recortando..."}
        self.vprog = VentanaProgreso(self, titulos[modo])
        threading.Thread(target=self._descargar_hilo, args=(url, modo), daemon=True).start()

    def _ts(self, s):
        parts = [int(x) for x in s.split(":")]
        if len(parts) == 3: return parts[0]*3600 + parts[1]*60 + parts[2]
        if len(parts) == 2: return parts[0]*60 + parts[1]
        return int(parts[0])

    def _cerrar_progreso(self):
        if self.vprog and not self.vprog._destruida:
            self.vprog.destruir_seguro()
            self.vprog = None

    def _descargar_hilo(self, url, modo):
        try:
            os.makedirs(self.carpeta, exist_ok=True)

            fase_actual  = [0]
            pct_guardado = [0.0]

            def progreso(d):
                if not self.vprog or self.vprog._destruida:
                    return
                if d["status"] == "downloading":
                    raw = d.get("_percent_str","0%").strip()
                    num = re.sub(r"[^\d.]","", raw)
                    try:    frag_pct = min(float(num), 100.0)
                    except: frag_pct = 0.0

                    vel  = d.get("_speed_str","").strip()
                    eta  = d.get("_eta_str","").strip()
                    arch = os.path.basename(d.get("filename",""))

                    if fase_actual[0] == 0:
                        global_pct = frag_pct * 0.48
                        fase_txt = "Descargando video... (1/2)"
                    else:
                        global_pct = 48.0 + frag_pct * 0.42
                        fase_txt = "Descargando audio... (2/2)"

                    if global_pct >= pct_guardado[0]:
                        pct_guardado[0] = global_pct
                        _p=global_pct; _f=fase_txt; _v=vel; _e=eta; _a=arch
                        self.after(0, lambda p=_p,f=_f,v=_v,e=_e,a=_a:
                            self.vprog and self.vprog.actualizar(p, fase=f, vel=v, eta=e, archivo=a))

                elif d["status"] == "finished":
                    if fase_actual[0] == 0:
                        fase_actual[0] = 1
                        self.after(0, lambda: self.vprog and self.vprog.actualizar(
                            48, fase="Descargando audio... (2/2)", vel="", eta=""))
                    else:
                        self.after(0, lambda: self.vprog and self.vprog.actualizar(
                            90, fase="Fusionando con FFmpeg...", vel="", eta=""))

            outtmpl_normal  = os.path.join(self.carpeta, "%(title).100s.%(ext)s")
            outtmpl_recorte = os.path.join(self.carpeta, "%(title).100s_recorte.%(ext)s")

            base_opts = {
                "outtmpl": outtmpl_normal,
                "progress_hooks": [progreso],
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
                cal = self.calidad_var.get()
                if cal == "best":
                    fmt = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
                else:
                    fmt = (f"bestvideo[height<={cal}][ext=mp4]+bestaudio[ext=m4a]"
                           f"/best[height<={cal}][ext=mp4]/best[height<={cal}]")
                opts = {**base_opts, "format": fmt, "merge_output_format": "mp4"}

            elif modo == "audio":
                opts = {
                    **base_opts,
                    "format": "bestaudio/best",
                    "postprocessors": [{
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": self.fmt_var.get(),
                        "preferredquality": self.bitrate_var.get(),
                    }],
                }

            elif modo == "recorte":
                t0   = self._ts(self.inicio_var.get().strip())
                t1   = self._ts(self.fin_var.get().strip())
                cfmt = self.clip_fmt_var.get()

                if cfmt == "mp4":
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

            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

            time.sleep(0.5)

            if self.vprog and not self.vprog._destruida:
                self.vprog.completado()
            self.after(1000, self._cerrar_progreso)
            self.after(1100, lambda: self._estado("Descarga completada!"))
            self.after(1200, lambda: messagebox.showinfo(
                "Listo!", f"Archivo guardado en:\n{self.carpeta}"))

        except yt_dlp.utils.DownloadError as e:
            msg = str(e)
            self.after(0, self._cerrar_progreso)
            self.after(100, lambda: messagebox.showerror("Error de descarga", msg))
            self.after(0, lambda: self._estado("Error en la descarga."))

        except Exception as e:
            err = str(e)
            self.after(0, self._cerrar_progreso)
            self.after(100, lambda: messagebox.showerror("Error inesperado", err))
            self.after(0, lambda: self._estado("Ocurrio un error."))


if __name__ == "__main__":
    app = App()
    app.mainloop()
