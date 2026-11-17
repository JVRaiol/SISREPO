import ctypes
import sys
from pathlib import Path

import webview

if getattr(sys, "frozen", False):
    ICONE = Path(sys._MEIPASS) / "templates" / "logobpav.ico"
else:
    ICONE = Path(__file__).resolve().parent.parent / "templates" / "logobpav.ico"


def colocar_icone(titulo):

    if sys.platform != "win32" or not ICONE.exists():
        return

    user32 = ctypes.windll.user32
    user32.FindWindowW.restype = ctypes.c_void_p
    user32.LoadImageW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint, ctypes.c_int, ctypes.c_int, ctypes.c_uint]
    user32.LoadImageW.restype = ctypes.c_void_p
    user32.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_size_t, ctypes.c_void_p]

    janela = user32.FindWindowW(None, titulo)

    if not janela:
        return

    IMAGEM_ICONE, CARREGAR_DO_ARQUIVO, DEFINIR_ICONE = 1, 0x10, 0x80

    for tipo, tamanho in ((0, 16), (1, 32)):
        icone = user32.LoadImageW(None, str(ICONE), IMAGEM_ICONE, tamanho, tamanho, CARREGAR_DO_ARQUIVO)
        user32.SendMessageW(janela, DEFINIR_ICONE, tipo, icone)


def main():

    url = sys.argv[1]
    titulo = sys.argv[2] if len(sys.argv) > 2 else "Painel de controle"

    webview.settings["IGNORE_SSL_ERRORS"] = True

    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("SISREPO.PainelDeControle")

    janela = webview.create_window(titulo, url, width=1100, height=760, on_top=True)

    janela.events.shown += lambda: colocar_icone(titulo)

    webview.start()


if __name__ == "__main__":
    main()