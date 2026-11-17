"""Preparação dos caminhos do SISREPO quando executado pelo PyInstaller."""

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # Carrega as credenciais externas, sem incluí-las no executável.
    pasta_dados = Path(os.environ.get("APPDATA", str(Path.home()))) / "SISREPO"
    arquivo_env = pasta_dados / ".env"

    if arquivo_env.is_file():
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=arquivo_env, override=False)

    # O projeto usa caminhos relativos para carregar arquivos KV e recursos.
    # No modo onedir, os arquivos incluídos ficam em sys._MEIPASS.
    os.chdir(sys._MEIPASS)
