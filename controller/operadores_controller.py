
class OperadoresController:

    
    def __init__(self, widgets, service):
        self.widgets = widgets
        self.service = service

    
    def buscar_operador_por_filtro(self, nome=None, matricula=None, data=None, turno=None, cargo=None):

        operadores = self.service.buscar_operador_por_filtro(nome, matricula, data, turno, cargo)
        return operadores

    
    def deletar_operador(self, operador_id, matricula):

        self.service.deletar_operador(operador_id, matricula)

    
    def cadastrar_operador(self, nome, nome_usuario, cargo, turno, matricula, data_nascimento, senha, senha_confirmacao):

        self.service.cadastrar_operador(nome, nome_usuario, cargo, turno, matricula, data_nascimento, senha, senha_confirmacao)    