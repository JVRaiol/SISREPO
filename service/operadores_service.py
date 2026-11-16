from datetime import datetime

class OperadoresService:
 
    def __init__(self, database_service):
        self.operadores_repository = database_service.operadores_repository

    def buscar_operador_por_filtro(self, nome=None, matricula=None, data=None, turno=None, cargo=None):

        if turno == "Todos":
            turno = None

        if cargo == "Todos":
            cargo = None

        operadores = self.operadores_repository.buscar_operador_por_filtro(nome, matricula, data, turno, cargo, parcial=True)

        lista_dados = []

        for operador in operadores:

            id_operador = operador[0]
            nome_operador = operador[1]
            nascimento_operador = operador[2].strftime("%d/%m/%Y") if operador[2] else ""
            cargo_operador = operador[3] or ""
            turno_operador = operador[4] or ""
            matricula_operador = operador[5] or ""
            data_cadastro_operador = operador[6].strftime("%d/%m/%Y %H:%M") if operador[6] else ""

            lista_dados.append({
                "id": id_operador,
                "nome": nome_operador,
                "nascimento": nascimento_operador,
                "cargo": cargo_operador,
                "turno": turno_operador,
                "matricula": matricula_operador,
                "cadastro": data_cadastro_operador,
            })

        return lista_dados

    def deletar_operador(self, operador_id, matricula):

        if not operador_id:
            raise ValueError("Não foi possível deletar o operador.")

        matricula_acesso = int(matricula) if matricula and matricula.isdigit() else None

        self.operadores_repository.deletar_operador(operador_id, matricula_acesso)

    
    def cadastrar_operador(self, nome, nome_usuario, cargo, turno, matricula, data_nascimento, senha, senha_confirmacao):

        if not all([nome, nome_usuario, matricula, data_nascimento, senha]):
            raise ValueError("Preencha todos os campos para cadastrar o operador.")

        if senha != senha_confirmacao:
            raise ValueError("As senhas não coincidem.")

        if cargo in ("", "Selecione") or turno in ("", "Selecione"):
            raise ValueError("Escolha o cargo e o turno lotado do operador.")

        if not matricula.isdigit():
            raise ValueError("A matrícula deve conter apenas números.")

        try:
            nascimento = datetime.strptime(data_nascimento, "%d/%m/%Y").date()
        except ValueError:
            raise ValueError("Data de nascimento inválida.\nUse o formato DD/MM/AAAA.")

        if self.operadores_repository.buscar_operador_por_filtro(matricula=matricula):
            raise ValueError("Já existe um operador com essa matrícula.")

        if self.operadores_repository.usuario_de_acesso_existe(int(matricula), nome_usuario):
            raise ValueError("Já existe um usuário de acesso com essa matrícula ou nome de usuário.")

        self.operadores_repository.cadastrar_operador_com_acesso(nome, nascimento, cargo, turno, matricula, nome_usuario, senha)    
            
