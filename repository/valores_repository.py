from repository.database import Database

class valoresRepository():

    def __init__(self, instancia_database):

        self.db = instancia_database
        self.cursor = self.db.cursor
    
    def buscar_todos_os_dados(self):

        self.cursor.execute("SELECT * FROM valoresProdut")

        return self.cursor.fetchall()
    
    def buscar_valor_por_produto(self, produto):

        self.cursor.execute("SELECT * FROM valoresProdut WHERE produto = %s", (produto,))

        return self.cursor.fetchone()
    
    def alterar_valor_produto(self, produto, novo_valor):

        self.cursor.execute("UPDATE valoresProdut SET valor = %s WHERE produto = %s", (novo_valor, produto))
        self.db.conexao.commit()