from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


RAIZ_PROJETO = Path(__file__).resolve().parent.parent
LOGO = RAIZ_PROJETO / "templates" / "logobpav.jpg"

PRODUTOS = {"Cópias": "copias", "Impressão": "impressoes", "Digitalização": "digitalizacoes"}

LARGURA, ALTURA = A4
MARGEM_X = 48
MARGEM_TOPO = 40
MARGEM_BASE = 50
LARGURA_UTIL = LARGURA - 2 * MARGEM_X

FONTE = "Helvetica"
FONTE_NEGRITO = "Helvetica-Bold"
PRETO = (0.1, 0.1, 0.1)
CINZA = (0.45, 0.45, 0.45)
LINHA = (0.8, 0.8, 0.8)


def moeda(valor):

    texto = f"{float(valor):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def numero(valor):
    return f"{int(valor or 0):,}".replace(",", ".")


def primeiro_e_ultimo_nome(nome):

    partes = str(nome).split()

    if len(partes) <= 2:
        return " ".join(partes)

    return f"{partes[0]} {partes[-1]}"


def tamanho_que_cabe(texto, largura, maximo, minimo=7, negrito=False):

    fonte = FONTE_NEGRITO if negrito else FONTE
    tamanho = maximo

    while tamanho > minimo and stringWidth(texto, fonte, tamanho) > largura:
        tamanho -= 0.5

    return tamanho


def quebrar_texto(texto, largura, tamanho, negrito=False):
    fonte = FONTE_NEGRITO if negrito else FONTE
    linhas = []
    atual = ""

    for palavra in str(texto).replace("\t", " ").split():

        while stringWidth(palavra, fonte, tamanho) > largura:
            corte = len(palavra)

            while corte > 1 and stringWidth(palavra[:corte], fonte, tamanho) > largura:
                corte -= 1

            if atual:
                linhas.append(atual)
                atual = ""

            linhas.append(palavra[:corte])
            palavra = palavra[corte:]

        tentativa = f"{atual} {palavra}".strip()

        if stringWidth(tentativa, fonte, tamanho) <= largura:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra

    if atual:
        linhas.append(atual)

    return linhas or [""]


