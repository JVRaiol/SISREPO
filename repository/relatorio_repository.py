from repository.database import Database

class RelatorioRepository():
    
    def __init__(self, instancia_database):
        
        self.db = instancia_database
        self.cursor = self.db.cursor

    def buscar_todos_os_dados(self):
        self.cursor.execute("SELECT * FROM relatorio")

        return self.cursor.fetchall()

    def buscar_relatorio_por_filtros(self, operador=None, data_inicio=None, data_fim=None):

        condicoes = []  # vai guardar cada pedaço, tipo "operadorResponsavel = %s"
        valores = []    # vai guardar os valores correspondentes, na mesma ordem

        if operador:
            condicoes.append("operadorResponsavel = %s")
            valores.append(operador)

        if data_inicio and data_fim:
            condicoes.append("data >= %s AND data < %s::date + INTERVAL '1 day'")
            valores.append(data_inicio)
            valores.append(data_fim)

        if not condicoes:
            return self.buscar_todos_os_dados()

        where = " AND ".join(condicoes)
        query = f"SELECT * FROM relatorio WHERE {where}"

        self.cursor.execute(query, valores)
        return self.cursor.fetchall()

    def gerar_novo_relatorio(self, dados: dict):

        colunas = ", ".join(dados.keys())  #os dados em dicionario chegam como "campo: valor", aqui estamos pegando só os nomes dos campos (que devem ser os mesmos nomes das colunas)
        porcento_s_para_cada_campo = ", ".join(["%s"] * len(dados))  #um %s (placeholder) pra cada campo, na mesma quantidade de dados que chegam no dicionario e ainda adicionar uma virgula entre cada %s
        valores = list(dados.values())  #os dados em dicionario chegam como "campo: valor", aqui estamos pegando só os valores dos campos

        query = f"INSERT INTO relatorio ({colunas}) VALUES ({porcento_s_para_cada_campo})"  #aqui a query vai pegar os nomes dos campos(que são e devem ser os mesmos nomes das colunas) e colocar os %s no lugar dos valores, igual quando escrevemos um insert normal no formato INSERT INTO tabela (campo1, campo2) VALUES (%s, %s)

        try:
            self.cursor.execute(query, valores) # aqui vai ser executada a query e substituir os %s pelos valores que são enviados no dicionario, esses valores
            self.db.conexao.commit()
        except Exception:
            # sem o rollback a conexão fica travada ("transaction aborted") e as próximas consultas também falhariam
            self.db.conexao.rollback()
            raise