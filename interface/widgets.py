import glob

from kivy.animation import Animation
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, NumericProperty, ObjectProperty, StringProperty, ListProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
import weakref
from kivy.properties import ListProperty, NumericProperty
from interface.abrir_janela_web import abrir_janela_web

from kivy.properties import ListProperty


class HoverBehavior:
    hovered = BooleanProperty(False)
    hover_permanente = False

    def __init__(self, **kwargs):
        self._ja_esteve_na_janela = False
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def _descartavel(self):
        # pop-ups e menus suspensos são recriados a cada uso, então podem soltar o vínculo quando fecham.
        # as telas ficam guardadas para quando o usuário voltar a elas, então seus widgets mantêm o vínculo.
        no = self

        while no.parent is not None:
            no = no.parent

        return no is self or isinstance(no, (Popup, DropDown))

    def on_mouse_pos(self, janela, pos):
        if not self.get_root_window():
            self.hovered = False
            if self._ja_esteve_na_janela and not self.hover_permanente and self._descartavel():
                Window.unbind(mouse_pos=self.on_mouse_pos)
            return

        self._ja_esteve_na_janela = True
        dentro = self.collide_point(*self.to_widget(*pos))
        if self.hovered != dentro:
            self.hovered = dentro

class CabecalhoSlides(FloatLayout):
    fontes = ListProperty([])
    intervalo = NumericProperty(8)
    duracao = NumericProperty(1.5)

    # estado compartilhado entre todas as telas (uma instância por tela)
    _indice_global = 0
    _instancias = weakref.WeakSet()
    _timer = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._indice = 0
        self._imagens = []
        Clock.schedule_once(self._montar)

    def _montar(self, *args):
        if not self.fontes:
            return

        # a tela nova já nasce mostrando a imagem que está valendo agora
        self._indice = CabecalhoSlides._indice_global % len(self.fontes)

        for i, src in enumerate(self.fontes):
            img = Image(source=src, fit_mode='fill',
                        opacity=1 if i == self._indice else 0,
                        size_hint=(1, 1), pos_hint={'x': 0, 'y': 0})
            self._imagens.append(img)
            self.add_widget(img)

        CabecalhoSlides._instancias.add(self)

        # um único timer para o app inteiro, criado pela primeira tela
        if CabecalhoSlides._timer is None and len(self.fontes) > 1:
            CabecalhoSlides._timer = Clock.schedule_interval(
                CabecalhoSlides._avancar, self.intervalo)

    @staticmethod
    def _avancar(dt):
        # avança o índice global e manda todos os cabeçalhos existentes transicionarem
        CabecalhoSlides._indice_global += 1
        for instancia in list(CabecalhoSlides._instancias):
            instancia._transicionar()

    def _transicionar(self):
        if len(self._imagens) < 2:
            return

        atual = self._imagens[self._indice]
        self._indice = CabecalhoSlides._indice_global % len(self._imagens)
        proxima = self._imagens[self._indice]

        # coloca a próxima por cima, começando transparente
        self.remove_widget(proxima)
        self.add_widget(proxima)
        proxima.opacity = 0

        # só a próxima anima; a atual fica opaca por baixo até o fim
        anim = Animation(opacity=1, duration=self.duracao, t='in_out_quad')
        anim.bind(on_complete=lambda *args: setattr(atual, 'opacity', 0))
        anim.start(proxima)

class IgnoraToqueOculto:
    # widgets "escondidos" (altura 0 ou opacidade 0) continuam na tela, e seus filhos, que ultrapassam a área do pai,
    # interceptavam os cliques dos botões vizinhos (um widget desabilitado "engole" o toque). Aqui eles simplesmente ignoram o toque.

    def _oculto(self):
        return self.height <= 0 or self.opacity <= 0

    def on_touch_down(self, touch):
        if self._oculto():
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._oculto():
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._oculto():
            return False
        return super().on_touch_up(touch)


class ConteudoDelegado:
    conteudo_id = 'conteudo'

    def add_widget(self, widget, *args, **kwargs):
        if self.conteudo_id not in self.ids:
            return super().add_widget(widget, *args, **kwargs)
        return self.ids[self.conteudo_id].add_widget(widget, *args, **kwargs)

    def clear_widgets(self, children=None):
        if self.conteudo_id not in self.ids:
            return super().clear_widgets(children)
        return self.ids[self.conteudo_id].clear_widgets(children)


class BarraDecorativaAzul(BoxLayout):
    rotulo = StringProperty('')
    largura_rotulo = NumericProperty(130)