class Relatorio:

    def __init__(self, c, resultado, observacoes, emitido_em):

        self.c = c
        self.resultado = resultado
        self.observacoes = (observacoes or "").strip()
        self.emitido_em = emitido_em
        self.y = MARGEM_TOPO


    def _y(self):

        return ALTURA - self.y

    def _cor(self, cor):
        self.c.setFillColorRGB(*cor)
        self.c.setStrokeColorRGB(*cor)

    def garantir_espaco(self, altura):

        if self.y + altura > ALTURA - MARGEM_BASE:
            self.c.showPage()
            self.y = MARGEM_TOPO

    def espaco(self, pontos):
        self.y += pontos

    def linha_horizontal(self, cor=LINHA, espessura=0.7):
        self._cor(cor)
        self.c.setLineWidth(espessura)
        self.c.line(MARGEM_X, self._y(), LARGURA - MARGEM_X, self._y())

    def texto(self, texto, x, tamanho, negrito=False, cor=PRETO, alinhamento="esquerda"):

        self._cor(cor)
        self.c.setFont(FONTE_NEGRITO if negrito else FONTE, tamanho)

        if alinhamento == "direita":
            self.c.drawRightString(x, self._y(), texto)
        elif alinhamento == "centro":
            self.c.drawCentredString(x, self._y(), texto)
        else:
            self.c.drawString(x, self._y(), texto)

    def linha_com_valor(self, esquerda, valor, tamanho, negrito=False, cor=PRETO, recuo=0):

        self.y += tamanho
        self.texto(esquerda, MARGEM_X + recuo, tamanho, negrito, cor)

        if valor:
            self.texto(valor, LARGURA - MARGEM_X, tamanho, negrito, cor, "direita")

        self.y += 4


    def cabecalho(self):

        r = self.resultado
        tamanho_logo = 90

        if LOGO.exists():
            self.c.drawImage(str(LOGO), (LARGURA - tamanho_logo) / 2, self._y() - tamanho_logo, tamanho_logo, tamanho_logo, mask="auto")

        self.y += tamanho_logo + 28

        informacoes = [
            ("OPERADOR", primeiro_e_ultimo_nome(r["operador"])),
            ("TURNO", str(r["turno"])),
            ("DATA", r["data"].strftime("%d/%m/%Y")),
            ("EMISSÃO", self.emitido_em.strftime("%d/%m/%Y %H:%M")),
        ]

        coluna = LARGURA_UTIL / len(informacoes)

        for indice, (rotulo, valor) in enumerate(informacoes):
            x = MARGEM_X + indice * coluna

            self.y += 8
            self.texto(rotulo, x, 8, cor=CINZA)
            self.y += 15

            tamanho = tamanho_que_cabe(valor, coluna - 10, 11.5, negrito=True)
            self.texto(valor, x, tamanho, negrito=True)
            self.y -= 23

        self.y += 32
        self.linha_horizontal()
        self.espaco(26)

    def secao(self, nome, total):

        self.linha_com_valor(nome, moeda(total), 14, negrito=True)
        self.espaco(2)
        self.linha_horizontal(cor=PRETO, espessura=0.9)
        self.espaco(16)

    def valor_do_produto(self, equipamento, produto, chave):

        resumo = self.resultado["resumo"][produto]
        promocao = equipamento[f"promo {chave}"]
        unitario_promo = (resumo["valor promocoes"] / resumo["promocoes"]) if resumo["promocoes"] > 0 else 0

        return equipamento[f"valor {chave}"], promocao, unitario_promo

    def bloco_equipamentos(self):

        for equipamento in self.resultado["equipamentos"]:

            produtos = []
            total_equipamento = 0

            for produto, chave in PRODUTOS.items():


                if equipamento[f"total {chave}"] == 0 and equipamento[f"perdidas {chave}"] == 0:
                    continue

                valor, promocao, unitario_promo = self.valor_do_produto(equipamento, produto, chave)

                produtos.append((produto, chave, valor, promocao, unitario_promo))
                total_equipamento += valor + promocao * unitario_promo

            if not produtos:
                continue

            self.garantir_espaco(120)
            self.secao(equipamento["nome"], total_equipamento)

            for produto, chave, valor, promocao, unitario_promo in produtos:

                self.garantir_espaco(70)

                unitario = self.resultado["resumo"][produto]["valor unitario"]

                self.linha_com_valor(produto, moeda(valor), 11.5, negrito=True, recuo=10)
                self.espaco(2)


                self.y += 10
                self.texto(f"Feitas {numero(equipamento[f'total {chave}'])}", MARGEM_X + 10, 10, cor=CINZA)
                self.texto(f"Perdidas {numero(equipamento[f'perdidas {chave}'])}", MARGEM_X + 120, 10, cor=CINZA)
                self.texto(f"Contabilizadas {numero(equipamento[f'normais {chave}'])} x {moeda(unitario)}", MARGEM_X + 230, 10, cor=CINZA)
                self.y += 5


                if promocao > 0:
                    self.y += 10
                    self.texto(f"Promoção {numero(promocao)} x {moeda(unitario_promo)}", MARGEM_X + 10, 10, cor=CINZA)
                    self.texto(moeda(promocao * unitario_promo), LARGURA - MARGEM_X, 10, cor=CINZA, alinhamento="direita")
                    self.y += 5

                self.espaco(14)

            self.espaco(14)

    def bloco_encadernacao(self):

        e = self.resultado["resumo"]["Encadernação"]

        if e["feitas"] <= 0:
            return

        unitario = e["valor unitario"]
        unitario_promo = (e["valor promocoes"] / e["promocoes"]) if e["promocoes"] > 0 else 0

        self.garantir_espaco(110)
        self.secao("Encadernação", e["total"])

        if e["promocoes"] > 0:

            self.linha_com_valor(f"Feitas {numero(e['feitas'])}", "", 10, cor=CINZA, recuo=10)
            self.espaco(2)

            if e["vendidas normais"] > 0:
                self.linha_com_valor(f"Normais {numero(e['vendidas normais'])} x {moeda(unitario)}", moeda(e["vendidas normais"] * unitario), 11, negrito=True, recuo=10)
                self.espaco(2)

            self.linha_com_valor(f"Promoção {numero(e['promocoes'])} x {moeda(unitario_promo)}", moeda(e["valor promocoes"]), 11, negrito=True, recuo=10)
        else:
            self.linha_com_valor(f"Feitas {numero(e['feitas'])} x {moeda(unitario)}", moeda(e["feitas"] * unitario), 11, negrito=True, recuo=10)

        self.espaco(26)

    def bloco_totais(self):

        r = self.resultado

        self.garantir_espaco(110)
        self.linha_horizontal()
        self.espaco(16)

        self.linha_com_valor("Total geral", moeda(r["total_geral"]), 16, negrito=True)
        self.espaco(8)
        self.linha_com_valor("Pix", moeda(r["total pix"]), 11.5)
        self.espaco(2)

        for pagamento in r["pagamentos pix"]:
            self.garantir_espaco(16)
            self.linha_com_valor(pagamento["nome"], moeda(pagamento["valor"]), 10, cor=CINZA, recuo=10)
            self.espaco(2)

        self.espaco(10)
        self.linha_com_valor("Espécie", moeda(r["total especie"]), 11.5)
        self.espaco(26)

    def bloco_avisos(self):

        if not self.resultado["avisos"]:
            return

        self.garantir_espaco(50)
        self.linha_com_valor("Avisos", "", 11, negrito=True)

        for aviso in self.resultado["avisos"]:
            for parte in quebrar_texto(aviso, LARGURA_UTIL, 9.5):
                self.garantir_espaco(14)
                self.y += 9.5
                self.texto(parte, MARGEM_X, 9.5, cor=CINZA)
                self.y += 4

        self.espaco(22)

    def bloco_observacoes(self):

        if not self.observacoes:
            return

        self.garantir_espaco(45)
        self.linha_com_valor("Observações", "", 12, negrito=True)
        self.espaco(4)

        for bloco in self.observacoes.splitlines() or [""]:
            for parte in quebrar_texto(bloco, LARGURA_UTIL, 10.5):
                self.garantir_espaco(16)
                self.y += 10.5
                self.texto(parte, MARGEM_X, 10.5)
                self.y += 5

    def bloco_produtos_salvos(self):

        # relatório já gravado no banco: só existem os totais por produto (o detalhe por equipamento não é guardado)
        for produto in self.resultado["produtos_salvos"]:

            if produto["feitas"] == 0 and not produto["perdidas"]:
                continue

            self.garantir_espaco(90)
            self.secao(produto["nome"], produto["total"])

            self.y += 10
            self.texto(f"Feitas {numero(produto['feitas'])}", MARGEM_X + 10, 10, cor=CINZA)

            if produto["perdidas"] is not None:
                self.texto(f"Perdidas {numero(produto['perdidas'])}", MARGEM_X + 120, 10, cor=CINZA)
                self.texto(f"Contabilizadas {numero(produto['contabilizadas'])}", MARGEM_X + 230, 10, cor=CINZA)

            self.y += 5

            if produto["promocoes"] > 0:
                self.y += 10
                self.texto(f"Promoção {numero(produto['promocoes'])}", MARGEM_X + 10, 10, cor=CINZA)
                self.texto(moeda(produto["valor promocoes"]), LARGURA - MARGEM_X, 10, cor=CINZA, alinhamento="direita")
                self.y += 5

            self.espaco(28)

    def desenhar(self):

        self.cabecalho()

        if "produtos_salvos" in self.resultado:
            self.bloco_produtos_salvos()
        else:
            self.bloco_equipamentos()
            self.bloco_encadernacao()

        self.bloco_totais()
        self.bloco_avisos()
        self.bloco_observacoes()


