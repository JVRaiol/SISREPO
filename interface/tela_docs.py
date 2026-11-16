from kivy.properties import BooleanProperty, DictProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from interface.caixa_de_mensagem import mensagem_sucesso, mensagem_aviso, mensagem_erro, mensagem_confirmacao
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from interface.widgets import BotaoPadrao, LinhaCampo, LinhaCentralizada, LinhaDivisoriaSessao, RotuloCampo, TituloSecao
import os
import tempfile
import pyautogui
from kivy.clock import Clock



class TelaDocs(BoxLayout):

    controller = None
    conteudo_tela = None
    mostrar_seta = BooleanProperty(False)
    

    def buscar_documentos_publicos(self):

        arquivos =self.controller.consultar_arquivos_publicos()

        relatorios = self.controller.consultar_ultimos_10_relatorios()

        self.montar_lista_storage(arquivos)
        self.montar_lista_relatorios(relatorios)

    
    def montar_lista_storage(self, arquivos):

        self.ids.lista_docs.data = [{"nome": nome} for nome in arquivos[:15]]
        self.ids.painel_azul_docs.vazio = not arquivos


    def montar_lista_relatorios(self, relatorios):
        self.ids.lista_relatorios.data = [ { "data": f"Dia {relatorio["data"][:10]}", "turno": relatorio['turno'], "texto_id": f"id {relatorio['id']}","relatorio_id": relatorio["id"],} for relatorio in relatorios]


    def baixar_arquivo(self, nome):

        destino = self.destino_download(nome)

        if not destino:
            return

        try:
            self.controller.baixar_arquivo(nome, destino)

        except Exception as erro:
            print(erro)
            mensagem_erro("Docs", "Não foi possível baixar o arquivo.\nTente novamente.")
            return

        mensagem_sucesso("Docs", f"Arquivo salvo em:\n{destino}")
    
    def ver(self, data, turno, relatorio_id=None):

        painel_cinza = self.ids.painel_cinza_docs

        if self.conteudo_tela is None:

            self.conteudo_tela = list(reversed(painel_cinza.ids.conteudo.children))

        try:
            dados = self.controller.consultar_relatorios_por_data_e_turno(data, turno)
        except ValueError as erro:
            mensagem_aviso("Docs", str(erro))
            return

        if relatorio_id:
            dados = [relatorio for relatorio in dados if relatorio["id"] == relatorio_id]

        if not dados:
            mensagem_aviso("Docs", "Nenhum relatório encontrado.")
            return

        painel_cinza.clear_widgets()

        Clock.schedule_once(lambda dt: setattr(self, "mostrar_seta", True), 0)

        reais = lambda valor: f"R$ {valor:.2f}".replace(".", ",")

        for relatorio in dados:

            promo_qtd = {}

            for promo in relatorio["registros_promocoes"]:
                promo_qtd[promo["produto"]] = promo_qtd.get(promo["produto"], 0) + promo["quantidade"]

            secoes = [
                (f"Relatório do dia {relatorio['data']}", [
                    ("Operador:", relatorio["operador"]),
                    ("Turno:", relatorio["turno"]),
                ]),
                ("Cópias", [
                    ("Quantidade:", relatorio["copias"]),
                    ("Perdidas:", relatorio["perdidas_copias"]),
                    ("Contabilizadas no dia:", relatorio["copias_contabilizadas_no_dia"]),
                    ("Em promoção:", promo_qtd.get("Cópias", 0)),
                    ("Vendidas normais:", max(relatorio["copias_contabilizadas_no_dia"] - promo_qtd.get("Cópias", 0), 0)),
                    ("Total:", reais(relatorio["total_real_copias"])),
                ]),
                ("Impressões", [
                    ("Quantidade:", relatorio["impressoes"]),
                    ("Perdidas:", relatorio["perdidas_impressoes"]),
                    ("Contabilizadas no dia:", relatorio["impressoes_contabilizadas_no_dia"]),
                    ("Em promoção:", promo_qtd.get("Impressão", 0)),
                    ("Vendidas normais:", max(relatorio["impressoes_contabilizadas_no_dia"] - promo_qtd.get("Impressão", 0), 0)),
                    ("Total:", reais(relatorio["total_real_impressoes"])),
                ]),
                ("Digitalização", [
                    ("Quantidade:", relatorio["digitalizacao"]),
                    ("Perdidas:", relatorio["perdidas_digitalizacao"]),
                    ("Contabilizadas no dia:", relatorio["digitalizacao_contabilizadas_no_dia"]),
                    ("Em promoção:", promo_qtd.get("Digitalização", 0)),
                    ("Vendidas normais:", max(relatorio["digitalizacao_contabilizadas_no_dia"] - promo_qtd.get("Digitalização", 0), 0)),
                    ("Total:", reais(relatorio["total_real_digitalizacao"])),
                ]),
                ("Encadernação", [
                    ("Quantidade:", relatorio["encadernacao"]),
                    ("Em promoção:", promo_qtd.get("Encadernação", 0)),
                    ("Total:", reais(relatorio["total_real_encadernacao"])),
                ]),
                ("Pix", [(f"{pix['nome']}:", reais(pix["valor"])) for pix in relatorio["registros_pix"]]
                        + [("Total pix:", reais(relatorio["total_pix"]))]),

                ("Promoções", [
                    (f"{promo['produto']}:", f"{promo['quantidade']} un. × {reais(promo['valor_unidade'])} = {reais(promo['valor_total'])}")
                    for promo in relatorio["registros_promocoes"]
                ] + [("Total promoções:", reais(relatorio["total_promocoes"]))]),                
               
            ]

            for titulo, linhas in secoes:

                painel_cinza.add_widget(LinhaDivisoriaSessao())
                painel_cinza.add_widget(TituloSecao(text=titulo))

                for rotulo, valor in linhas:
                    linha = LinhaCampo(rotulo=rotulo, largura_rotulo=190)
                    linha.add_widget(RotuloCampo(text=str(valor)))
                    painel_cinza.add_widget(linha)

            if relatorio["observacoes"]:
                painel_cinza.add_widget(LinhaDivisoriaSessao())
                painel_cinza.add_widget(TituloSecao(text="Observações"))
                painel_cinza.add_widget(RotuloCampo(text=relatorio["observacoes"], size_hint_y=None, height="60dp", valign="top"))

            painel_cinza.add_widget(LinhaDivisoriaSessao())

            linha_imprimir = LinhaCentralizada()
            linha_imprimir.add_widget(BotaoPadrao(text="Imprimir PDF", on_release=lambda *_, r=relatorio: self.imprimir_relatorio(r)))
            painel_cinza.add_widget(linha_imprimir)

        
    def restaurar_painel_cinza(self):

        if self.conteudo_tela is None:
            return

        painel_cinza = self.ids.painel_cinza_docs
        painel_cinza.clear_widgets()

        for widget in self.conteudo_tela:
            painel_cinza.add_widget(widget)

        Clock.schedule_once(lambda dt: setattr(self, "mostrar_seta", False), 0)

    
    def destino_download(self, nome):

       
        janela = tk.Tk()
        janela.withdraw()
        janela.attributes("-topmost", True)

        caminho = filedialog.asksaveasfilename(
            parent=janela,
            title="Salvar arquivo",
            initialdir=str(Path.home() / "Downloads"),
            initialfile=nome,
            defaultextension=Path(nome).suffix,
        )

        janela.destroy()

        return caminho

    def imprimir_arquivo(self, nome):

        caminho = Path(tempfile.mkdtemp()) / nome

        try:
            self.controller.baixar_arquivo(nome, str(caminho))
            os.startfile(caminho)
        except Exception as erro:
            print(erro)
            mensagem_erro("Docs", "Não foi possível abrir o arquivo para impressão.")
            return

        Clock.schedule_once(lambda dt: pyautogui.hotkey("ctrl", "p"), 3)

    def imprimir_relatorio(self, relatorio):

        caminho = Path(tempfile.mkdtemp()) / f"relatorio_{relatorio['id']}_{relatorio['turno']}.pdf"

        try:
            self.controller.gerar_pdf_relatorio(relatorio, caminho)
            os.startfile(caminho)
        except Exception as erro:
            print(erro)
            mensagem_erro("Docs", "Não foi possível abrir o relatório para impressão.")
            return

        Clock.schedule_once(lambda dt: pyautogui.hotkey("ctrl", "p"), 3)