class BarraProgresso(Widget):
    valor = NumericProperty(0)


class BolhaMensagem(FloatLayout):
    texto = StringProperty('')
    autor = StringProperty('ia')
    largura_texto = NumericProperty(0)

    def on_texto(self, instancia, valor):
        # largura natural do texto (linha mais larga), para o balão não ocupar sempre o máximo
        medidor = CoreLabel(font_size=sp(15))
        self.largura_texto = max((medidor.get_extents(linha or ' ')[0] for linha in valor.split('\n')), default=0) + dp(4)


class BotaoAzulEscuro(Button):
    pass


class BotaoCasinha(HoverBehavior, ButtonBehavior, Widget):
    hover_permanente = True


class BotaoOlho(ButtonBehavior, Widget):
    aberto = BooleanProperty(False)


class BotaoVer(HoverBehavior, ButtonBehavior, Widget):
    pass


class BotaoPadrao(HoverBehavior, Button):
    pass


class BotaoPainel(HoverBehavior, Button):
    pass


class BotaoPerigo(BotaoPainel):
    pass


class BotaoTresPontinhos(HoverBehavior, ButtonBehavior, Widget):
    pass

class BotaoDownload(HoverBehavior, ButtonBehavior, Widget):
    pass

class BotaoImprimir(HoverBehavior, ButtonBehavior, Widget):
    pass

class Cabecalho(BoxLayout):
    pass


class CaixaConfirmacao(Popup):
    texto = StringProperty('')
    texto_botao = StringProperty('Confirmar')
    ao_confirmar = ObjectProperty(None, allownone=True)

    def confirmar(self):
        self.dismiss()

        if self.ao_confirmar:
            self.ao_confirmar()


class CaixaMensagem(Popup):
    texto = StringProperty('')
    tipo = StringProperty('aviso')
    

class PopupAtualizacao(Popup):
    valor = NumericProperty(0)
    status = StringProperty('Preparando download...')


class CampoInput(TextInput):
    pass


class CampoLoguin(TextInput):
    pass


class CartaoLoguin(BoxLayout):
    ativo = BooleanProperty(False)


class ImageButtonMenu(HoverBehavior, ButtonBehavior, Image):
    hover_permanente = True
    brilho = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(hovered=self._on_hover)

    def _on_hover(self, instance, value):
        Animation.cancel_all(self, 'brilho')
        Animation(brilho=1 if value else 0, duration=0.15, t='out_quad').start(self)


class ItemMenu(BoxLayout):
    icone = StringProperty('')
    texto = StringProperty('')
    expandido = BooleanProperty(False)
    progresso = NumericProperty(0)

    __events__ = ('on_release',)

    def on_release(self):
        pass


class ItemMenuOpcao(HoverBehavior, Button):
    pass


class ItemMenuPerigo(ItemMenuOpcao):
    pass


class LinhaBotoes(IgnoraToqueOculto, BoxLayout):
    pass


class LinhaCampo(IgnoraToqueOculto, BoxLayout):
    rotulo = StringProperty('')
    largura_rotulo = NumericProperty(110)


class LinhaCentralizada(ConteudoDelegado, BoxLayout):
    conteudo_id = 'meio'


class LinhaDivisoriaSessao(BoxLayout):
    pass


class LinhaEdicao(IgnoraToqueOculto, BoxLayout):
    rotulo = StringProperty('')
    valor = StringProperty('')
    numerico = BooleanProperty(False)


class LinhaEquipamento(BoxLayout):
    equipamento_id = NumericProperty(0)
    nome = StringProperty('')
    pausado = BooleanProperty(False)

    def abrir_menu(self, botao):
        menu = MenuEquipamento(
            equipamento_id=self.equipamento_id,
            nome=self.nome,
            pausado=self.pausado,
        )
        menu.open(botao)


class LinhaInformacao(IgnoraToqueOculto, BoxLayout):
    rotulo = StringProperty('')
    valor = StringProperty('')


class LinhaLink(IgnoraToqueOculto, BoxLayout):

    rotulo = StringProperty('')
    valor = StringProperty('')

    cor_rotulo = ListProperty([])
    cor_link = ListProperty([])

    font_rotulo = StringProperty('14sp')
    negrito_rotulo = BooleanProperty(True)

    font_link = StringProperty('16sp')
    negrito_link = BooleanProperty(True)

    __events__ = ('on_abrir',)

    def on_abrir(self):

        url = (self.valor or '').strip()

        if not url:
            return

        if '://' not in url:
            url = 'http://' + url

        try:
            abrir_janela_web(url, "Painel de controle")

        except Exception as erro:
            print(f"Erro ao abrir painel de controle: {erro}")

