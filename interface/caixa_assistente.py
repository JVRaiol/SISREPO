from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.popup import Popup


class CaixaAssistente(Popup):
    # caixa de confirmação das ações do assistente: avisa quando o operador confirma OU cancela

    texto = StringProperty('')
    texto_botao = StringProperty('Confirmar')
    critico = BooleanProperty(False)
    ao_confirmar = ObjectProperty(None, allownone=True)
    ao_cancelar = ObjectProperty(None, allownone=True)

    _decidido = False

    def confirmar(self):

        self._decidido = True
        self.dismiss()

        if self.ao_confirmar:
            self.ao_confirmar()

    def cancelar(self):

        self.dismiss()

    def fechar_sem_decisao(self):

        # usado quando o tempo esgota: fecha a caixa sem chamar nenhuma das duas ações
        self._decidido = True
        self.dismiss()

    def on_dismiss(self):

        if not self._decidido:
            self._decidido = True

            if self.ao_cancelar:
                self.ao_cancelar()


def abrir_confirmacao_assistente(texto, ao_confirmar, ao_cancelar, critico=False, texto_botao="Confirmar"):

    caixa = CaixaAssistente(
        title="Confirmar ação do assistente",
        texto=texto,
        texto_botao=texto_botao,
        critico=critico,
        ao_confirmar=ao_confirmar,
        ao_cancelar=ao_cancelar,
    )
    caixa.open()

    return caixa