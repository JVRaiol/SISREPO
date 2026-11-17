
import requests
import hashlib
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from vesion import VERSAO_ATUAL
import subprocess
import sys
import textwrap



SCRIPT_POWERSHELL = r"""
param(
    [int]$ProcessIdSISREPO,
    [string]$SetupPath,
    [string]$InstallDir,
    [string]$AppExePath,
    [string]$SetupLog
)

$ErrorActionPreference = "Stop"

try {

    # Aguarda o encerramento completo do SISREPO
    $limite = (Get-Date).AddSeconds(120)

    while (Get-Process -Id $ProcessIdSISREPO -ErrorAction SilentlyContinue) {

        if ((Get-Date) -gt $limite) {
            throw "O SISREPO não encerrou dentro do tempo esperado."
        }

        Start-Sleep -Milliseconds 500
    }

    # Confere se o instalador ainda existe
    if (-not (Test-Path -LiteralPath $SetupPath -PathType Leaf)) {
        throw "O instalador não foi encontrado."
    }

    # Executa a instalação no mesmo diretório do programa atual
    $argumentosSetup = @(
        "/SILENT",
        "/NORESTART",
        "/SP-",
        ('/DIR="{0}"' -f $InstallDir),
        ('/LOG="{0}"' -f $SetupLog)
    )

    $processoSetup = Start-Process `
        -FilePath $SetupPath `
        -ArgumentList $argumentosSetup `
        -Wait `
        -PassThru

    # Código zero significa instalação concluída
    if ($processoSetup.ExitCode -ne 0) {
        throw "O instalador terminou com o código $($processoSetup.ExitCode)."
    }

    # Confere se o executável foi instalado
    if (-not (Test-Path -LiteralPath $AppExePath -PathType Leaf)) {
        throw "O SISREPO.exe não foi encontrado após a instalação."
    }

    # Inicia a nova versão
    Start-Process `
        -FilePath $AppExePath `
        -WorkingDirectory $InstallDir

}
catch {

    $mensagem = (
        "Não foi possível concluir a atualização do SISREPO.`r`n`r`n" +
        $_.Exception.Message +
        "`r`n`r`nO SISREPO não foi reiniciado automaticamente. " +
        "Tente abri-lo pelo atalho. Consulte o log em:`r`n" +
        $SetupLog
    )

    try {

        Add-Type -AssemblyName System.Windows.Forms

        [System.Windows.Forms.MessageBox]::Show(
            $mensagem,
            "Atualização do SISREPO",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null

    }
    catch {
        Write-Error $mensagem
    }
}
"""

