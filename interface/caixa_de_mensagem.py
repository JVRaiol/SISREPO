from interface.widgets import CaixaConfirmacao, CaixaMensagem


def mensagem_sucesso(titulo, texto):
    CaixaMensagem(title=titulo, texto=texto, tipo="sucesso").open()


def mensagem_aviso(titulo, texto):
    CaixaMensagem(title=titulo, texto=texto, tipo="aviso").open()


def mensagem_erro(titulo, texto):
    CaixaMensagem(title=titulo, texto=texto, tipo="erro").open()


def mensagem_confirmacao(titulo, texto, ao_confirmar, texto_botao="Confirmar"):
    CaixaConfirmacao(title=titulo, texto=texto, ao_confirmar=ao_confirmar, texto_botao=texto_botao).open()