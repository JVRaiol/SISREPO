from kivy.config import Config

Config.set('kivy', 'window_icon', 'templates/logobpav.jpg') #aqui no topo, pois evita aparecer o icone do kivy no inicio, nem que seja por alguns segundos

from repository.database import Database
from service.database_service import DatabaseService
from service.janela_principal_service import JanelaPrincipalService
from service.equipamentos_service import EquipamentosService
from service.operadores_service import OperadoresService
from service.relatorio_service import RelatorioService
from service.valores_service import ValoresService
from service.storage_service import StorageService
from interface.tela_principal import TelaPrincipal



def criar_service(ao_progredir):
    #roda em segundo plano, enquanto a tela de carregamento aparece
    # ao_progredir(porcentagem, mensagem) atualiza a barra de progresso

    # instancia da classe construtora do banco de dados (conexao e cursor que vao para os repositories)
    
    database_instance = Database(ao_progredir)

    # repassa o database para todos os repositories do projeto
    ao_progredir(90, "Carregando repositórios...")
    
    repasse_database = DatabaseService(database_instance)

    # service da janela principal
    janela_principal_service = JanelaPrincipalService(repasse_database, operador_responsavel="jvrai")
    #service da janela de equipamentos
    equipamentos_service = EquipamentosService(repasse_database)
    operadores_service = OperadoresService(repasse_database)
    relatorio_service = RelatorioService(repasse_database)
    valores_service = ValoresService(repasse_database)
    storage_service = StorageService(repasse_database)
    auditoria_repository = repasse_database.auditoria_repository

    ao_progredir(100, "Pronto!")
    return janela_principal_service, equipamentos_service, operadores_service, relatorio_service, valores_service, auditoria_repository, storage_service


if __name__ == "__main__":

    # a tela recebe a função que monta o service e chama ela depois que a janela abrir
    TelaPrincipal(criar_service).run()