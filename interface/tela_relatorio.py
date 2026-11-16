import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from interface.caixa_de_mensagem import mensagem_aviso, mensagem_confirmacao, mensagem_erro, mensagem_sucesso
from interface.widgets import CampoInput, LinhaCampo, LinhaDivisoriaSessao, LinhaValor, SeparadorPainel, TextoVazio, TituloPainel, TituloSecao, LinkTexto, LinhaLink


ATRASO_AVISO = 1.2


def formatar_numero(numero):
    return f"{int(numero or 0):,}".replace(",", ".")


def abrir_arquivo(caminho):
    # abre o PDF no leitor padrão do computador
    if sys.platform.startswith("win"):
        os.startfile(caminho)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(caminho)])
    else:
        subprocess.Popen(["xdg-open", str(caminho)])


def escolher_destino_pdf(nome):
    # janela do sistema para escolher onde salvar o PDF (devolve "" se o operador cancelar)
    janela = tk.Tk()
    janela.withdraw()
    janela.attributes("-topmost", True)

    caminho = filedialog.asksaveasfilename(
        parent=janela,
        title="Salvar relatório",
        initialdir=str(Path.home() / "Downloads"),
        initialfile=nome,
        defaultextension=".pdf",
        filetypes=[("PDF", "*.pdf")],
    )

    janela.destroy()

    return caminho


