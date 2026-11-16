from repository.database import Database

class RegistrosLoguinRepository():

    def __init__(self, instancia_database):

        self.db = instancia_database
        self.cursor = self.db.cursor
    
    def buscar_todos_os_dados(self):

        self.cursor.execute("SELECT * FROM registrosLoguin")

        return self.cursor.fetchall()
    
    def buscar_registro_por_filtro(self, data_inicio=None, data_fim=None, acao=None):

        condicoes = []  # vai guardar cada pedaço, tipo "nome = %s"
        valores = []    # vai guardar os valores correspondentes, na mesma ordem


        if data_inicio and data_fim:
            condicoes.append("dataHora >= %s AND dataHora < %s::date + INTERVAL '1 day'")
            valores.append(data_inicio)
            valores.append(data_fim)

       
        if acao is not None:
            condicoes.append("acao = %s")
            valores.append(acao)


        if not condicoes:
            return self.buscar_todos_os_dados()

        where = " AND ".join(condicoes)
        query = f"SELECT * FROM registrosLoguin WHERE {where}"

        self.cursor.execute(query, valores)
        return self.cursor.fetchall()

    def criar_novo_registro_loguin(self, dados: dict):

        # as chaves do dicionário devem ter o mesmo nome das colunas: nomeOperador, turno, matriculaOperador, acao
        colunas = ", ".join(dados.keys())
        porcento_s_para_cada_campo = ", ".join(["%s"] * len(dados))
        valores = list(dados.values())

        query = f"INSERT INTO registrosLoguin ({colunas}) VALUES ({porcento_s_para_cada_campo})"
        self.cursor.execute(query, valores)
        self.db.conexao.commit()