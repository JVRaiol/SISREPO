from repository.database import Database


class OperadoresRepository():

    def __init__(self, instancia_database):

        self.db = instancia_database
        self.cursor = self.db.cursor
    
    def buscar_todos_os_dados(self):

        self.cursor.execute("SELECT * FROM operadoresRepografia")

        return self.cursor.fetchall()

    
    def buscar_operador_por_filtro(self, nome=None, matricula=None, data=None, turno=None, cargo=None, parcial=False):

        condicoes = []
        valores = []

        if nome:
            if parcial:
                condicoes.append("nomeCompleto ILIKE %s")
                valores.append(f"%{nome}%")
            else:
                condicoes.append("nomeCompleto = %s")
                valores.append(nome)

        if matricula:
            condicoes.append("matricula = %s")
            valores.append(matricula)

        if data:
            condicoes.append("dataNascimento= %s")
            valores.append(data)

        if turno:
            condicoes.append("turnoLotado = %s")
            valores.append(turno)

        if cargo:
            condicoes.append("cargoOuFuncao = %s")
            valores.append(cargo)

        if not condicoes:
            return self.buscar_todos_os_dados()

        where = " AND ".join(condicoes)
        query = f"SELECT * FROM operadoresRepografia WHERE {where} ORDER BY nomeCompleto"

        self.cursor.execute(query, valores)
        return self.cursor.fetchall()

    def criar_novo_operador(self, dados: dict):

        colunas = ", ".join(dados.keys())  #os dados em dicionario chegam como "campo: valor", aqui estamos pegando só os nomes dos campos (que devem ser os mesmos nomes das colunas)
        porcento_s_para_cada_campo = ", ".join(["%s"] * len(dados))  #um %s (placeholder) pra cada campo, na mesma quantidade de dados que chegam no dicionario e ainda adicionar uma virgula entre cada %s
        valores = list(dados.values())  #os dados em dicionario chegam como "campo: valor", aqui estamos pegando só os valores dos campos

        query = f"INSERT INTO operadoresRepografia ({colunas}) VALUES ({porcento_s_para_cada_campo})"  #aqui a query vai pegar os nomes dos campos(que são e devem ser os mesmos nomes das tabeelas) e colocar os %s no lugar dos valores, igual quando escrevemos um insert normal no formato INSERT INTO tabela (campo1, campo2) VALUES (%s, %s)
        self.cursor.execute(query, valores) # aqui vai ser executada a query e substituir os %s pelos valores que são enviados no dicionario, esses valores
        self.db.salvar()

    def validar_operador(self, nome_completo, num_matricula, data_nascimento):

        validado = True
        invalidado = False
   
        dados = self.buscar_operador_por_filtro(nome=nome_completo, matricula = num_matricula, data = data_nascimento)

        # lista com alguma linha: achou um operador com esse nome e essa data de nascimento
        if dados:
            return validado
        
        return invalidado

    
    def deletar_operador(self, id, matricula_acesso=None):

        self.cursor.execute("DELETE FROM operadoresRepografia WHERE id = %s", (id,))

        if matricula_acesso is not None:
            self.cursor.execute("DELETE FROM usuariosInformacoes WHERE matricula = %s", (matricula_acesso,))

        self.db.salvar()

    
    def cadastrar_operador_com_acesso(self, nome, data_nascimento, cargo, turno, matricula, nome_usuario, senha):

        try:
            self.cursor.execute(
                "INSERT INTO operadoresRepografia (nomeCompleto, dataNascimento, cargoOuFuncao, turnoLotado, matricula) VALUES (%s, %s, %s, %s, %s)",
                (nome, data_nascimento, cargo, turno, matricula),
            )

            self.cursor.execute(
                "INSERT INTO usuariosInformacoes (nome, matricula, nomeUsuario, turno, senha) VALUES (%s, %s, %s, %s, %s)",
                (nome, int(matricula), nome_usuario, turno, senha),
            )

            self.db.salvar()

        except Exception:
            self.db.conexao.rollback()
            raise

    
    def usuario_de_acesso_existe(self, matricula_acesso, nome_usuario):

        self.cursor.execute(
            "SELECT id FROM usuariosInformacoes WHERE matricula = %s OR nomeUsuario = %s",
            (matricula_acesso, nome_usuario),
        )

        return self.cursor.fetchone() is not None



    