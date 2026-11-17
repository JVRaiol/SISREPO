from interface.abrir_janela_web import abrir_janela_web

from kivy.clock import Clock
from kivy.properties import DictProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from interface.caixa_de_mensagem import mensagem_sucesso, mensagem_aviso, mensagem_erro, mensagem_confirmacao



def formatar_numero(numero):
    return f"{int(numero or 0):,}".replace(",", ".")


def normalizar_url(endereco):
    # aceita o endereço como foi cadastrado: "192.168.0.10" vira "http://192.168.0.10"
    endereco = (endereco or "").strip()

    if endereco and "://" not in endereco:
        endereco = "http://" + endereco

    return endereco


class TelaEquipamentos(BoxLayout):

    controller = None
    pagina = StringProperty('vazio')

    
    equipamento_exibido = DictProperty({
        "equipamento_id": 0, "nome": "", "pausado": False,
        "copia": False, "imprime": False, "scaneia": False,
        "total_copias": "", "total_impressoes": "", "total_digitalizacoes": "",
        "copias": "", "impressoes": "", "digitalizacoes": "",
        "painel_controle": "",
    })

    def carregar_lista_equipamentos(self):

        try:
            equipamentos = self.controller.listar_equipamentos()
        except Exception as erro:
            print(erro)
            mensagem_erro("Equipamentos", "Não foi possível carregar os equipamentos.\nTente novamente.")
            return

        self.ids.lista.data = [
            {
                "equipamento_id": equipamento_id,
                "nome": informacoes["nome"],
                "pausado": bool(informacoes["pausado"]),
            }
            for equipamento_id, informacoes in equipamentos.items()
        ]

    def _consultar(self, equipamento_id):

        try:
            equipamento = self.controller.consultar_equipamento(equipamento_id)

        except ValueError as erro:
            mensagem_aviso("Equipamentos", str(erro))
            return None

        except Exception as erro:
            print(erro)
            mensagem_erro("Equipamentos", "Não foi possível carregar as informações.\nTente novamente.")
            return None

        return {
            "equipamento_id": equipamento_id,
            "nome": equipamento["nome"],
            "pausado": bool(equipamento["pausado"]),
            "copia": bool(equipamento["copia"]),
            "imprime": bool(equipamento["imprime"]),
            "scaneia": bool(equipamento["scaneia"]),
            "total_copias": formatar_numero(equipamento["totalCopias"]),
            "total_impressoes": formatar_numero(equipamento["totalImpressoes"]),
            "total_digitalizacoes": formatar_numero(equipamento["totalDigitalizacao"]),
            "copias": str(equipamento["totalCopias"]),
            "impressoes": str(equipamento["totalImpressoes"]),
            "digitalizacoes": str(equipamento["totalDigitalizacao"]),
            "painel_controle": (equipamento.get("painel_controle") or "").strip(),
        }

    def ver_informacoes_equipamento(self, equipamento_id):

        exibicao = self._consultar(equipamento_id)

        if exibicao is None:
            return

        self.equipamento_exibido = exibicao
        self.pagina = 'informacoes'

    def mostrar_informacoes(self):

        # o dicionário nunca fica vazio, então verifica se há um equipamento selecionado pelo id
        if self.equipamento_exibido.get("equipamento_id"):
            self.ver_informacoes_equipamento(self.equipamento_exibido["equipamento_id"])

    def abrir_alteracao(self):

        exibicao = self._consultar(self.equipamento_exibido["equipamento_id"])

        if exibicao is None:
            return

        self.equipamento_exibido = exibicao

        ids = self.ids
        ids.edita_nome.ids.campo.text = exibicao["nome"]
        ids.edita_copias.ids.campo.text = exibicao["copias"]
        ids.edita_impressoes.ids.campo.text = exibicao["impressoes"]
        ids.edita_digitalizacoes.ids.campo.text = exibicao["digitalizacoes"]

        self.pagina = 'alterar'

        Clock.schedule_once(lambda dt: setattr(ids.edita_nome.ids.campo, "focus", True), 0.1)

    def salvar_alteracoes(self):

        ids = self.ids
        equipamento = self.equipamento_exibido

        try:
            self.controller.alterar_equipamento(
                equipamento["equipamento_id"],
                ids.edita_nome.ids.campo.text,
                ids.edita_copias.ids.campo.text if equipamento["copia"] else "0",
                ids.edita_impressoes.ids.campo.text if equipamento["imprime"] else "0",
                ids.edita_digitalizacoes.ids.campo.text if equipamento["scaneia"] else "0",
            )

        except ValueError as erro:
            mensagem_aviso("Alterar equipamento", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Alterar equipamento", "Não foi possível alterar o equipamento.\nTente novamente.")
            return

        self.carregar_lista_equipamentos()
        self.ver_informacoes_equipamento(equipamento["equipamento_id"])
        mensagem_sucesso("Alterar equipamento", "Dados do equipamento alterados com sucesso!")

    def alternar_pausa(self):

        self.alternar_pausa_equipamento(
            self.equipamento_exibido["equipamento_id"],
            self.equipamento_exibido["pausado"],
        )

    def alternar_pausa_equipamento(self, equipamento_id, pausado_atual):

        try:
            if pausado_atual:
                self.controller.ativar_equipamento(equipamento_id)
            else:
                self.controller.pausar_equipamento(equipamento_id)

        except ValueError as erro:
            mensagem_aviso("Equipamentos", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Equipamentos", "Não foi possível alterar o equipamento.\nTente novamente.")
            return

        self.carregar_lista_equipamentos()

        if self.pagina == 'informacoes' and self.equipamento_exibido.get("equipamento_id") == equipamento_id:
            self.ver_informacoes_equipamento(equipamento_id)

    def abrir_painel_controle(self):

        url = normalizar_url(self.equipamento_exibido.get("painel_controle"))

        if not url:
            mensagem_aviso("Painel de controle", "Este equipamento não tem painel de controle cadastrado.")
            return

        try:
            abrir_janela_web(url, f"Painel de controle - {self.equipamento_exibido['nome']}")

        except Exception as erro:
            print(erro)
            mensagem_erro("Painel de controle", "Não foi possível abrir o painel de controle.\nVerifique o endereço cadastrado.")

    def pedir_exclusao(self):

        self.confirmar_exclusao_equipamento(
            self.equipamento_exibido["equipamento_id"],
            self.equipamento_exibido["nome"],)

    def confirmar_exclusao_equipamento(self, equipamento_id, nome):

        mensagem_confirmacao(
            "Deletar equipamento",
            f"Tem certeza que deseja deletar o equipamento\n'{nome}'?\nEssa ação não pode ser desfeita.",
            ao_confirmar=lambda: self.deletar_equipamento(equipamento_id),
            texto_botao="Deletar",
        )

    def deletar_equipamento(self, equipamento_id):

        try:
            self.controller.deletar_equipamento(equipamento_id)

        except ValueError as erro:
            mensagem_aviso("Equipamentos", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Equipamentos", "Não foi possível deletar o equipamento.\nTente novamente.")
            return

        self.carregar_lista_equipamentos()

        if self.equipamento_exibido.get("equipamento_id") == equipamento_id:
            self.limpar_painel_informacoes()

        mensagem_sucesso("Equipamentos", "Equipamento deletado com sucesso!")

    def limpar_painel_informacoes(self):

        # volta ao dicionário padrão da property (com todas as chaves vazias), em vez de {}
        self.equipamento_exibido = dict(self.property('equipamento_exibido').defaultvalue)
        self.pagina = 'vazio'

    def cadastrar_equipamento(self):

        ids = self.ids

        try:
            self.controller.cadastrar_equipamento(
                ids.input_nome_equipamento.text,
                ids.chk_copia.active,
                ids.input_total_copias.text,
                ids.chk_imprime.active,
                ids.input_total_impressoes.text,
                ids.chk_scaneia.active,
                ids.input_total_digitalizacoes.text,
                ids.input_painel_controle.text,
            )

        except ValueError as erro:
            mensagem_aviso("Cadastro de equipamento", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Cadastro de equipamento", "Não foi possível cadastrar o equipamento.\nTente novamente.")
            return

        ids.input_nome_equipamento.text = ""
        ids.input_total_copias.text = ""
        ids.input_total_impressoes.text = ""
        ids.input_total_digitalizacoes.text = ""
        ids.input_painel_controle.text = ""
        ids.chk_copia.active = False
        ids.chk_imprime.active = False
        ids.chk_scaneia.active = False

        self.carregar_lista_equipamentos()
        mensagem_sucesso("Cadastro de equipamento", "Equipamento cadastrado com sucesso!")