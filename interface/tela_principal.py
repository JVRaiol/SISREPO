from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from threading import Thread
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.effectwidget import EffectWidget, HorizontalBlurEffect, VerticalBlurEffect
from controller.janela_principal_controller import janelaPrincipalController
from controller.equipamentos_controller import EquipamentosController
from interface.caixa_de_mensagem import mensagem_sucesso, mensagem_aviso, mensagem_erro, mensagem_confirmacao
from interface import widgets
from interface.widgets import LinhaValor
from interface.tela_relatorio import TelaRelatorios
from interface.tela_equipamentos import TelaEquipamentos
from interface.tela_operadores import TelaOperadores
from controller.operadores_controller import OperadoresController
from controller.relatorio_controller import RelatorioController
from controller.relatorio_controller import RelatorioController
from interface.tela_relatorio import TelaRelatorios
from interface.tela_valores import TelaValores
from interface.tela_chat import TelaChat
from controller.valores_controller import ValoresController
from interface.montar_assistente import criar_chat_controller
from interface.tela_docs import TelaDocs
from controller.storage_controller import StorageController
import webbrowser
from service.atualizacao_service import AtualizacaoService


class TelaPrincipal(App):

    escala_texto = NumericProperty(1.0)

    def __init__(self, criar_service, **kwargs):
        super().__init__(**kwargs)

        self.icon = "templates/logobpav.jpg"
        self.title = "SISREPO"

        self.criar_service = criar_service
        self.service = None
        self.controller = None
        self.camada_desfoque = None
        self.tela_loguin = None
        self.matricula_recuperacao = None
        self.tela_principal = None

        self.tela_equipamentos = None
        self.equipamentos_service = None

        self.tela_operadores = None
        self.operadores_service = None

        self.relatorio_service = None
        self.tela_relatorios = None

        self.valores_service = None
        self.tela_valores = None

        self.tela_chat = None
        self.auditoria_repository = None

        self.tela_docs = None
        self.storage_service = None

        self.total_produtos = 0
        self.total_promocoes = 0

        self.atualizacao_verificada = False
        self.atualizacao_pendente = None
        self.sisrepo_pronto = False

        self.download_em_andamento = False
        self.instalador_baixado = None

    def _calcular_escala(self, *args):

        largura_painel = (Window.width - dp(80)) / 2

        escala = largura_painel / dp(560)

        self.escala_texto = max(0.6, min(1.0, escala))

    def build(self):
        Window.size = (dp(600), dp(600))

        Window.bind(width=self._calcular_escala)
        self._calcular_escala()

        widgets.carregar_componentes()

        return Builder.load_file("templates/tela_carregamento.kv")

    def on_start(self):
        self.verificar_atualizacoes()
        self.iniciar_conexao()

    def verificar_atualizacoes(self):

        if self.atualizacao_verificada:
            return

        self.atualizacao_verificada = True

        Thread(
            target=self._consultar_atualizacao,
            daemon=True
        ).start()


    def _consultar_atualizacao(self):

        try:
            service = AtualizacaoService()
            atualizacao = service.verificar_atualizacao()

        except Exception as erro:
            print(f"Não foi possível verificar atualizações: {erro}")
            return

        if atualizacao:
            Clock.schedule_once(
                lambda dt, dados=atualizacao: self._receber_atualizacao(dados)
            )


    def _receber_atualizacao(self, atualizacao):

        self.atualizacao_pendente = atualizacao

        if self.sisrepo_pronto:
            self._mostrar_popup_atualizacao()


    def _mostrar_popup_atualizacao(self):

        atualizacao = self.atualizacao_pendente

        if not atualizacao:
            return

        self.atualizacao_pendente = None

        mensagem_confirmacao(
            "Atualização disponível",
            f"Uma nova versão ({atualizacao['versao']}) do SISREPO está disponível.\nDeseja fazer o download agora?",
            ao_confirmar=lambda dados=atualizacao: self._iniciar_download_atualizacao(dados),
            texto_botao="Baixar"
        )

    def _iniciar_download_atualizacao(self, atualizacao):

        if self.download_em_andamento:
            return

        self.download_em_andamento = True

        Thread(
            target=self._baixar_instalador,
            args=(atualizacao,),
            daemon=True
        ).start()


    def _baixar_instalador(self, atualizacao):

        try:

            service = AtualizacaoService()
            caminho = service.baixar_instalador(atualizacao)

        except Exception as erro:

            mensagem = str(erro)

            Clock.schedule_once(
                lambda dt: self._download_falhou(mensagem)
            )

            return

        Clock.schedule_once(
            lambda dt: self._download_concluido(caminho)
        )


    def _download_falhou(self, erro):

        self.download_em_andamento = False

        print(f"Erro no download da atualização: {erro}")

        mensagem_erro(
            "Falha na atualização",
            "Não foi possível baixar ou validar o instalador.\nTente novamente mais tarde."
        )


    def _download_concluido(self, caminho):

        self.download_em_andamento = False
        self.instalador_baixado = caminho

        mensagem_sucesso(
            "Download concluído",
            "O instalador foi baixado e passou na verificação de integridade."
        )

    def iniciar_conexao(self):
        ids = self.root.ids
        ids.barra.valor = 0
        ids.lbl_status.text = "Iniciando..."
        ids.btn_tentar.opacity = 0
        ids.btn_tentar.disabled = True

        Thread(target=self._conectar, daemon=True).start()

    def _conectar(self):
        try:
            service = self.criar_service(self._progresso)
        except Exception as erro:
            Clock.schedule_once(lambda dt, e=erro: self._falhou(e))
            return

        Clock.schedule_once(lambda dt: self._conectado(service))

    def _progresso(self, porcentagem, mensagem):
        Clock.schedule_once(lambda dt: self._mostrar_progresso(porcentagem, mensagem))

    def _mostrar_progresso(self, porcentagem, mensagem):
        ids = self.root.ids
        ids.lbl_status.text = mensagem
        Animation(valor=porcentagem, duration=0.3).start(ids.barra)

    def _conectado(self, services):

        self.service, self.equipamentos_service, self.operadores_service, self.relatorio_service, self.valores_service, self.auditoria_repository, self.storage_service = services

        Clock.schedule_once(self._abrir_tela_principal, 0.6)

    def _abrir_tela_principal(self, dt):
        tela = Builder.load_file("templates/tela_principal.kv")
        self.controller = janelaPrincipalController(tela, self.service)
        self.tela_principal = tela

        Window.remove_widget(self.root)
        self.root = tela

        tela.disabled = True
        self.camada_desfoque = EffectWidget(effects=[
            HorizontalBlurEffect(size=8.0),
            VerticalBlurEffect(size=8.0),
            HorizontalBlurEffect(size=16.0),
            VerticalBlurEffect(size=16.0),
        ])
        self.camada_desfoque.add_widget(tela)

        self.tela_loguin = Builder.load_file("templates/tela_loguin.kv")

        Window.add_widget(self.camada_desfoque)
        Window.add_widget(self.tela_loguin)

        Window.minimum_width = dp(750)
        Window.minimum_height = dp(600)

        Window.maximize()

        Clock.schedule_once(self._focar_campo_loguin, 0.3)

    def _focar_campo_loguin(self, dt):
        self.tela_loguin.ids.input_loguin.focus = True

    def _falhou(self, erro):
        ids = self.root.ids
        ids.lbl_status.text = "Não foi possível conectar ao banco de dados.\nVerifique a internet e tente novamente."
        ids.btn_tentar.opacity = 1
        ids.btn_tentar.disabled = False

    def tentar_loguin(self):

        ids = self.tela_loguin.ids
        ids.lbl_erro.color = (0.80, 0.10, 0.10, 1)
        ids.lbl_erro.text = ""

        if ids.check_manha.active:
            turno = "Manhã"
        elif ids.check_tarde.active:
            turno = "Tarde"
        else:
            turno = ""

        try:
            autenticado = self.controller.autenticar_loguin(
                ids.input_loguin.text,
                ids.input_senha.text,
                turno,
            )
        except ValueError as erro:
            ids.lbl_erro.text = str(erro)
            return
        except Exception as erro:
            print(erro)
            ids.lbl_erro.text = "Erro ao consultar o banco. Tente novamente."
            return

        if not autenticado:
            ids.lbl_erro.text = "Usuário ou senha incorretos."
            ids.input_senha.text = ""
            return

        self.liberar_tela_principal()

    def liberar_tela_principal(self):

        tela = self.root

        self.camada_desfoque.remove_widget(tela)
        Window.remove_widget(self.camada_desfoque)
        Window.remove_widget(self.tela_loguin)
        Window.add_widget(tela)

        tela.disabled = False

        tela.ids.lbl_operador.text = self.controller.consultar_operador_logado()

        self.sisrepo_pronto = True
        self._mostrar_popup_atualizacao()

    def mostrar_recuperacao(self):

        ids = self.tela_loguin.ids
        ids.lbl_erro.text = ""
        ids.lbl_msg_recuperacao.text = ""

        self.tela_loguin.tela_atual = 'recuperacao'
        ids.input_rec_nome.focus = True

    def voltar_loguin(self):

        ids = self.tela_loguin.ids

        ids.input_rec_nome.text = ""
        ids.input_rec_matricula.text = ""
        ids.input_rec_data.text = ""
        ids.lbl_msg_recuperacao.text = ""
        ids.input_nova_senha.text = ""
        ids.input_confirma_senha.text = ""
        ids.lbl_msg_nova_senha.text = ""
        self.matricula_recuperacao = None

        self.tela_loguin.tela_atual = 'loguin'
        ids.input_loguin.focus = True

    def tentar_recuperar_senha(self):

        ids = self.tela_loguin.ids
        ids.lbl_msg_recuperacao.text = ""

        try:
            validado = self.controller.validar_operador(
                ids.input_rec_nome.text,
                ids.input_rec_matricula.text,
                ids.input_rec_data.text,
            )
        except ValueError as erro:
            ids.lbl_msg_recuperacao.text = str(erro)
            return
        except Exception as erro:
            print(erro)
            ids.lbl_msg_recuperacao.text = "Erro ao consultar o banco. Tente novamente."
            return

        if not validado:
            ids.lbl_msg_recuperacao.text = "Os dados não conferem. Verifique e tente novamente."
            return

        self.matricula_recuperacao = ids.input_rec_matricula.text.strip()
        ids.lbl_nome_operador.text = ids.input_rec_nome.text.strip()

        ids.input_rec_nome.text = ""
        ids.input_rec_matricula.text = ""
        ids.input_rec_data.text = ""

        self.tela_loguin.tela_atual = 'nova_senha'
        ids.input_nova_senha.focus = True

    def tentar_alterar_senha(self):

        ids = self.tela_loguin.ids
        ids.lbl_msg_nova_senha.text = ""

        try:
            alterada = self.controller.alterar_senha(
                ids.input_nova_senha.text,
                ids.input_confirma_senha.text,
                self.matricula_recuperacao or "",
            )
        except ValueError as erro:
            ids.lbl_msg_nova_senha.text = str(erro)
            return
        except Exception as erro:
            print(erro)
            ids.lbl_msg_nova_senha.text = "Erro ao salvar a senha. Tente novamente."
            return

        if not alterada:
            ids.lbl_msg_nova_senha.text = "Não existe usuário de acesso cadastrado para essa matrícula."
            return

        self.voltar_loguin()
        ids.lbl_erro.color = (0.10, 0.55, 0.20, 1)
        ids.lbl_erro.text = "Senha alterada com sucesso! Entre com a nova senha."

    def atualizar_total_atendimento(self):

        total = float(self.total_produtos) + float(self.total_promocoes)
        self.root.ids.lbl_total_geral.text = f"R$ {total:.2f}"
        
    def calcular_e_atualizar_painel(self):

        if self.controller is None:
            return

        ids = self.root.ids

        try:
            calculo = self.controller.buscar_valores(
                ids.input_copias.text,
                ids.input_impressao.text,
                ids.input_digitalizacao.text,
                ids.input_encadernacao.text,
            )
        except ValueError as erro:
            print(erro)
            return

        ids.linha_copias.valor = f"R$ {calculo.get('Cópias', 0):.2f}"
        ids.linha_impressao.valor = f"R$ {calculo.get('Impressão', 0):.2f}"
        ids.linha_digital.valor = f"R$ {calculo.get('Digitalização', 0):.2f}"
        ids.linha_encad.valor = f"R$ {calculo.get('Encadernação', 0):.2f}"

        unitarios = calculo['unitarios']
        ids.linha_copias.detalhe = f"{int(ids.input_copias.text)} x {float(unitarios['Cópias']):g}" if 'Cópias' in unitarios else ''
        ids.linha_impressao.detalhe = f"{int(ids.input_impressao.text)} x {float(unitarios['Impressão']):g}" if 'Impressão' in unitarios else ''
        ids.linha_digital.detalhe = f"{int(ids.input_digitalizacao.text)} x {float(unitarios['Digitalização']):g}" if 'Digitalização' in unitarios else ''
        ids.linha_encad.detalhe = f"{int(ids.input_encadernacao.text)} x {float(unitarios['Encadernação']):g}" if 'Encadernação' in unitarios else ''

        self.total_produtos = calculo['total']
        self.atualizar_total_atendimento()

    def registrar_pix(self):

        ids = self.root.ids

        try:
            self.controller.registrar_pix(
                ids.input_nome_pix.text,
                ids.input_valor_pix.text,
            )
        except ValueError as erro:
            print(erro)
            mensagem_aviso("Atenção", str(erro))
            return
        except Exception as erro:
            mensagem_erro("Erro", "Não foi possível registrar o Pix.\nTente novamente.")
            print(erro)
            return

        ids.input_nome_pix.text = ""
        ids.input_valor_pix.text = ""
        mensagem_sucesso("Pix registrado", "O Pix foi registrado com sucesso!")

    def registrar_promocao(self):

        ids = self.root.ids

        produtos = {
            "Cópias": "copias",
            "Impressão": "impressao",
            "Digitalização": "digitalizacao",
            "Encadernação": "encadernacao",
        }

        promocoes = {}

        for produto, nome_no_kv in produtos.items():

            if ids[f"chk_promo_{nome_no_kv}"].active:
                promocoes[produto] = (ids[f"promo_qtd_{nome_no_kv}"].text, ids[f"promo_val_{nome_no_kv}"].text)

        try:
            self.controller.registrar_promocao(promocoes)

        except ValueError as erro:
            mensagem_aviso("Registro de promoção", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Registro de promoção", "Falha ao salvar os registros de promoção.\nTente novamente.")
            return

        for nome_no_kv in produtos.values():

            ids[f"promo_qtd_{nome_no_kv}"].text = ""
            ids[f"promo_val_{nome_no_kv}"].text = ""
            ids[f"chk_promo_{nome_no_kv}"].active = False

        mensagem_sucesso("Registro de promoção", "Promoção registrada com sucesso!")

    def atualizar_promocao_painel(self):

        if self.controller is None:
            return

        ids = self.root.ids

        promocoes = {}

        if ids.chk_promo_copias.active:
            promocoes["Cópias"] = (ids.promo_qtd_copias.text, ids.promo_val_copias.text)

        if ids.chk_promo_impressao.active:
            promocoes["Impressão"] = (ids.promo_qtd_impressao.text, ids.promo_val_impressao.text)

        if ids.chk_promo_digitalizacao.active:
            promocoes["Digitalização"] = (ids.promo_qtd_digitalizacao.text, ids.promo_val_digitalizacao.text)

        if ids.chk_promo_encadernacao.active:
            promocoes["Encadernação"] = (ids.promo_qtd_encadernacao.text, ids.promo_val_encadernacao.text)

        calculo = self.controller.calcular_promocao(promocoes)

        ids.container_promocao.clear_widgets()

        total_promocao = 0

        for produto, resultado in calculo.items():

            linha = LinhaValor(
                nome=f"Promoção {produto}",
                valor=f"R$ {resultado['total']:.2f}",
            )
            ids.container_promocao.add_widget(linha)

            total_promocao += resultado["total"]

        if calculo:
            ids.lbl_total_promocao.text = f"Total das promoções: R$ {total_promocao:.2f}"
            ids.lbl_total_promocao.height = dp(36)
        else:
            ids.lbl_total_promocao.text = ""
            ids.lbl_total_promocao.height = 0

        self.total_promocoes = total_promocao
        self.atualizar_total_atendimento()

    def _trocar_tela(self, nova_tela):

        if self.root is nova_tela:
            return

        Window.remove_widget(self.root)
        Window.add_widget(nova_tela)
        self.root = nova_tela

    def voltar_tela_principal(self):

        self._trocar_tela(self.tela_principal)

    def abrir_tela_equipamentos(self):

        if self.tela_equipamentos is None:
            self.tela_equipamentos = Builder.load_file("templates/tela_equipamentos.kv")
            self.tela_equipamentos.controller = EquipamentosController(self.tela_equipamentos, self.equipamentos_service)

        self._trocar_tela(self.tela_equipamentos)

        self.tela_equipamentos.carregar_lista_equipamentos()

    def abrir_tela_operadores(self):

        if self.tela_operadores is None:
            self.tela_operadores = Builder.load_file("templates/tela_operadores.kv")
            self.tela_operadores.controller = OperadoresController(self.tela_operadores, self.operadores_service)

        self._trocar_tela(self.tela_operadores)

    def abrir_tela_relatorios(self):

        if self.tela_relatorios is None:
            self.tela_relatorios = Builder.load_file("templates/tela_relatorio.kv")
            self.tela_relatorios.controller = RelatorioController(self.tela_relatorios, self.relatorio_service, self.service)

        self._trocar_tela(self.tela_relatorios)

        self.tela_relatorios.carregar_equipamentos()

    def abrir_tela_valores(self):

        if self.tela_valores is None:
            self.tela_valores = Builder.load_file("templates/tela_valores.kv")
            self.tela_valores.controller = ValoresController(self.tela_valores, self.valores_service)

        self._trocar_tela(self.tela_valores)

        self.tela_valores.configurar_telas()

    def abrir_tela_chat(self):

        if self.tela_chat is None:
            self.tela_chat = Builder.load_file("templates/tela_chat.kv")
            self.tela_chat.controller = criar_chat_controller(
                self.tela_chat,
                self.service,
                self.equipamentos_service,
                self.relatorio_service,
                self.valores_service,
                self.auditoria_repository,
            )

        self._trocar_tela(self.tela_chat)

        self.tela_chat.ao_abrir()

    def abrir_tela_docs(self):

    
        if self.tela_docs is None:
            self.tela_docs = Builder.load_file("templates/tela_docs.kv")
            self.tela_docs.controller = StorageController(self.tela_docs, self.storage_service)

        self._trocar_tela(self.tela_docs)

        self.tela_docs.buscar_documentos_publicos()