class LinhaArquivosStorage(BoxLayout):
    nome = StringProperty('')

    def baixar(self):
        tela = App.get_running_app().tela_docs
        tela.baixar_arquivo(self.nome)

    def imprimir(self):
        tela = App.get_running_app().tela_docs
        tela.imprimir_arquivo(self.nome)

class LinhaRelatorios(BoxLayout):
    data = StringProperty('')
    turno = StringProperty('')
    texto_id = StringProperty('')
    relatorio_id = NumericProperty(0)

    def ver(self):
        tela = App.get_running_app().tela_docs
        tela.ver(self.data[4:], self.turno, self.relatorio_id)

class LinhaOperador(BoxLayout):
    operador_id = NumericProperty(0)
    nome = StringProperty('')

    def abrir_menu(self, botao):
        menu = MenuOperador(operador_id=self.operador_id)
        menu.open(botao)


class LinhaValor(BoxLayout):
    nome = StringProperty('')
    detalhe = StringProperty('')
    valor = StringProperty('R$ 0.00')


class LinkPainel(HoverBehavior, ButtonBehavior, Label):
    pass


class LinkTexto(ButtonBehavior, Label):
    pass


class ListaEquipamentos(RecycleView):
    pass


class ListaOperadores(RecycleView):
    pass

class ListaDocs(RecycleView):
    pass

class ListaRelatorios(RecycleView):
    pass


class MenuEquipamento(DropDown):
    equipamento_id = NumericProperty(0)
    nome = StringProperty('')
    pausado = BooleanProperty(False)

    acao_pendente = None

    def ver_informacoes(self):
        tela = App.get_running_app().tela_equipamentos
        self._escolher(lambda: tela.ver_informacoes_equipamento(self.equipamento_id))

    def alternar_pausa(self):
        tela = App.get_running_app().tela_equipamentos
        self._escolher(lambda: tela.alternar_pausa_equipamento(self.equipamento_id, self.pausado))

    def deletar(self):
        tela = App.get_running_app().tela_equipamentos
        self._escolher(lambda: tela.confirmar_exclusao_equipamento(self.equipamento_id, self.nome))

    def _escolher(self, acao):
        self.acao_pendente = acao
        self.dismiss()

    def on_dismiss(self):
        acao = self.acao_pendente
        self.acao_pendente = None

        if acao:
            Clock.schedule_once(lambda dt: acao(), 0)


class MenuLateral(HoverBehavior, BoxLayout):
    hover_permanente = True
    progresso = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(hovered=self._animar_abertura)

    def _animar_abertura(self, instance, value):
        Animation.cancel_all(self, 'progresso')
        Animation(progresso=1 if value else 0, duration=0.22, t='out_cubic').start(self)


class MenuOperador(DropDown):
    operador_id = NumericProperty(0)

    acao_pendente = None

    def mais_informacoes(self):
        tela = App.get_running_app().tela_operadores
        self._escolher(lambda: tela.ver_informacoes_operador(self.operador_id))

    def _escolher(self, acao):
        self.acao_pendente = acao
        self.dismiss()

    def on_dismiss(self):
        acao = self.acao_pendente
        self.acao_pendente = None

        if acao:
            Clock.schedule_once(lambda dt: acao(), 0)


class OpcaoPagamento(BoxLayout):
    ativo = BooleanProperty(False)


class OpcaoSeletor(HoverBehavior, SpinnerOption):
    hover_permanente = True


class PaginaPainel(IgnoraToqueOculto, BoxLayout):
    pass


class PainelAzul(ConteudoDelegado, FloatLayout):
    vazio = BooleanProperty(False)


class PainelCinza(ConteudoDelegado, ScrollView):
    pass


class RotuloCampo(Label):
    pass


class SeletorFiltro(Spinner):
    pass


class SeparadorPainel(Widget):
    pass


class TelaLoguin(FloatLayout):
    tela_atual = StringProperty('loguin')


class TextoClicavel(ButtonBehavior, Label):
    pass


class TextoVazio(Label):
    pass


class TituloPainel(Label):
    pass


class TituloSecao(Label):
    pass


def carregar_componentes():
    for arquivo in sorted(glob.glob("templates/widgets/*.kv")):
        Builder.load_file(arquivo)