class AtualizacaoService:

    URL_API = "https://api.github.com/repos/JVRaiol/SISREPO/releases/latest"
    NOME_INSTALADOR = "SISREPO_Setup.exe"

    def __init__(self):

        self.versao_atual = VERSAO_ATUAL

    @staticmethod
    def _normalizar_versao(versao):

        versao = str(versao).strip()

        if versao.lower().startswith("v"):
            versao = versao[1:]

        partes = versao.split(".")

        if not partes or any(not parte.isdigit() for parte in partes):
            raise ValueError(f"Versão inválida: {versao}")

        return tuple(int(parte) for parte in partes)

    @classmethod
    def comparar_versoes(cls, versao_remota, versao_local):

        remota = list(cls._normalizar_versao(versao_remota))
        local = list(cls._normalizar_versao(versao_local))

        tamanho = max(len(remota), len(local))

        remota.extend([0] * (tamanho - len(remota)))
        local.extend([0] * (tamanho - len(local)))

        return remota > local

    def verificar_atualizacao(self):

        resposta = requests.get(self.URL_API, headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "SISREPO-Updater"}, timeout=10)

        # Nenhuma Release publicada ainda
        if resposta.status_code == 404:
            return None

        resposta.raise_for_status()

        release = resposta.json()

        if release.get("draft") or release.get("prerelease"):
            return None

        versao_remota = release.get("tag_name")

        if not versao_remota:
            raise ValueError("A Release não possui uma versão identificada.")

        # Compara a versão publicada com a versão instalada
        if not self.comparar_versoes(versao_remota, self.versao_atual):
            return None

        # Procura o instalador publicado na Release
        instalador = next( (asset for asset in release.get("assets", []) if asset.get("name") == self.NOME_INSTALADOR), None)

        if not instalador or not instalador.get("browser_download_url"):
            return None

        return {
            "versao": versao_remota,
            "url_release": release.get("html_url"),
            "url_download": instalador["browser_download_url"],
            "digest": instalador.get("digest"),
            "tamanho": instalador.get("size")
        }

    def baixar_instalador(self, atualizacao):

        url = atualizacao.get("url_download")
        digest = atualizacao.get("digest")
        tamanho_esperado = atualizacao.get("tamanho")

        if not url:
            raise ValueError("URL de download não encontrada.")

        # verifica se o endereço bate certinho com release oficial do Sisrepo no GitHub
        endereco = urlparse(url)

        if (
            endereco.scheme != "https"
            or endereco.hostname != "github.com"
            or not endereco.path.startswith(
                "/JVRaiol/SISREPO/releases/download/"
            )
        ):
            raise ValueError("Endereço de download não autorizado.")

        #exige o SHA-256 informado pelo GitHub
        if not digest or not digest.startswith("sha256:"):
            raise ValueError("A Release não possui SHA-256 válido.")

        hash_esperado = digest.split(":", 1)[1].lower()

        if not re.fullmatch(r"[a-f0-9]{64}", hash_esperado):
            raise ValueError("Formato de SHA-256 inválido.")

        # Diretório temporário para o instalador
        pasta_download = (
            Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
            / "SISREPO"
            / "updates"
        )

        pasta_download.mkdir(parents=True, exist_ok=True)

        caminho_instalador = pasta_download / self.NOME_INSTALADOR
        caminho_temporario = pasta_download / (
            self.NOME_INSTALADOR + ".part"
        )

        hash_calculado = hashlib.sha256()
        bytes_baixados = 0

        try:

            with requests.get(
                url,
                stream=True,
                timeout=(15, 120)
            ) as resposta:

                resposta.raise_for_status()

                with open(caminho_temporario, "wb") as arquivo:

                    for bloco in resposta.iter_content(chunk_size=1024 * 1024):

                        if bloco:

                            arquivo.write(bloco)
                            hash_calculado.update(bloco)

                            bytes_baixados += len(bloco)

            # Confere o tamanho recebido
            if (
                tamanho_esperado is not None
                and bytes_baixados != int(tamanho_esperado)
            ):
                raise ValueError("O tamanho do instalador não corresponde ao esperado.")

            # Confere a integridade do arquivo
            if hash_calculado.hexdigest().lower() != hash_esperado:
                raise ValueError("A verificação SHA-256 falhou.")

            # Só disponibiliza o arquivo depois da validação
            os.replace(caminho_temporario, caminho_instalador)

            return caminho_instalador

        except Exception:
            caminho_temporario.unlink(missing_ok=True)
            raise

    def iniciar_instalacao(self, caminho_instalador):

        if os.name != "nt":
            raise RuntimeError("A atualização automática está disponível apenas no Windows.")

        if not getattr(sys, "frozen", False):
            raise RuntimeError(
                "A instalação automática só pode ser iniciada pelo SISREPO.exe."
            )

        pasta_download = (
            Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
            / "SISREPO"
            / "updates"
        ).resolve()

        caminho_instalador = Path(caminho_instalador).resolve()

        if (
            caminho_instalador.name != self.NOME_INSTALADOR
            or caminho_instalador.parent != pasta_download
        ):
            raise ValueError("Caminho do instalador não autorizado.")

        if not caminho_instalador.is_file():
            raise FileNotFoundError("O instalador não foi encontrado.")

        # Identifica a instalação atual
        executavel = Path(sys.executable).resolve()
        pasta_instalacao = executavel.parent

        if executavel.name.lower() != "sisrepo.exe":
            raise RuntimeError("Executável principal do SISREPO não identificado.")

        # Localiza o PowerShell do Windows
        powershell = (
            Path(os.environ.get("WINDIR", r"C:\Windows"))
            / "System32"
            / "WindowsPowerShell"
            / "v1.0"
            / "powershell.exe"
        )

        if not powershell.is_file():
            raise FileNotFoundError("PowerShell não encontrado.")

        # Arquivos auxiliares da atualização
        arquivo_script = pasta_download / "instalar_atualizacao.ps1"
        arquivo_log = pasta_download / "instalacao.log"

        arquivo_script.write_text(
            textwrap.dedent(SCRIPT_POWERSHELL).lstrip(),
            encoding="utf-8-sig"
        )

        # Inicia o processo externo que aguardará o encerramento do SISREPO
        subprocess.Popen(
            [
                str(powershell),
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", str(arquivo_script),
                str(os.getpid()),
                str(caminho_instalador),
                str(pasta_instalacao),
                str(executavel),
                str(arquivo_log)
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

        return True