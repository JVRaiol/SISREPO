# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.building.datastruct import Tree
from kivy.tools.packaging.pyinstaller_hooks import (
    get_deps_minimal,
    hookspath,
    runtime_hooks as kivy_runtime_hooks,
)
from kivy_deps import sdl2, glew

ROOT = Path(SPECPATH).resolve()

# Dependências específicas do Kivy.
# O SISREPO não utiliza áudio ou vídeo do Kivy no código atualmente auditado.
kivy_dependencies = get_deps_minimal(audio=None, video=None)

# O SISREPO utiliza tkinter.filedialog em interface/tela_docs.py.
# O hook alternativo do Kivy normalmente exclui tkinter, então removemos essa exclusão.
kivy_dependencies["excludes"] = [
    module
    for module in kivy_dependencies.get("excludes", [])
    if module not in {"tkinter", "_tkinter"}
]

# O pywebview será empacotado futuramente como um executável auxiliar separado.
# Na primeira compilação, o SISREPO usará o navegador padrão como alternativa.
excludes = sorted(set(kivy_dependencies.get("excludes", []) + ["webview"]))

app_data = [
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "fonts"), "fonts"),
]

analysis = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=kivy_dependencies.get("binaries", []),
    datas=app_data,
    hiddenimports=kivy_dependencies.get("hiddenimports", []),
    hookspath=hookspath(),
    hooksconfig={},
    runtime_hooks=[str(ROOT / "rthook_sisrepo.py"), *kivy_runtime_hooks()],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="SISREPO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ROOT / "templates" / "logobpav.ico"),
)

collection = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    *[Tree(path) for path in (sdl2.dep_bins + glew.dep_bins)],
    strip=False,
    upx=False,
    upx_exclude=[],
    name="SISREPO",
)
