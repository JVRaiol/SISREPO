from decimal import Decimal, InvalidOperation


class ValoresController:

    def __init__(self, widgets, service):

        self.widgets = widgets
        self.service = service

    def consultar_valores(self):

        dados = self.service.consultar_valores()

        return dados

    def alterar_valor(self, produto, valor):

        produto = produto.strip()

        
        produtos_validos = [item["produto"] for item in self.service.consultar_valores()]

        if produto not in produtos_validos:
            raise ValueError("Escolha um produto para prosseguir com a alteração de valor.")

        try:
            valor = Decimal(valor.strip().replace(",", "."))

        except InvalidOperation:
            raise ValueError("Digite um valor válido para prosseguir com a alteração.")

        if not valor.is_finite() or valor <= 0:
            raise ValueError("O valor deve ser maior que zero para alteração.")

        self.service.alterar_valores(produto, valor)