def gerar_pdf_relatorio(resultado, observacoes="", caminho=None, emitido_em=None):

    if not caminho:
        raise ValueError("Escolha onde salvar o PDF do relatório.")

    caminho = Path(caminho)

    if caminho.suffix.lower() != ".pdf":
        caminho = caminho.with_name(caminho.name + ".pdf")

    caminho.parent.mkdir(parents=True, exist_ok=True)

    emitido_em = emitido_em or datetime.now()

    c = canvas.Canvas(str(caminho), pagesize=A4)
    c.setTitle("Relatório do dia - Reprografia BPAV")
    c.setAuthor("SISREPO")

    Relatorio(c, resultado, observacoes, emitido_em).desenhar()

    c.showPage()
    c.save()

    return caminho


def gerar_pdf_relatorio_salvo(relatorio, caminho):

    # recebe o relatório como vem do storage_service (dados gravados no banco) e monta o mesmo layout do PDF original
    emitido_em = datetime.strptime(relatorio["data"], "%d/%m/%Y %H:%M:%S")

    promocoes = {}

    for promo in relatorio.get("registros_promocoes", []):
        quantidade, valor = promocoes.get(promo["produto"], (0, 0))
        promocoes[promo["produto"]] = (quantidade + promo["quantidade"], valor + promo["valor_total"])

    produtos = [
        ("Cópias", relatorio["copias"], relatorio["perdidas_copias"], relatorio["copias_contabilizadas_no_dia"], relatorio["total_real_copias"]),
        ("Impressão", relatorio["impressoes"], relatorio["perdidas_impressoes"], relatorio["impressoes_contabilizadas_no_dia"], relatorio["total_real_impressoes"]),
        ("Digitalização", relatorio["digitalizacao"], relatorio["perdidas_digitalizacao"], relatorio["digitalizacao_contabilizadas_no_dia"], relatorio["total_real_digitalizacao"]),
        ("Encadernação", relatorio["encadernacao"], None, None, relatorio["total_real_encadernacao"]),
    ]

    produtos_salvos = []
    total_geral = 0

    for nome, feitas, perdidas, contabilizadas, total in produtos:

        promocoes_produto, valor_promocoes = promocoes.get(nome, (0, 0))

        produtos_salvos.append({
            "nome": nome,
            "feitas": feitas or 0,
            "perdidas": perdidas,
            "contabilizadas": contabilizadas,
            "total": total,
            "promocoes": promocoes_produto,
            "valor promocoes": valor_promocoes,
        })

        total_geral += total

    resultado = {
        "operador": relatorio["operador"],
        "turno": relatorio["turno"],
        "data": emitido_em,
        "equipamentos": [],
        "produtos_salvos": produtos_salvos,
        "total_geral": total_geral,
        "total pix": relatorio["total_pix"],
        "pagamentos pix": relatorio["registros_pix"],
        "total especie": total_geral - relatorio["total_pix"],
        "avisos": [],
    }

    return gerar_pdf_relatorio(resultado, relatorio["observacoes"], caminho, emitido_em)
