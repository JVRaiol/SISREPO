# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH).resolve()

# Reúne módulos, dados e binários do pywebview.
webview_datas, webview_binaries, webview_hiddenimports = collect_all("webview")

# O backend Windows do pywebview utiliza pythonnet/.NET.
# O módulo `clr` é carregado dinamicamente pelo pythonnet.
clr_hiddenimports = collect_submodules("clr_loader")

hiddenimports = sorted(set(webview_hiddenimports + clr_hiddenimports + ["clr"]))

datas = webview_datas + [
    (str(ROOT / "templates" / "logobpav.ico"), "templates"),
]

analysis = Analysis(
    [str(ROOT / "interface" / "janela_web.py")],
    pathex=[str(ROOT)],
    binaries=webview_binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PyQt5", "PyQt6", "PySide2", "PySide6", "cefpython3"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

# Primeiro build com console habilitado para facilitar o diagnóstico.
# Depois dos testes, podemos mudar console=True para console=False.
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="SISREPO_WebView",
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "templates" / "logobpav.ico"),
)
