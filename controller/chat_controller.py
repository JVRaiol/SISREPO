from threading import Thread

from kivy.clock import Clock


class ChatController():

    def __init__(self, widgets, agente):

        self.widgets = widgets
        self.agente = agente

    def enviar_mensagem(self, texto, ao_responder):

        # a conversa com a IA demora, então roda em outra thread para a janela não travar
        Thread(target=self._processar, args=(texto, ao_responder), daemon=True).start()

    def _processar(self, texto, ao_responder):

        try:
            resposta = self.agente.conversar(texto)

        except Exception as erro:
            print(erro)
            resposta = "Aconteceu um erro inesperado no assistente."

        # widgets só podem ser mexidos pela thread da tela, por isso a resposta volta por aqui
        Clock.schedule_once(lambda dt: ao_responder(resposta), 0)

    def limpar_conversa(self):

        self.agente.limpar()