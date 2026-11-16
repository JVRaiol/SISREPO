from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout

from interface.widgets import BolhaMensagem


MENSAGEM_BOAS_VINDAS = "Olá! Sou o Arthur, assiste de IA da Repografia, você precisa de alguma ajuda?"


class TelaChat(BoxLayout):

    controller = None
    aguardando = False

    def ao_abrir(self):

        if not self.ids.lista_mensagens.children:
            self.adicionar_mensagem(MENSAGEM_BOAS_VINDAS, "ia")

        self.ids.input_mensagem.focus = True

    def adicionar_mensagem(self, texto, autor):

        self.ids.lista_mensagens.add_widget(BolhaMensagem(texto=texto, autor=autor))

        Clock.schedule_once(self._rolar_para_baixo, 0.05)

    def _rolar_para_baixo(self, dt):

        self.ids.scroll.scroll_y = 0

    def enviar(self):

        if self.aguardando:
            return

        texto = self.ids.input_mensagem.text.strip()

        if not texto:
            return

        self.ids.input_mensagem.text = ""
        self.adicionar_mensagem(texto, "usuario")

        if self.controller is None:
            self.adicionar_mensagem("A IA ainda não está conectada.", "ia")
            self.ids.input_mensagem.focus = True
            return

        self.definir_aguardando(True)
        self.controller.enviar_mensagem(texto, self.receber_resposta)

    def receber_resposta(self, texto):

        self.definir_aguardando(False)
        self.adicionar_mensagem(texto, "ia")

    def definir_aguardando(self, aguardando):

        self.aguardando = aguardando

        self.ids.lbl_status.text = "O assistente está pensando..." if aguardando else ""
        self.ids.btn_enviar.disabled = aguardando
        self.ids.input_mensagem.disabled = aguardando

        if not aguardando:
            self.ids.input_mensagem.focus = True

    def nova_conversa(self):

        if self.aguardando:
            return

        self.ids.lista_mensagens.clear_widgets()

        if self.controller is not None:
            self.controller.limpar_conversa()

        self.ao_abrir()