class TelaRelatorios(BoxLayout):

    controller = None
    entradas = []
    avisos = []
    bloqueado = False

    def carregar_equipamentos(self):

        Clock.unschedule(self.mostrar_avisos)

        ids = self.ids

        ids.container_equipamentos.clear_widgets()
        ids.input_encadernacao.text = ""
        ids.input_observacoes.text = ""
        self.entradas = []

        try:
            equipamentos = self.controller.listar_equipamentos()
        except Exception as erro:
            print(erro)
            mensagem_erro("Relatório", "Não foi possível carregar os equipamentos.\nTente novamente.")
            return

        quantidade = len(equipamentos)

        if quantidade == 0:
            ids.container_equipamentos.add_widget(TextoVazio(text="Nenhum equipamento ativo."))

        for indice in range(quantidade):

            equipamento = equipamentos[indice]

            entrada = {"nome": equipamento["nome"], "campos": {}}

            if indice > 0:
                ids.container_equipamentos.add_widget(LinhaDivisoriaSessao())

            ids.container_equipamentos.add_widget(TituloSecao(text=equipamento["nome"]))

            if equipamento["copia"]:
                self.criar_linha_produto(entrada, "Cópias", "copias", equipamento["total_copias"])

            if equipamento["imprime"]:
                self.criar_linha_produto(entrada, "Impressão", "impressoes", equipamento["total_impressoes"])

            if equipamento["scaneia"]:
                self.criar_linha_produto(entrada, "Digitalização", "digitalizacoes", equipamento["total_digitalizacoes"])

            if equipamento["painel_controle"] is not None:
                ids.container_equipamentos.add_widget(LinhaLink(rotulo = "Painel de controle", valor=equipamento["painel_controle"], cor_rotulo=[0, 0, 0, 1], cor_link=[0, 0.4, 1, 1], negrito_link=True, negrito_rotulo=True))
            
            self.entradas.append(entrada)

        self.atualizar_painel()

    def criar_linha_produto(self, entrada, produto, chave, total_atual):

        linha = LinhaCampo(rotulo=produto)

        campo_total = CampoInput(hint_text=f"Atual: {formatar_numero(total_atual)}", input_filter="int")
        campo_perdidas = CampoInput(hint_text="Perdidas", input_filter="int", size_hint_x=0.45)

        campo_total.bind(text=self.atualizar_painel)
        campo_perdidas.bind(text=self.atualizar_painel)

        linha.add_widget(campo_total)
        linha.add_widget(campo_perdidas)

        self.ids.container_equipamentos.add_widget(linha)

        entrada["campos"][chave] = campo_total
        entrada["campos"][f"perdidas {chave}"] = campo_perdidas

    def coletar_equipamentos(self):

        # lê o que foi digitado em cada equipamento; "preenchido" indica se existe qualquer campo com valor
        equipamentos = []
        preenchido = self.ids.input_encadernacao.text != ""

        for entrada in self.entradas:

            equipamento = {"nome": entrada["nome"]}

            for chave, campo in entrada["campos"].items():

                equipamento[chave] = campo.text

                if campo.text != "":
                    preenchido = True

            equipamentos.append(equipamento)

        return equipamentos, preenchido

    def confirmar_geracao(self):

        if self.controller is None:
            return

        equipamentos, preenchido = self.coletar_equipamentos()

        if not preenchido:
            mensagem_aviso("Relatório", "Preencha os totais dos equipamentos\nantes de gerar o relatório.")
            return

        if self.bloqueado:
            mensagem_aviso("Relatório", "Corrija os valores informados\nantes de gerar o relatório.")
            return

        mensagem_confirmacao(
            "Gerar relatório",
            "O relatório será salvo, o PDF será gerado e os totais\ndos equipamentos serão atualizados. Deseja continuar?",
            self.gerar_relatorio,
            "Gerar",
        )

    def gerar_relatorio(self):

        ids = self.ids
        equipamentos, preenchido = self.coletar_equipamentos()

        try:
            destino = escolher_destino_pdf(self.controller.nome_sugerido_pdf())
        except ValueError as erro:
            mensagem_aviso("Relatório", str(erro))
            return

        if not destino:
            mensagem_aviso("Relatório", "Nenhum local foi escolhido para salvar o PDF.\nO relatório não foi gerado.")
            return

        try:
            caminho = self.controller.gerar_relatorio(equipamentos, ids.input_encadernacao.text, ids.input_observacoes.text, destino)

        except ValueError as erro:
            mensagem_aviso("Relatório", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Relatório", "Não foi possível gerar o relatório.\nTente novamente.")
            return

        try:
            abrir_arquivo(caminho)
        except Exception as erro:
            # o relatório já foi salvo; só não foi possível abrir o PDF automaticamente
            print(erro)

        # recarrega a tela: os totais "Atual" já refletem o relatório gerado e os campos ficam limpos
        self.carregar_equipamentos()

        mensagem_sucesso("Relatório", f"Relatório salvo e PDF gerado!\nPDF salvo em:\n{caminho}")

    def atualizar_painel(self, *args):

        if self.controller is None:
            return

        Clock.unschedule(self.mostrar_avisos)

        ids = self.ids
        painel = ids.painel_azul

        equipamentos, preenchido = self.coletar_equipamentos()

        if not preenchido:
            painel.clear_widgets()
            painel.vazio = True
            return

        try:
            resultado = self.controller.calcular_relatorio(equipamentos, ids.input_encadernacao.text)

        except ValueError as erro:
            self.avisos = [str(erro)]
            self.bloqueado = True
            Clock.schedule_once(self.mostrar_avisos, ATRASO_AVISO)
            return

        except Exception as erro:
            print(erro)
            return

        painel.clear_widgets()
        painel.vazio = False

        painel.add_widget(TituloPainel(text="Resumo do dia"))

        data = resultado["data"].strftime("%d/%m/%Y")
        painel.add_widget(self.criar_texto(f"Operador: {resultado['operador']}  ·  Turno: {resultado['turno']}  ·  {data}"))

        chaves = {"Cópias": "copias", "Impressão": "impressoes", "Digitalização": "digitalizacoes"}

        for equipamento in resultado["equipamentos"]:

            linhas = []
            total_equipamento = 0

            for produto, chave in chaves.items():

                if equipamento[f"total {chave}"] == 0 and equipamento[f"perdidas {chave}"] == 0:
                    continue

                detalhe = f"{equipamento[f'total {chave}']} feitas"

                if equipamento[f"perdidas {chave}"]:
                    detalhe += f", {equipamento[f'perdidas {chave}']} perdidas"

                linhas.append(self.criar_linha_painel(produto, detalhe, equipamento[f"valor {chave}"]))
                total_equipamento += equipamento[f"valor {chave}"]

            if not linhas:
                continue

            bloco = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
            bloco.bind(minimum_height=bloco.setter("height"))

            bloco.add_widget(self.criar_cabecalho_painel(equipamento["nome"], total_equipamento))

            for linha in linhas:
                bloco.add_widget(linha)

            painel.add_widget(bloco)
            painel.add_widget(SeparadorPainel())

        encadernacao = resultado["resumo"]["Encadernação"]

        if encadernacao["feitas"] > 0:

            bloco = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
            bloco.bind(minimum_height=bloco.setter("height"))

            bloco.add_widget(self.criar_cabecalho_painel("Encadernação", encadernacao["vendidas normais"] * encadernacao["valor unitario"]))
            bloco.add_widget(self.criar_texto(f"{encadernacao['feitas']} feitas"))

            painel.add_widget(bloco)
            painel.add_widget(SeparadorPainel())

        promocoes = [(produto, resumo) for produto, resumo in resultado["resumo"].items() if resumo["promocoes"] > 0]

        if promocoes:

            total_promocoes = 0

            for produto, resumo in promocoes:
                total_promocoes += resumo["valor promocoes"]

            bloco = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
            bloco.bind(minimum_height=bloco.setter("height"))

            bloco.add_widget(self.criar_cabecalho_painel("Promoções", total_promocoes))

            for produto, resumo in promocoes:
                bloco.add_widget(self.criar_linha_painel(produto, f"{resumo['promocoes']} em promoção", resumo["valor promocoes"]))

            painel.add_widget(bloco)
            painel.add_widget(SeparadorPainel())

        painel.add_widget(LinhaValor(nome="Total geral", valor=f"R$ {resultado['total_geral']:.2f}"))
        painel.add_widget(LinhaValor(nome="Pix", detalhe="registrados no turno", valor=f"R$ {resultado['total pix']:.2f}"))
        painel.add_widget(LinhaValor(nome="Espécie", detalhe="total geral - pix", valor=f"R$ {resultado['total especie']:.2f}"))

        painel.add_widget(Widget())

        self.avisos = resultado["avisos"]
        self.bloqueado = False

        if self.avisos:
            Clock.schedule_once(self.mostrar_avisos, ATRASO_AVISO)

    def mostrar_avisos(self, dt):

        painel = self.ids.painel_azul

        acima = 2

        if self.bloqueado:
            painel.clear_widgets()
            painel.vazio = False
            acima = 0

        for aviso in self.avisos:
            painel.add_widget(self.criar_texto(aviso, cor=(1, 0.93, 0.55, 1), tamanho_fonte="15sp"), index=len(painel.ids.conteudo.children) - acima)
            acima += 1

    def criar_cabecalho_painel(self, titulo, valor):

        cabecalho = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        cabecalho.add_widget(self.criar_rotulo(titulo, "20sp", "left"))
        cabecalho.add_widget(self.criar_rotulo(f"R$ {valor:.2f}", "22sp", "right", negrito=True))

        return cabecalho

    def criar_linha_painel(self, produto, detalhe, valor):

        linha = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(30))

        nome = self.criar_rotulo(produto, "15sp", "left", negrito=True)
        nome.size_hint_x = 0.25

        descricao = self.criar_rotulo(detalhe, "13sp", "left", cor=(0.85, 0.93, 1, 1))
        descricao.size_hint_x = 0.5

        total = self.criar_rotulo(f"R$ {valor:.2f}", "15sp", "right", negrito=True)
        total.size_hint_x = 0.25

        linha.add_widget(nome)
        linha.add_widget(descricao)
        linha.add_widget(total)

        return linha

    def criar_texto(self, texto, cor=(0.85, 0.93, 1, 1), tamanho_fonte="14sp"):

        label = Label(text=texto, font_size=tamanho_fonte, color=cor, size_hint_y=None, halign="left", valign="top")
        label.bind(width=lambda instancia, largura: setattr(instancia, "text_size", (largura, None)))
        label.bind(texture_size=lambda instancia, tamanho: setattr(instancia, "height", tamanho[1] + dp(2)))

        return label

    def criar_rotulo(self, texto, tamanho_fonte, alinhamento, negrito=False, cor=(1, 1, 1, 1)):

        label = Label(text=texto, font_size=tamanho_fonte, bold=negrito, color=cor, halign=alinhamento, valign="middle")
        label.bind(size=lambda instancia, tamanho: setattr(instancia, "text_size", tamanho))

        return label