from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget

from interface.caixa_de_mensagem import mensagem_aviso, mensagem_erro, mensagem_sucesso
from interface.widgets import LinhaValor, SeparadorPainel, TituloPainel


class TelaValores(BoxLayout):

    controller = None

    def configurar_telas(self):

        painel = self.ids.painel
        seletor_produto = self.ids.seletor_produto

        try:
            prod_e_valores = self.controller.consultar_valores()

        except Exception as e:
            print(e)
            mensagem_erro("Valores", "Não foi possível carregar os valores.")
            return

        # configurando o painel cinza
        produtos = []

        for v in prod_e_valores:

            produto = v["produto"]
            produtos.append(produto)

        seletor_produto.values = produtos

        # configurando o painel azul
        painel.clear_widgets()

        painel.vazio = not prod_e_valores

        if not prod_e_valores:
            return

        painel.add_widget(TituloPainel(text="Valores de cada produto"))
        painel.add_widget(SeparadorPainel())

        for dados in prod_e_valores:

            produto = dados["produto"]
            valor = dados["valor"]

            painel.add_widget(LinhaValor(nome=produto, valor=f"R$ {valor:.2f}"))

        painel.add_widget(Widget())

    def salvar(self):

        try:
            self.controller.alterar_valor(self.ids.seletor_produto.text, self.ids.input_valor.text)

        except ValueError as erro:
            mensagem_aviso("Valores", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Valores", "Não foi possível salvar o novo valor")
            return

        self.ids.input_valor.text = ""
        self.configurar_telas()
        mensagem_sucesso("Valores", "Valor alterado com sucesso!")