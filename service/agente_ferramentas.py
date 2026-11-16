"""Ferramentas que o assistente pode chamar.

Cada ferramenta é uma função que o modelo pede para rodar. Existem três tipos:

  leitura  -> roda direto e devolve dados ao modelo
  escrita  -> primeiro PREPARA (valida e monta o texto da confirmação), depois o operador confirma, só então executa
  critica  -> igual à escrita, mas a confirmação mostra "antes -> depois" e avisos mais fortes

O texto que o operador vê na confirmação é montado AQUI, a partir dos dados já validados, e nunca copiado do que o
modelo escreveu. Assim, mesmo que o modelo entenda errado (ou leia um texto malicioso vindo do banco), o operador
enxerga exatamente o que vai ser gravado.

Este arquivo não depende do Kivy nem do Gemini, só dos controllers que já existem no projeto.
"""

import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

LEITURA = "leitura"
ESCRITA = "escrita"
CRITICA = "critica"

PRODUTOS = ("Cópias", "Impressão", "Digitalização", "Encadernação")


# ---------------------------------------------------------------- utilitários

def moeda(valor):
    # formato brasileiro: R$ 1.234,56
    texto = f"{float(valor):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def numero(valor):
    return f"{int(valor or 0):,}".replace(",", ".")


def sem_acento(texto):
    # "Impressão" -> "impressao": serve para comparar nomes sem se preocupar com acento ou maiúscula
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).strip().lower()


def pegar_texto(args, chave, obrigatorio=True, maximo=120, quebras=False):

    valor = args.get(chave)

    if valor is None:
        valor = ""

    valor = str(valor).strip()

    if not quebras:
        valor = " ".join(valor.split())  # tira espaços repetidos e quebras de linha

    if obrigatorio and not valor:
        raise ValueError(f"Falta informar: {chave}.")

    if len(valor) > maximo:
        raise ValueError(f"O campo {chave} passou do limite de {maximo} caracteres.")

    return valor


def pegar_inteiro(args, chave, minimo=0, maximo=10_000_000, obrigatorio=False):

    valor = args.get(chave)

    if valor is None or valor == "":
        if obrigatorio:
            raise ValueError(f"Falta informar: {chave}.")
        return None

    if isinstance(valor, bool):
        raise ValueError(f"O campo {chave} precisa ser um número.")

    try:
        numero_lido = Decimal(str(valor).strip().replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"O campo {chave} precisa ser um número.")

    if not numero_lido.is_finite() or numero_lido != numero_lido.to_integral_value():
        raise ValueError(f"O campo {chave} precisa ser um número inteiro.")

    numero_lido = int(numero_lido)

    if numero_lido < minimo or numero_lido > maximo:
        raise ValueError(f"O campo {chave} precisa estar entre {minimo} e {maximo}.")

    return numero_lido


def pegar_dinheiro(args, chave, maximo=100_000):

    valor = args.get(chave)

    if valor is None or isinstance(valor, bool):
        raise ValueError(f"Falta informar: {chave}.")

    try:
        valor = Decimal(str(valor).strip().replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"O campo {chave} precisa ser um valor em reais.")

    if not valor.is_finite() or valor <= 0:
        raise ValueError(f"O campo {chave} precisa ser maior que zero.")

    valor = valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    if valor <= 0 or valor > maximo:
        raise ValueError(f"O campo {chave} precisa estar entre R$ 0,01 e {moeda(maximo)}.")

    return valor


def pegar_booleano(args, chave):

    valor = args.get(chave)

    if isinstance(valor, bool):
        return valor

    if isinstance(valor, str) and sem_acento(valor) in ("true", "sim", "verdadeiro"):
        return True

    return False


def normalizar_produto(texto):

    alvo = sem_acento(texto)

    for produto in PRODUTOS:
        if sem_acento(produto) == alvo:
            return produto

    raise ValueError(f"Produto desconhecido: '{texto}'. Os produtos são: {', '.join(PRODUTOS)}.")


def serializar(objeto):
    # transforma Decimal, datas, tuplas etc. em algo que vira JSON
    if isinstance(objeto, Decimal):
        return float(round(objeto, 2))

    if isinstance(objeto, dict):
        return {str(chave): serializar(valor) for chave, valor in objeto.items()}

    if isinstance(objeto, (list, tuple)):
        return [serializar(item) for item in objeto]

    if hasattr(objeto, "isoformat"):
        return objeto.isoformat()

    return objeto


