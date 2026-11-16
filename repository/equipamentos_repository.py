from repository.database import Database

class EquipamentosRepository():

    def __init__(self, instancia_database):

        self.db = instancia_database
        self.cursor = self.db.cursor
    
    def buscar_todos_os_dados(self):

        self.cursor.execute("SELECT * FROM equipamentosInformacoes ORDER BY id")

        return self.cursor.fetchall()

    
    def buscar_equipamento_por_filtro(self, dados: dict):

        #se a funcao for chama sem nenhum filtro, ela vai retornar todos os dados da tabela
        if not dados:
            return self.buscar_todos_os_dados()

        #A depender de quantos filtros forem passados no dicionario, será mantado uma lista de %s para cada um
        porcentos_s = []

        #busca vai ser cada chave do dicionario, e cada busca vai ter um %s no comando do banco
        for busca in dados.keys():
            porcentos_s.append(f"{busca} = %s")

        #os valores do docinario serão guardados nessa lista
        valores = list(dados.values())

        #se houver mais de um filtro na lista porcentos_s, vai ser adicionado um AND entre cada filtro a mais
        where = " AND ".join(porcentos_s)

        comando = f"SELECT * FROM equipamentosInformacoes WHERE {where}"

        self.cursor.execute(comando, valores)
        return self.cursor.fetchall()
    

    def cadastrar_novo_equipamento(self, dados: dict):

        colunas = ", ".join(dados.keys())  #os dados em dicionario chegam como "campo: valor", aqui estamos pegando só os nomes dos campos (que devem ser os mesmos nomes das tabelas)
        porcento_s_para_cada_campo = ", ".join(["%s"] * len(dados))  #um %s (placeholder) pra cada campo, na mesma quantidade de dados que chegam no dicionario e ainda adicionar uma virgula entre cada %s
        valores = list(dados.values())  #os dados em dicionario chegam como "campo: valor", aqui estamos pegando só os valores dos campos

        query = f"INSERT INTO equipamentosInformacoes ({colunas}) VALUES ({porcento_s_para_cada_campo})"  #aqui a query vai pegar os nomes dos campos(que são e devem ser os mesmos nomes das tabeelas) e colocar os %s no lugar dos valores, igual quando escrevemos um insert normal no formato INSERT INTO tabela (campo1, campo2) VALUES (%s, %s)
        self.cursor.execute(query, valores) # aqui vai ser executada a query e substituir os %s pelos valores que são enviados no dicionario, esses valores
        self.db.salvar()


    def equipamento_pausado_ou_ativo(self, id, pausado):

        comando = "UPDATE equipamentosInformacoes SET pausado = %s WHERE id = %s"
        self.cursor.execute(comando, (pausado, id))
        self.db.salvar()


    def deletar_equipamento(self, id):
        comando = "DELETE FROM equipamentosInformacoes WHERE id = %s"
        self.cursor.execute(comando, (id,))
        self.db.salvar()

    def atualizar_equipamento(self, id, dados: dict):

        colunas = ", ".join([f"{coluna} = %s" for coluna in dados.keys()])

        valores = list(dados.values())
        valores.append(id)  #adiciona o id no final da lista de valores para ser usado no WHERE

        comando = f"UPDATE equipamentosInformacoes SET {colunas} WHERE id = %s"
        self.cursor.execute(comando, valores)

        self.db.salvar()

    def atualizar_totais(self, totais: list):

        #totais é uma lista de tuplas (id, totalCopias, totalImpressoes, totalDigitalizacao), todos os equipamentos são atualizados juntos: ou salva tudo ou nada
        comando = "UPDATE equipamentosInformacoes SET totalCopias = %s, totalImpressoes = %s, totalDigitalizacao = %s WHERE id = %s"

        try:
            for id, copias, impressoes, digitalizacoes in totais:
                self.cursor.execute(comando, (copias, impressoes, digitalizacoes, id))

            self.db.salvar()

        except Exception:
            self.db.conexao.rollback()
            raise