from repository.database import Database

class RegistrosPromoRepository():

    def __init__(self, instancia_database):

        self.db = instancia_database
        self.cursor = self.db.cursor
    
    def buscar_todos_os_dados(self):

        self.cursor.execute("SELECT * FROM registrosPromocoes")

        return self.cursor.fetchall()
    
    def buscar_registro_por_filtro(self, dataInicio=None, dataFim=None):

        condicoes = []  # vai guardar cada pedaço, tipo "nome = %s"
        valores = []    # vai guardar os valores correspondentes, na mesma ordem

        if dataInicio and dataFim:
            condicoes.append("dataEHora >= %s AND dataEHora < %s::date + INTERVAL '1 day'")
            valores.append(dataInicio)
            valores.append(dataFim)
        if not condicoes:
            return self.buscar_todos_os_dados()

        where = " AND ".join(condicoes)
        query = f"SELECT * FROM registrosPromocoes WHERE {where}"

        self.cursor.execute(query, valores)
        return self.cursor.fetchall()

    def buscar_registro_por_operador_data_e_turno(self, data, operador, turno):

        dataOperacao = data
        operadorResponsavel = operador
        turnoOperacao = turno

        query = "SELECT * FROM registrosPromocoes WHERE dataEHora >= %s AND dataEHora < %s::date + INTERVAL '1 day' AND operadorResponsavel = %s AND turno = %s"  

        self.cursor.execute(query, (dataOperacao, dataOperacao, operadorResponsavel, turnoOperacao))  # a data entra duas vezes porque a query tem dois %s de data
        return self.cursor.fetchall()

    def criar_novo_registro_promo(self, dados: dict):

        colunas = ", ".join(dados.keys())  #os dados em dicionario chegam como "campo: valor", aqui estamos pegando só os nomes dos campos (que devem ser os mesmos nomes das colunas)
        porcento_s_para_cada_campo = ", ".join(["%s"] * len(dados))  #um %s (placeholder) pra cada campo, na mesma quantidade de dados que chegam no dicionario e ainda adicionar uma virgula entre cada %s
        valores = list(dados.values())  #os dados em dicionario chegam como "campo: valor", aqui estamos pegando só os valores dos campos

        query = f"INSERT INTO registrosPromocoes ({colunas}) VALUES ({porcento_s_para_cada_campo})"  #aqui a query vai pegar os nomes dos campos(que são e devem ser os mesmos nomes das colunas) e colocar os %s no lugar dos valores, igual quando escrevemos um insert normal no formato INSERT INTO tabela (campo1, campo2) VALUES (%s, %s)
        self.cursor.execute(query, valores) # aqui vai ser executada a query e substituir os %s pelos valores que são enviados no dicionario, esses valores
        self.db.conexao.commit()

    
