



class EquipamentosController():

    def __init__(self, widgets, service):

        self.service = service
        self.widgets = widgets


    def listar_equipamentos(self):

        return self.service.consultar_equipamentos_cadastrados()


    def cadastrar_equipamento(self, nome, copia, total_copias, imprime, total_impressoes, scaneia, total_digitalizacoes, painel_controle):

        nome = nome.strip()
        painel_controle = painel_controle.strip()

        
        try:
            total_copias = int(total_copias or 0) if copia else 0
            total_impressoes = int(total_impressoes or 0) if imprime else 0
            total_digitalizacoes = int(total_digitalizacoes or 0) if scaneia else 0
        except ValueError:
            raise ValueError("Digite apenas números nos totais de cópias, impressões e digitalizações.")

       
        self.service.cadastrar_novo_equipamento(nome, copia, total_copias, imprime, total_impressoes, scaneia, total_digitalizacoes, painel_controle or None,)


    def pausar_equipamento(self, id):

        self.service.pausar_equipamento(id)


    def ativar_equipamento(self, id):

        self.service.ativar_equipamento(id)


    def deletar_equipamento(self, id):

        self.service.deletar_equipamento(id)

    
    def consultar_equipamento(self, id):
        
        return self.service.consultar_equipamento_por_id(id)


    def alterar_equipamento(self, id, nome, total_copias, total_impressoes, total_digitalizacao):

        nome = nome.strip()

        try:
            total_copias = int(total_copias or 0)
            total_impressoes = int(total_impressoes or 0)
            total_digitalizacao = int(total_digitalizacao or 0)
        except ValueError:
            raise ValueError("Digite apenas números nos totais de cópias, impressões e digitalizações.")

        self.service.alterar_dados_equipamento(id, nome, total_copias, total_impressoes, total_digitalizacao)