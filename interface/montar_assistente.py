from kivy.clock import Clock

from controller.chat_controller import ChatController
from controller.equipamentos_controller import EquipamentosController
from controller.janela_principal_controller import janelaPrincipalController
from controller.relatorio_controller import RelatorioController
from controller.valores_controller import ValoresController
from interface.caixa_assistente import abrir_confirmacao_assistente
from interface.tela_relatorio import abrir_arquivo, escolher_destino_pdf
from service.agente_executor import ExecutorFerramentas
from service.agente_ferramentas import Ferramentas
from service.agente_service import AgenteService, criar_cliente


def criar_chat_controller(tela_chat, janela_service, equipamentos_service, relatorio_service, valores_service, auditoria_repository):
    """Monta o assistente inteiro e devolve o controller que a tela de chat usa."""

    # os controllers das telas já validam e convertem os dados, então o assistente passa por eles (None = sem tela)
    janela = janelaPrincipalController(None, janela_service)
    equipamentos = EquipamentosController(None, equipamentos_service)
    valores = ValoresController(None, valores_service)
    relatorio = RelatorioController(None, relatorio_service, janela_service)

    ferramentas = Ferramentas(janela, equipamentos, valores, relatorio, janela_service, abrir_arquivo=abrir_arquivo, escolher_destino=escolher_destino_pdf).todas()

    def dados_turno():
        dados = janela_service.consultar_dados_operador_logado()

        if dados is None:
            return "ninguém logado", ""

        return dados["nome"], dados["turnoTrabalhado"]

    def agendar_na_tela(funcao):
        Clock.schedule_once(lambda dt: funcao(), 0)

    executor = ExecutorFerramentas(ferramentas, auditoria_repository, dados_turno, agendar_na_tela, abrir_confirmacao_assistente)

    cliente, motivo = criar_cliente(ferramentas)

    agente = AgenteService(cliente, executor, dados_turno, motivo)

    return ChatController(tela_chat, agente)