from main import criar_service
from interface.tela_principal import TelaPrincipal
from service.atualizacao_service import AtualizacaoService


def simular_atualizacao(self):

    return {
        "versao": "1.0.1",
        "url_release": "https://github.com/JVRaiol/SISREPO/releases",
        "url_download": "",
        "digest": None
    }


AtualizacaoService.verificar_atualizacao = simular_atualizacao


if __name__ == "__main__":
    TelaPrincipal(criar_service).run()