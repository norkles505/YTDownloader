"""
Punto de entrada de YT Downloader.
Instala dependencias si faltan y lanza la interfaz (visual.py).
"""
import sys
import os
import subprocess

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

from visual import App

if __name__ == "__main__":
    app = App()
    app.mainloop()
