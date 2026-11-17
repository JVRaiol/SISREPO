import subprocess
import sys
import webbrowser
from importlib.util import find_spec
from pathlib import Path


def abrir_janela_web(url, titulo="Painel de controle"):
    #Abre o painel em uma janela pywebview, inclusive na versão empacotada.

    if getattr(sys, "frozen", False):
        executavel_web = Path(sys.executable).resolve().parent / "SISREPO_WebView.exe"

        if executavel_web.is_file():
            subprocess.Popen([str(executavel_web), url, titulo])
        else:
            webbrowser.open(url)

        return

    janela_web = Path(__file__).resolve().parent / "janela_web.py"

    if find_spec("webview") is not None:
        subprocess.Popen([sys.executable, str(janela_web), url, titulo])
    else:
        webbrowser.open(url)
