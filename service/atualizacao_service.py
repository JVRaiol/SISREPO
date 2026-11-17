
import requests
import hashlib
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from vesion import VERSAO_ATUAL


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