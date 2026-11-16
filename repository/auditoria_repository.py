class AuditoriaRepository():

    def __init__(self, instancia_database):

        self.db = instancia_database
        self.cursor = self.db.cursor

        self.criar_tabela()

    def criar_tabela(self):

        # histórico de tudo que o assistente tentou gravar: o que pediu, se o operador confirmou e o que aconteceu
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS auditoriaIA (
                id SERIAL PRIMARY KEY,
                dataEHora TIMESTAMP DEFAULT NOW(),
                operadorResponsavel TEXT,
                turno TEXT,
                ferramenta TEXT,
                argumentos TEXT,
                descricao TEXT,
                confirmado BOOLEAN,
                resultado TEXT
            )
        """)
        self.db.conexao.commit()

    def buscar_todos_os_dados(self):

        self.cursor.execute("SELECT * FROM auditoriaIA ORDER BY id DESC")

        return self.cursor.fetchall()

    def registrar(self, operador, turno, ferramenta, argumentos, descricao, confirmado, resultado):

        dados = {
            "operadorResponsavel": operador,
            "turno": turno,
            "ferramenta": ferramenta,
            "argumentos": argumentos,
            "descricao": descricao,
            "confirmado": confirmado,
            "resultado": resultado,
        }

        colunas = ", ".join(dados.keys())
        porcento_s_para_cada_campo = ", ".join(["%s"] * len(dados))

        query = f"INSERT INTO auditoriaIA ({colunas}) VALUES ({porcento_s_para_cada_campo})"

        try:
            self.cursor.execute(query, list(dados.values()))
            self.db.conexao.commit()
        except Exception:
            # sem o rollback a conexão fica travada e as próximas consultas do sistema também falhariam
            self.db.conexao.rollback()
            raise