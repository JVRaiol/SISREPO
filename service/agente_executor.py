"""Executa as ferramentas pedidas pelo modelo e controla a confirmação do operador.

Como as threads se dividem:

  thread do agente  -> conversa com o Gemini pela internet (demora). É a única que PODE esperar.
  thread da tela    -> a janela do Kivy. Tudo que mexe no banco ou em widgets roda aqui (o banco tem uma conexão só,
                       compartilhada por todos os repositories, então ele nunca é usado por duas threads ao mesmo tempo).

Quando o modelo pede uma escrita, a thread do agente pede à tela para PREPARAR (validar + montar o texto), a tela abre a
caixa de confirmação e a thread do agente fica parada num Event, esperando a decisão do operador. A janela continua
livre o tempo todo; só o agente espera. Se o operador confirma, a ação roda na thread da tela e o agente retoma.
"""

import json
import threading

from service.agente_ferramentas import LEITURA


class ExecutorFerramentas:

    def __init__(self, ferramentas, auditoria, dados_turno, agendar_na_tela, abrir_confirmacao,
                 tempo_confirmacao=600, tempo_leitura=60, max_escritas_por_pedido=5):

        self.ferramentas = ferramentas                  # dicionário nome -> Ferramenta
        self.auditoria = auditoria                      # repository da tabela de auditoria
        self.dados_turno = dados_turno                  # função -> (operador, turno)
        self.agendar_na_tela = agendar_na_tela          # função(f): roda f na thread da tela
        self.abrir_confirmacao = abrir_confirmacao      # função(texto, ao_confirmar, ao_cancelar, critico, texto_botao) -> caixa
        self.tempo_confirmacao = tempo_confirmacao
        self.tempo_leitura = tempo_leitura
        self.max_escritas_por_pedido = max_escritas_por_pedido

        self.escritas_neste_pedido = 0
        self.gravou_neste_pedido = False

    def novo_pedido(self):
        # chamado a cada mensagem nova do operador
        self.escritas_neste_pedido = 0
        self.gravou_neste_pedido = False

    # ------------------------------------------------------------ entrada (chamada pela thread do agente)

    def executar(self, nome, argumentos):

        ferramenta = self.ferramentas.get(nome)

        if ferramenta is None:
            return {"erro": f"A ferramenta '{nome}' não existe."}

        if not isinstance(argumentos, dict):
            argumentos = {}

        if ferramenta.tipo == LEITURA:
            return self._ler(ferramenta, argumentos)

        return self._escrever(ferramenta, argumentos)

    # ------------------------------------------------------------ leitura

    def _na_tela(self, funcao):
        # roda a função na thread da tela e espera o resultado
        pronto = threading.Event()
        caixa = {}

        def rodar():
            try:
                caixa["valor"] = funcao()
            except Exception as erro:
                caixa["erro"] = erro
            finally:
                pronto.set()

        self.agendar_na_tela(rodar)

        if not pronto.wait(self.tempo_leitura):
            raise TimeoutError("A tela não respondeu a tempo.")

        if "erro" in caixa:
            raise caixa["erro"]

        return caixa["valor"]

    def _ler(self, ferramenta, argumentos):

        try:
            return self._na_tela(lambda: ferramenta.funcao(argumentos))

        except ValueError as erro:
            return {"erro": str(erro)}

        except Exception as erro:
            print(f"Erro na ferramenta {ferramenta.nome}: {erro}")
            return {"erro": "Não foi possível consultar essa informação agora."}

    # ------------------------------------------------------------ escrita

    def _escrever(self, ferramenta, argumentos):

        if self.escritas_neste_pedido >= self.max_escritas_por_pedido:
            return {"erro": "Limite de operações de escrita por pedido atingido. Peça ao operador para enviar uma nova mensagem."}

        estado = {"decidido": False, "resultado": None, "caixa": None}
        pronto = threading.Event()

        def finalizar(resultado):
            estado["decidido"] = True
            estado["resultado"] = resultado
            pronto.set()

        # tudo daqui até o fim de "iniciar" roda na thread da tela
        def iniciar():

            if estado["decidido"]:
                return  # o tempo já esgotou antes da tela chegar aqui

            try:
                plano = ferramenta.funcao(argumentos)

            except ValueError as erro:
                self._auditar(ferramenta, argumentos, "(recusado na validação)", False, f"recusado: {erro}")
                finalizar({"erro": str(erro)})
                return

            except Exception as erro:
                print(f"Erro ao preparar {ferramenta.nome}: {erro}")
                self._auditar(ferramenta, argumentos, "(falha ao preparar)", False, f"falha: {erro}")
                finalizar({"erro": "Não foi possível preparar essa operação."})
                return

            # só conta no limite quando uma confirmação realmente vai ser mostrada ao operador
            self.escritas_neste_pedido += 1

            def confirmar():

                if estado["decidido"]:
                    return

                estado["decidido"] = True

                try:
                    dados = plano.executar() or {}
                    resultado = {"sucesso": True, **dados}
                    self.gravou_neste_pedido = True
                    self._auditar(ferramenta, argumentos, plano.descricao, True, f"sucesso: {dados.get('mensagem', '')}")

                except ValueError as erro:
                    resultado = {"erro": str(erro)}
                    self._auditar(ferramenta, argumentos, plano.descricao, True, f"erro: {erro}")

                except Exception as erro:
                    print(f"Erro ao executar {ferramenta.nome}: {erro}")
                    resultado = {"erro": "Falha ao gravar. Nada foi alterado."}
                    self._auditar(ferramenta, argumentos, plano.descricao, True, f"falha: {erro}")

                finalizar(resultado)

            def cancelar():

                if estado["decidido"]:
                    return

                self._auditar(ferramenta, argumentos, plano.descricao, False, "cancelado pelo operador")
                finalizar({"cancelado_pelo_operador": True, "mensagem": "O operador não confirmou. Nada foi gravado. Não tente de novo, a menos que ele peça."})

            estado["plano"] = plano
            estado["cancelar"] = cancelar
            estado["caixa"] = self.abrir_confirmacao(plano.descricao, confirmar, cancelar, plano.critico, plano.texto_botao)

        self.agendar_na_tela(iniciar)

        # a thread do agente espera aqui, parada, até o operador decidir
        if not pronto.wait(self.tempo_confirmacao):

            def expirar():

                if estado["decidido"]:
                    return

                estado["decidido"] = True
                self._auditar(ferramenta, argumentos, estado["plano"].descricao if "plano" in estado else "", False, "sem resposta do operador (tempo esgotado)")

                if estado["caixa"] is not None:
                    estado["caixa"].fechar_sem_decisao()

                finalizar({"cancelado_pelo_operador": True, "mensagem": "O operador não respondeu a tempo. Nada foi gravado."})

            self.agendar_na_tela(expirar)
            pronto.wait(10)

        return estado["resultado"] or {"erro": "Sem resposta da tela."}

    # ------------------------------------------------------------ auditoria (sempre na thread da tela)

    def _auditar(self, ferramenta, argumentos, descricao, confirmado, resultado):

        try:
            operador, turno = self.dados_turno()
            texto_argumentos = json.dumps(argumentos, ensure_ascii=False, default=str)

            self.auditoria.registrar(operador, turno, ferramenta.nome, texto_argumentos[:4000], (descricao or "")[:4000], confirmado, (resultado or "")[:1000])

        except Exception as erro:
            # a auditoria nunca pode derrubar a operação, mas o erro aparece no terminal
            print(f"Falha ao gravar a auditoria: {erro}")