# ---------------------------------------------------------------- estruturas

class Plano:
    # o que uma ferramenta de escrita devolve ao ser preparada: o texto para o operador e a ação a executar se ele confirmar
    def __init__(self, descricao, executar, texto_botao="Confirmar", critico=False):
        self.descricao = descricao
        self.executar = executar
        self.texto_botao = texto_botao
        self.critico = critico


class Ferramenta:
    def __init__(self, nome, descricao, parametros, tipo, funcao):
        self.nome = nome
        self.descricao = descricao
        self.parametros = parametros  # esquema (dicionário) dos parâmetros, ou None se não tem
        self.tipo = tipo
        self.funcao = funcao


def objeto(propriedades, obrigatorios=()):
    return {"type": "OBJECT", "properties": propriedades, "required": list(obrigatorios)}


TEXTO = lambda descricao: {"type": "STRING", "description": descricao}
INTEIRO = lambda descricao: {"type": "INTEGER", "description": descricao}
NUMERO = lambda descricao: {"type": "NUMBER", "description": descricao}
BOOLEANO = lambda descricao: {"type": "BOOLEAN", "description": descricao}


# ---------------------------------------------------------------- as ferramentas

class Ferramentas:

    def __init__(self, janela, equipamentos, valores, relatorio, janela_service, abrir_arquivo=None, data_hoje=None, escolher_destino=None):

        self.janela = janela                  # janelaPrincipalController (pix, promoções, cobrança rápida)
        self.equipamentos = equipamentos      # EquipamentosController
        self.valores = valores                # ValoresController
        self.relatorio = relatorio            # RelatorioController
        self.janela_service = janela_service  # para ler os registros do turno
        self.abrir_arquivo = abrir_arquivo    # abre o PDF depois de gerar (opcional)
        self.escolher_destino = escolher_destino  # janela de "salvar como" do PDF
        self.data_hoje = data_hoje

    def todas(self):

        lista = [
            # ---- leitura
            Ferramenta("consultar_valores",
                       "Lista o preço unitário atual de cada produto (Cópias, Impressão, Digitalização, Encadernação).",
                       None, LEITURA, self.consultar_valores),

            Ferramenta("consultar_equipamentos",
                       "Lista os equipamentos cadastrados com o que cada um faz, se está pausado e o total acumulado atual do contador (cópias, impressões, digitalizações).",
                       None, LEITURA, self.consultar_equipamentos),

            Ferramenta("consultar_pix_do_turno",
                       "Lista os Pix já registrados hoje no turno do operador logado, com o total.",
                       None, LEITURA, self.consultar_pix_do_turno),

            Ferramenta("consultar_promocoes_do_turno",
                       "Lista as promoções já registradas hoje no turno do operador logado.",
                       None, LEITURA, self.consultar_promocoes_do_turno),

            Ferramenta("calcular_cobranca",
                       "Calcula quanto cobrar de um cliente por quantidades de produtos. Não grava nada.",
                       objeto({"copias": INTEIRO("Quantidade de cópias"),
                               "impressoes": INTEIRO("Quantidade de impressões"),
                               "digitalizacoes": INTEIRO("Quantidade de digitalizações"),
                               "encadernacoes": INTEIRO("Quantidade de encadernações")}),
                       LEITURA, self.calcular_cobranca),

            Ferramenta("simular_relatorio",
                       "Calcula o relatório do turno sem gravar nada (prévia): valores por equipamento, promoções, Pix e espécie. "
                       "Os totais informados são a LEITURA ATUAL DO CONTADOR de cada equipamento (acumulado), não a quantidade feita no turno. "
                       "Equipamento ou campo não informado é considerado sem movimento.",
                       self._esquema_relatorio(), LEITURA, self.simular_relatorio),

            # ---- escrita comum (pede confirmação)
            Ferramenta("registrar_pix",
                       "Registra um pagamento por Pix no turno do operador logado. O operador precisa confirmar.",
                       objeto({"pagador": TEXTO("Nome de quem pagou"),
                               "valor": NUMERO("Valor pago em reais, por exemplo 12.5")}, ("pagador", "valor")),
                       ESCRITA, self.registrar_pix),

            Ferramenta("registrar_promocao",
                       "Registra promoções do turno (um ou mais produtos). valor_unitario é o preço promocional de cada unidade. O operador precisa confirmar.",
                       objeto({"promocoes": {"type": "ARRAY", "items": objeto({
                           "produto": TEXTO("Cópias, Impressão, Digitalização ou Encadernação"),
                           "quantidade": INTEIRO("Quantidade de unidades em promoção"),
                           "valor_unitario": NUMERO("Preço promocional de cada unidade, em reais")},
                           ("produto", "quantidade", "valor_unitario"))}}, ("promocoes",)),
                       ESCRITA, self.registrar_promocao),

            Ferramenta("alterar_pausa_equipamento",
                       "Pausa ou reativa um equipamento. Equipamento pausado não entra no relatório. O operador precisa confirmar.",
                       objeto({"nome": TEXTO("Nome do equipamento"),
                               "pausar": BOOLEANO("true para pausar, false para reativar")}, ("nome", "pausar")),
                       ESCRITA, self.alterar_pausa_equipamento),

            Ferramenta("cadastrar_equipamento",
                       "Cadastra um equipamento novo. O operador precisa confirmar.",
                       objeto({"nome": TEXTO("Nome do equipamento"),
                               "copia": BOOLEANO("Se faz cópia"),
                               "imprime": BOOLEANO("Se imprime"),
                               "digitaliza": BOOLEANO("Se digitaliza"),
                               "total_copias": INTEIRO("Contador atual de cópias (só se faz cópia)"),
                               "total_impressoes": INTEIRO("Contador atual de impressões (só se imprime)"),
                               "total_digitalizacoes": INTEIRO("Contador atual de digitalizações (só se digitaliza)"),
                               "painel_controle": TEXTO("Link do painel de controle (opcional)")},
                              ("nome", "copia", "imprime", "digitaliza")),
                       ESCRITA, self.cadastrar_equipamento),

            Ferramenta("gerar_relatorio",
                       "Gera o relatório do turno: salva no banco, atualiza os totais dos equipamentos e cria o PDF. "
                       "Os totais informados são a LEITURA ATUAL DO CONTADOR de cada equipamento (acumulado), não a quantidade feita no turno. "
                       "Perdidas são as páginas perdidas no turno. O operador precisa confirmar.",
                       self._esquema_relatorio(com_observacoes=True), ESCRITA, self.gerar_relatorio),

            # ---- escrita crítica (confirmação com antes/depois)
            Ferramenta("alterar_valor_produto",
                       "Altera o preço unitário de um produto. CRÍTICO: vale para todos os turnos seguintes. O operador precisa confirmar.",
                       objeto({"produto": TEXTO("Cópias, Impressão, Digitalização ou Encadernação"),
                               "novo_valor": NUMERO("Novo preço unitário, em reais")}, ("produto", "novo_valor")),
                       CRITICA, self.alterar_valor_produto),

            Ferramenta("alterar_totais_equipamento",
                       "Altera o contador acumulado de um equipamento. CRÍTICO: esse total é o ponto de partida dos próximos relatórios. O operador precisa confirmar.",
                       objeto({"nome": TEXTO("Nome do equipamento"),
                               "total_copias": INTEIRO("Novo contador de cópias"),
                               "total_impressoes": INTEIRO("Novo contador de impressões"),
                               "total_digitalizacoes": INTEIRO("Novo contador de digitalizações")}, ("nome",)),
                       CRITICA, self.alterar_totais_equipamento),

            Ferramenta("deletar_equipamento",
                       "Deleta um equipamento. CRÍTICO: não tem como desfazer. O operador precisa confirmar.",
                       objeto({"nome": TEXTO("Nome do equipamento")}, ("nome",)),
                       CRITICA, self.deletar_equipamento),
        ]

        return {ferramenta.nome: ferramenta for ferramenta in lista}

    def _esquema_relatorio(self, com_observacoes=False):

        propriedades = {
            "equipamentos": {"type": "ARRAY", "items": objeto({
                "nome": TEXTO("Nome do equipamento"),
                "total_copias": INTEIRO("Leitura atual do contador de cópias (acumulado)"),
                "perdidas_copias": INTEIRO("Cópias perdidas no turno"),
                "total_impressoes": INTEIRO("Leitura atual do contador de impressões (acumulado)"),
                "perdidas_impressoes": INTEIRO("Impressões perdidas no turno"),
                "total_digitalizacoes": INTEIRO("Leitura atual do contador de digitalizações (acumulado)"),
                "perdidas_digitalizacoes": INTEIRO("Digitalizações perdidas no turno")}, ("nome",))},
            "encadernacoes": INTEIRO("Quantidade de encadernações feitas no turno"),
        }

        if com_observacoes:
            propriedades["observacoes"] = TEXTO("Observações do turno (opcional)")

        return objeto(propriedades, ("equipamentos",))

    # ------------------------------------------------------------ apoio

    def _equipamentos_cadastrados(self):

        lista = []

        for id_equipamento in self.equipamentos.listar_equipamentos():
            lista.append(self.equipamentos.consultar_equipamento(id_equipamento))

        return lista

    def _achar_equipamento(self, nome):

        todos = self._equipamentos_cadastrados()
        alvo = sem_acento(nome)

        iguais = [e for e in todos if sem_acento(e["nome"]) == alvo]

        if not iguais:
            iguais = [e for e in todos if alvo and alvo in sem_acento(e["nome"])]

        if len(iguais) == 1:
            return iguais[0]

        nomes = ", ".join(e["nome"] for e in todos) or "nenhum"

        if len(iguais) > 1:
            raise ValueError(f"Mais de um equipamento combina com '{nome}': {', '.join(e['nome'] for e in iguais)}. Pergunte ao operador qual deles.")

        raise ValueError(f"Não encontrei o equipamento '{nome}'. Equipamentos cadastrados: {nomes}.")

    def _entradas_relatorio(self, args):

        lista = args.get("equipamentos")

        if not isinstance(lista, list) or not lista:
            raise ValueError("Falta informar os equipamentos do relatório.")

        chaves = {
            "total_copias": "copias", "perdidas_copias": "perdidas copias",
            "total_impressoes": "impressoes", "perdidas_impressoes": "perdidas impressoes",
            "total_digitalizacoes": "digitalizacoes", "perdidas_digitalizacoes": "perdidas digitalizacoes",
        }

        entradas = []
        usados = set()

        for item in lista:

            if not isinstance(item, dict):
                raise ValueError("Cada equipamento do relatório precisa ter nome e totais.")

            equipamento = self._achar_equipamento(pegar_texto(item, "nome"))

            if equipamento["id"] in usados:
                raise ValueError(f"O equipamento {equipamento['nome']} apareceu duas vezes no relatório.")

            usados.add(equipamento["id"])

            entrada = {"nome": equipamento["nome"]}

            for chave_modelo, chave_controller in chaves.items():
                valor = pegar_inteiro(item, chave_modelo)
                if valor is not None:
                    entrada[chave_controller] = valor

            entradas.append(entrada)

        encadernacao = pegar_inteiro(args, "encadernacoes") or 0

        tem_movimento = encadernacao > 0 or any(valor for entrada in entradas for chave, valor in entrada.items() if chave != "nome")

        if not tem_movimento:
            raise ValueError("Nenhum total foi informado. Informe o contador atual de pelo menos um equipamento ou as encadernações.")

        return entradas, encadernacao

    def _resumir_previa(self, previa):

        equipamentos = []

        for equipamento in previa["equipamentos"]:

            produtos = []

            for produto, chave in (("Cópias", "copias"), ("Impressão", "impressoes"), ("Digitalização", "digitalizacoes")):

                if equipamento[f"total {chave}"] == 0 and equipamento[f"perdidas {chave}"] == 0:
                    continue

                produtos.append({
                    "produto": produto,
                    "contador_anterior": equipamento[chave],
                    "feitas": equipamento[f"total {chave}"],
                    "perdidas": equipamento[f"perdidas {chave}"],
                    "contabilizadas": equipamento[f"liquido {chave}"],
                    "em_promocao": equipamento[f"promo {chave}"],
                    "valor_das_normais": equipamento[f"valor {chave}"],
                })

            if produtos:
                equipamentos.append({"nome": equipamento["nome"], "produtos": produtos})

        return serializar({
            "equipamentos": equipamentos,
            "por_produto": previa["resumo"],
            "total_geral": previa["total_geral"],
            "total_pix": previa["total pix"],
            "total_especie": previa["total especie"],
            "avisos": previa["avisos"],
        })

    # ------------------------------------------------------------ leitura

    def consultar_valores(self, args):

        return {"valores": serializar(self.valores.consultar_valores())}

    def consultar_equipamentos(self, args):

        lista = []

        for e in self._equipamentos_cadastrados():

            item = {"nome": e["nome"], "pausado": e["pausado"], "faz_copia": e["copia"], "imprime": e["imprime"], "digitaliza": e["scaneia"]}

            if e["copia"]:
                item["total_copias"] = e["totalCopias"]
            if e["imprime"]:
                item["total_impressoes"] = e["totalImpressoes"]
            if e["scaneia"]:
                item["total_digitalizacoes"] = e["totalDigitalizacao"]

            lista.append(item)

        return {"equipamentos": lista}

    def _dados_do_turno(self):

        dados = self.janela_service.consultar_dados_operador_logado()

        if dados is None:
            raise ValueError("Nenhum operador logado no sistema.")

        from datetime import date
        return dados["nome"], dados["turnoTrabalhado"], (self.data_hoje or date.today())

    def consultar_pix_do_turno(self, args):

        operador, turno, data = self._dados_do_turno()

        registros = self.janela_service.registros_pix_repository.buscar_registro_por_operador_data_e_turno(data, operador, turno)

        lista = [{"hora": r[1].strftime("%H:%M"), "pagador": r[4], "valor": serializar(r[5])} for r in registros]

        return {"pix": lista, "total": serializar(sum((r[5] for r in registros), Decimal(0)))}

    def consultar_promocoes_do_turno(self, args):

        operador, turno, data = self._dados_do_turno()

        registros = self.janela_service.registros_promo_repository.buscar_registro_por_operador_data_e_turno(data, operador, turno)

        lista = [{"hora": r[1].strftime("%H:%M"), "produto": r[4], "quantidade": r[5], "valor_unitario": serializar(r[6]), "valor_total": serializar(r[7])} for r in registros]

        return {"promocoes": lista}

    def calcular_cobranca(self, args):

        quantidades = {}

        for chave in ("copias", "impressoes", "digitalizacoes", "encadernacoes"):
            quantidades[chave] = pegar_inteiro(args, chave, maximo=1_000_000) or 0

        if not any(quantidades.values()):
            raise ValueError("Informe pelo menos uma quantidade.")

        calculo = self.janela.buscar_valores(str(quantidades["copias"]), str(quantidades["impressoes"]), str(quantidades["digitalizacoes"]), str(quantidades["encadernacoes"]))

        return serializar(calculo)

    def simular_relatorio(self, args):

        entradas, encadernacao = self._entradas_relatorio(args)

        previa = self.relatorio.calcular_relatorio(entradas, str(encadernacao))

        return self._resumir_previa(previa)

    # ------------------------------------------------------------ escrita comum

    def registrar_pix(self, args):

        pagador = pegar_texto(args, "pagador", maximo=100)
        valor = pegar_dinheiro(args, "valor")

        def executar():
            self.janela.registrar_pix(pagador, str(valor))
            return {"mensagem": f"Pix de {moeda(valor)} de {pagador} registrado."}

        return Plano(f"Registrar Pix de {moeda(valor)} de {pagador}?", executar)

    def registrar_promocao(self, args):

        lista = args.get("promocoes")

        if not isinstance(lista, list) or not lista:
            raise ValueError("Falta informar as promoções.")

        promocoes = {}
        linhas = []
        total = Decimal(0)

        for item in lista:

            if not isinstance(item, dict):
                raise ValueError("Cada promoção precisa ter produto, quantidade e valor_unitario.")

            produto = normalizar_produto(pegar_texto(item, "produto"))

            if produto in promocoes:
                raise ValueError(f"O produto {produto} apareceu duas vezes. Junte em uma promoção só.")

            quantidade = pegar_inteiro(item, "quantidade", minimo=1, maximo=100_000, obrigatorio=True)
            valor = pegar_dinheiro(item, "valor_unitario")

            promocoes[produto] = (quantidade, str(valor))
            linhas.append(f"• {produto}: {numero(quantidade)} x {moeda(valor)} = {moeda(quantidade * valor)}")
            total += quantidade * valor

        def executar():
            self.janela.registrar_promocao(promocoes)
            return {"mensagem": "Promoção registrada."}

        return Plano("Registrar promoção?\n\n" + "\n".join(linhas) + f"\n\nTotal: {moeda(total)}", executar)

    def alterar_pausa_equipamento(self, args):

        equipamento = self._achar_equipamento(pegar_texto(args, "nome"))
        pausar = pegar_booleano(args, "pausar")

        if pausar and equipamento["pausado"]:
            raise ValueError(f"O equipamento {equipamento['nome']} já está pausado.")

        if not pausar and not equipamento["pausado"]:
            raise ValueError(f"O equipamento {equipamento['nome']} já está ativo.")

        def executar():
            if pausar:
                self.equipamentos.pausar_equipamento(equipamento["id"])
            else:
                self.equipamentos.ativar_equipamento(equipamento["id"])

            return {"mensagem": f"Equipamento {equipamento['nome']} {'pausado' if pausar else 'reativado'}."}

        acao = "Pausar" if pausar else "Reativar"
        return Plano(f"{acao} o equipamento '{equipamento['nome']}'?", executar)

    def cadastrar_equipamento(self, args):

        nome = pegar_texto(args, "nome", maximo=80)
        copia = pegar_booleano(args, "copia")
        imprime = pegar_booleano(args, "imprime")
        digitaliza = pegar_booleano(args, "digitaliza")
        painel = pegar_texto(args, "painel_controle", obrigatorio=False, maximo=300)

        if not (copia or imprime or digitaliza):
            raise ValueError("Informe o que o equipamento faz (cópia, impressão ou digitalização).")

        if any(sem_acento(e["nome"]) == sem_acento(nome) for e in self._equipamentos_cadastrados()):
            raise ValueError(f"Já existe um equipamento chamado {nome}.")

        total_copias = (pegar_inteiro(args, "total_copias") or 0) if copia else 0
        total_impressoes = (pegar_inteiro(args, "total_impressoes") or 0) if imprime else 0
        total_digitalizacoes = (pegar_inteiro(args, "total_digitalizacoes") or 0) if digitaliza else 0

        linhas = [f"Cadastrar o equipamento '{nome}'?", ""]

        if copia:
            linhas.append(f"• Cópia (contador inicial: {numero(total_copias)})")
        if imprime:
            linhas.append(f"• Impressão (contador inicial: {numero(total_impressoes)})")
        if digitaliza:
            linhas.append(f"• Digitalização (contador inicial: {numero(total_digitalizacoes)})")
        if painel:
            linhas.append(f"• Painel de controle: {painel}")

        def executar():
            self.equipamentos.cadastrar_equipamento(nome, copia, str(total_copias), imprime, str(total_impressoes), digitaliza, str(total_digitalizacoes), painel)
            return {"mensagem": f"Equipamento {nome} cadastrado."}

        return Plano("\n".join(linhas), executar)

    def gerar_relatorio(self, args):

        entradas, encadernacao = self._entradas_relatorio(args)
        observacoes = pegar_texto(args, "observacoes", obrigatorio=False, maximo=1000, quebras=True)

        # calcula antes de pedir a confirmação: se algo estiver errado (total menor que o anterior, perdidas demais...) já avisa aqui
        previa = self.relatorio.calcular_relatorio(entradas, str(encadernacao))

        linhas = ["Gerar o relatório do turno?", ""]

        for equipamento in previa["equipamentos"]:
            for produto, chave in (("cópias", "copias"), ("impressões", "impressoes"), ("digitalizações", "digitalizacoes")):

                if equipamento[f"total {chave}"] == 0 and equipamento[f"perdidas {chave}"] == 0:
                    continue

                antes = equipamento[chave]
                depois = antes + equipamento[f"total {chave}"]
                linhas.append(f"• {equipamento['nome']} ({produto}): {numero(antes)} → {numero(depois)}")

        if encadernacao:
            linhas.append(f"• Encadernações: {numero(encadernacao)}")

        linhas += ["", f"Total geral: {moeda(previa['total_geral'])}", f"Pix: {moeda(previa['total pix'])}  |  Espécie: {moeda(previa['total especie'])}"]

        for aviso in previa["avisos"]:
            linhas.append(f"Atenção: {aviso}")

        if observacoes:
            linhas += ["", f"Observações: {observacoes}"]

        linhas += ["", "O relatório será salvo, os totais dos equipamentos serão atualizados e o PDF será aberto."]

        def executar():
            destino = self.escolher_destino(self.relatorio.nome_sugerido_pdf()) if self.escolher_destino else None

            if not destino:
                raise ValueError("Geração cancelada: nenhum local foi escolhido para salvar o PDF.")

            caminho = self.relatorio.gerar_relatorio(entradas, str(encadernacao), observacoes, destino)

            if self.abrir_arquivo:
                try:
                    self.abrir_arquivo(caminho)
                except Exception as erro:
                    print(erro)

            return {"mensagem": "Relatório gerado e salvo.", "arquivo": caminho.name, "total_geral": serializar(previa["total_geral"])}

        return Plano("\n".join(linhas), executar, texto_botao="Gerar")

    # ------------------------------------------------------------ escrita crítica

    def alterar_valor_produto(self, args):

        produto = normalizar_produto(pegar_texto(args, "produto"))
        novo = pegar_dinheiro(args, "novo_valor", maximo=10_000)

        atual = None

        for item in self.valores.consultar_valores():
            if item["produto"] == produto:
                atual = item["valor"]

        if atual is None:
            raise ValueError(f"O produto {produto} não tem valor cadastrado.")

        if Decimal(str(atual)) == novo:
            raise ValueError(f"O valor de {produto} já é {moeda(novo)}.")

        def executar():
            self.valores.alterar_valor(produto, str(novo))
            return {"mensagem": f"Valor de {produto} alterado para {moeda(novo)}."}

        texto = f"Alterar o valor de {produto}?\n\nValor de {produto}: {moeda(atual)} → {moeda(novo)}\n\nO novo preço vale para todos os turnos seguintes."

        return Plano(texto, executar, texto_botao="Alterar", critico=True)

    def alterar_totais_equipamento(self, args):

        equipamento = self._achar_equipamento(pegar_texto(args, "nome"))

        campos = (
            ("total_copias", "cópias", "copia", "totalCopias"),
            ("total_impressoes", "impressões", "imprime", "totalImpressoes"),
            ("total_digitalizacoes", "digitalizações", "scaneia", "totalDigitalizacao"),
        )

        novos = {}
        linhas = []

        for chave, rotulo, funcao, coluna in campos:

            valor = pegar_inteiro(args, chave)

            if valor is None:
                novos[coluna] = equipamento[coluna]
                continue

            if not equipamento[funcao]:
                raise ValueError(f"O equipamento {equipamento['nome']} não faz {rotulo}.")

            novos[coluna] = valor

            if valor != equipamento[coluna]:
                linhas.append(f"Total de {rotulo} de {equipamento['nome']}: {numero(equipamento[coluna])} → {numero(valor)}")

        if not linhas:
            raise ValueError("Nenhum total novo foi informado, ou os valores informados já são os atuais.")

        def executar():
            self.equipamentos.alterar_equipamento(equipamento["id"], equipamento["nome"], str(novos["totalCopias"]), str(novos["totalImpressoes"]), str(novos["totalDigitalizacao"]))
            return {"mensagem": f"Totais de {equipamento['nome']} alterados."}

        texto = "Alterar os totais do equipamento?\n\n" + "\n".join(linhas) + "\n\nEsse total é o ponto de partida do próximo relatório. Um valor errado altera os relatórios seguintes."

        return Plano(texto, executar, texto_botao="Alterar", critico=True)

    def deletar_equipamento(self, args):

        equipamento = self._achar_equipamento(pegar_texto(args, "nome"))

        def executar():
            self.equipamentos.deletar_equipamento(equipamento["id"])
            return {"mensagem": f"Equipamento {equipamento['nome']} deletado."}

        texto = f"Deletar o equipamento '{equipamento['nome']}'?\n\nEssa ação NÃO pode ser desfeita."

        return Plano(texto, executar, texto_botao="Deletar", critico=True)