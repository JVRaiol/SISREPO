from repository.registros_promo_repository import RegistrosPromoRepository
from repository.operadores_repository import OperadoresRepository
from repository.equipamentos_repository import EquipamentosRepository
from repository.valores_repository import valoresRepository
from repository.relatorio_repository import RelatorioRepository
from repository.registros_loguin_repository import RegistrosLoguinRepository
from repository.registros_pix_repository import RegistrosPixRepository
from repository.usuarios_informacoes_repository import usuariosInformacoesRepository
from repository.auditoria_repository import AuditoriaRepository
from repository.storage_repository import StorageRepository


class DatabaseService():

    def __init__(self, instancia_database):

        self.registros_promo_repository = RegistrosPromoRepository(instancia_database)
        self.operadores_repository = OperadoresRepository(instancia_database)
        self.equipamentos_repository = EquipamentosRepository(instancia_database)
        self.valores_repository = valoresRepository(instancia_database)
        self.relatorio_repository = RelatorioRepository(instancia_database)
        self.registros_loguin_repository = RegistrosLoguinRepository(instancia_database)
        self.registros_pix_repository = RegistrosPixRepository(instancia_database)
        self.usuarios_informacoes_repository = usuariosInformacoesRepository(instancia_database)
        self.auditoria_repository = AuditoriaRepository(instancia_database)
        self.storage_repository = StorageRepository(instancia_database)

        self.storage_repository.arquivos_publicos()