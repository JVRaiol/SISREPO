class ValoresService:

    def __init__(self, database_service):
        self.valores_repository = database_service.valores_repository

    def consultar_valores(self):
        
        valores = self.valores_repository.buscar_todos_os_dados()
        dados = [] 

        for item in valores:

            nome = item[1]
            valor_produto = item[2]

            dados.append( {"produto": nome, "valor": valor_produto} )

        return dados

    def alterar_valores(self, produto, valor):

        self.valores_repository.alterar_valor_produto(produto, valor)

