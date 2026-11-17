from service.relatorio_pdf import gerar_pdf_relatorio
import json

class RelatorioService:

    def __init__(self, database_service):

        self.relatorio_repository = database_service.relatorio_repository
        self.registro_promo_repository = database_service.registros_promo_repository
        self.equipamentos_repository = database_service.equipamentos_repository
        self.valores_repository = database_service.valores_repository
        self.registros_pix_repository = database_service.registros_pix_repository

    def calcular_relatorio(self, equipamentos, operador, turno, data, encadernacao=0):

        produtos = ("Cópias", "Impressão", "Digitalização", "Encadernação")
        valores = {}
        contador = []

        for produto in produtos:

            valor = self.valores_repository.buscar_valor_por_produto(produto)

            valores[produto] = valor[2]

        for equipamento in equipamentos:

            nome_equipamento = equipamento["nome"]

            busca = self.equipamentos_repository.buscar_equipamento_por_filtro({"nome": nome_equipamento})[0]

            contador_equipamento = {}
            contador_equipamento["id"] = busca[0]
            contador_equipamento["nome"] = nome_equipamento
            contador_equipamento["copias"] = busca[3] or 0
            contador_equipamento["impressoes"] = busca[5] or 0
            contador_equipamento["digitalizacoes"] = busca[7] or 0

            contador.append(contador_equipamento)

            copias = equipamento.get("copias") or contador_equipamento["copias"]
            impressoes = equipamento.get("impressoes") or contador_equipamento["impressoes"]
            digitalizacoes = equipamento.get("digitalizacoes") or contador_equipamento["digitalizacoes"]

            perdidas_copias = equipamento.get("perdidas copias") or 0
            perdidas_impressoes = equipamento.get("perdidas impressoes") or 0
            perdidas_digitalizacoes = equipamento.get("perdidas digitalizacoes") or 0

            if copias < contador_equipamento["copias"] or impressoes < contador_equipamento["impressoes"] or digitalizacoes < contador_equipamento["digitalizacoes"]:
                raise ValueError("O total novo não pode ser menor que o total anterior")

            if ( (copias - contador_equipamento["copias"] == 0 and perdidas_copias != 0) or (perdidas_copias > copias - contador_equipamento["copias"]) ) or ( (impressoes - contador_equipamento["impressoes"] == 0 and perdidas_impressoes != 0) or (perdidas_impressoes > impressoes - contador_equipamento["impressoes"]) ) or ( (digitalizacoes - contador_equipamento["digitalizacoes"] == 0 and perdidas_digitalizacoes != 0) or (perdidas_digitalizacoes > digitalizacoes - contador_equipamento["digitalizacoes"]) ):
                raise ValueError("Não é possível que páginas perdidas tenham mais quantidades que a quantidade de produtos")

            else:

                contador_equipamento["total copias"] = copias - contador_equipamento["copias"]
                contador_equipamento["total impressoes"] = impressoes - contador_equipamento["impressoes"]
                contador_equipamento["total digitalizacoes"] = digitalizacoes - contador_equipamento["digitalizacoes"]

                contador_equipamento["perdidas copias"] = perdidas_copias
                contador_equipamento["perdidas impressoes"] = perdidas_impressoes
                contador_equipamento["perdidas digitalizacoes"] = perdidas_digitalizacoes

        promocoes = self.registro_promo_repository.buscar_registro_por_operador_data_e_turno(data, operador, turno)

        promo_quantidade = {}
        promo_valor = {}

        for produto in produtos:

            promo_quantidade[produto] = 0
            promo_valor[produto] = 0

        for promocao in promocoes:

            promo_quantidade[promocao[4]] += promocao[5]
            promo_valor[promocao[4]] += promocao[7]

        chaves = {"Cópias": "copias", "Impressão": "impressoes", "Digitalização": "digitalizacoes"}

        resumo = {}
        avisos = []

        for produto, chave in chaves.items():

            feitas = 0
            perdidas = 0
            total_produto = 0

            for contador_equipamento in contador:

                contador_equipamento[f"liquido {chave}"] = contador_equipamento[f"total {chave}"] - contador_equipamento[f"perdidas {chave}"]
                contador_equipamento[f"promo {chave}"] = 0

                feitas += contador_equipamento[f"total {chave}"]
                perdidas += contador_equipamento[f"perdidas {chave}"]
                total_produto += contador_equipamento[f"liquido {chave}"]

            quantidade_promo = promo_quantidade[produto]

            if quantidade_promo > total_produto:
                avisos.append(f"As promoções de {produto} ({quantidade_promo}) são maiores que o total contabilizável ({total_produto}).")

            ordenados = sorted(contador, key=lambda eq: eq[f"total {chave}"], reverse=True)

            for contador_equipamento in ordenados:

                retirar = min(quantidade_promo, contador_equipamento[f"liquido {chave}"])
                contador_equipamento[f"promo {chave}"] = retirar
                quantidade_promo -= retirar

            promo_aplicada = promo_quantidade[produto] - quantidade_promo

            if promo_aplicada == promo_quantidade[produto]:
                valor_promo_aplicado = promo_valor[produto]
            else:
                valor_promo_aplicado = promo_valor[produto] * promo_aplicada / promo_quantidade[produto]

            for contador_equipamento in contador:

                contador_equipamento[f"normais {chave}"] = contador_equipamento[f"liquido {chave}"] - contador_equipamento[f"promo {chave}"]
                contador_equipamento[f"valor {chave}"] = contador_equipamento[f"normais {chave}"] * valores[produto]

            vendidas_normais = total_produto - promo_aplicada
            total_arrecadado = vendidas_normais * valores[produto] + valor_promo_aplicado

            resumo[produto] = {"feitas": feitas, "perdidas": perdidas, "vendidas normais": vendidas_normais, "promocoes": promo_aplicada, "valor promocoes": valor_promo_aplicado, "valor unitario": valores[produto], "total": total_arrecadado}

        quantidade_promo = promo_quantidade["Encadernação"]

        if quantidade_promo > encadernacao:
            avisos.append(f"As promoções de Encadernação ({quantidade_promo}) são maiores que o total encadernado ({encadernacao}).")

        promo_aplicada = min(quantidade_promo, encadernacao)

        if promo_aplicada == quantidade_promo:
            valor_promo_aplicado = promo_valor["Encadernação"]
        else:
            valor_promo_aplicado = promo_valor["Encadernação"] * promo_aplicada / quantidade_promo

        vendidas_normais = encadernacao - promo_aplicada
        total_arrecadado = vendidas_normais * valores["Encadernação"] + valor_promo_aplicado

        resumo["Encadernação"] = {"feitas": encadernacao, "perdidas": 0, "vendidas normais": vendidas_normais, "promocoes": promo_aplicada, "valor promocoes": valor_promo_aplicado, "valor unitario": valores["Encadernação"], "total": total_arrecadado}

        total_geral = 0

        for produto in resumo:

            total_geral += resumo[produto]["total"]

        registros_pix = self.registros_pix_repository.buscar_registro_por_operador_data_e_turno(data, operador, turno)

        total_pix = 0
        pagamentos_pix = []

        for registro_pix in registros_pix:

            valor_pix = registro_pix[5]
            total_pix += valor_pix
            pagamentos_pix.append({"nome": registro_pix[4], "valor": valor_pix})

        total_especie = total_geral - total_pix

        return {"operador": operador, "turno": turno, "data": data, "equipamentos": contador, "resumo": resumo, "total_geral": total_geral, "total pix": total_pix, "pagamentos pix": pagamentos_pix, "total especie": total_especie, "avisos": avisos}

    def gerar_relatorio(self, equipamentos, operador, turno, data, encadernacao=0, observacoes="", destino=None):

        resultado = self.calcular_relatorio(equipamentos, operador, turno, data, encadernacao)

        observacoes = (observacoes or "").strip()

        caminho_pdf = gerar_pdf_relatorio(resultado, observacoes, destino)

        resumo = resultado["resumo"]

        dados = {}

        dados["operadorResponsavel"] = operador
        dados["turno"] = turno

        dados["copias"] = resumo["Cópias"]["feitas"]
        dados["perdidasCopias"] = resumo["Cópias"]["perdidas"]
        dados["totalCopias"] = resumo["Cópias"]["feitas"] - resumo["Cópias"]["perdidas"]
        dados["totalRealCopias"] = round(resumo["Cópias"]["total"], 2)

        dados["impressoes"] = resumo["Impressão"]["feitas"]
        dados["perdidasImpressoes"] = resumo["Impressão"]["perdidas"]
        dados["totalImpressoes"] = resumo["Impressão"]["feitas"] - resumo["Impressão"]["perdidas"]
        dados["totalRealImpressoes"] = round(resumo["Impressão"]["total"], 2)

        dados["digitalizacao"] = resumo["Digitalização"]["feitas"]
        dados["perdidasDigitalizacao"] = resumo["Digitalização"]["perdidas"]
        dados["totalDigitalizacao"] = resumo["Digitalização"]["feitas"] - resumo["Digitalização"]["perdidas"]
        dados["totalRealDigitalizacao"] = round(resumo["Digitalização"]["total"], 2)

        dados["encadernacao"] = resumo["Encadernação"]["feitas"]
        dados["totalRealEncadernacao"] = round(resumo["Encadernação"]["total"], 2)

        dados["observacoes"] = observacoes or None

        dados["detalhesEquipamentos"] = json.dumps({
            "equipamentos": resultado["equipamentos"],
            "resumo": resultado["resumo"],
            "total_geral": resultado["total_geral"],
            "avisos": resultado["avisos"],
        }, default=float)   # default=float serve para converter Decimal em float, caso contrário, o json.dumps vai quebrar a aplicação

        totais_antigos = []
        totais_novos = []

        for equipamento in resultado["equipamentos"]:

            totais_antigos.append((equipamento["id"], equipamento["copias"], equipamento["impressoes"], equipamento["digitalizacoes"]))
            totais_novos.append((
                equipamento["id"],
                equipamento["copias"] + equipamento["total copias"],
                equipamento["impressoes"] + equipamento["total impressoes"],
                equipamento["digitalizacoes"] + equipamento["total digitalizacoes"],
            ))

        try:
            self.equipamentos_repository.atualizar_totais(totais_novos)

            try:
                self.relatorio_repository.gerar_novo_relatorio(dados)
            except Exception:

                self.equipamentos_repository.atualizar_totais(totais_antigos)
                raise

        except Exception:

            caminho_pdf.unlink(missing_ok=True)
            raise

        return caminho_pdf

    def consultar_equipamentos_para_relatorio(self):

        equipamentos = []

        for equipamento in self.equipamentos_repository.buscar_todos_os_dados():

            if equipamento[9]:
                continue

            equipamentos.append({"nome": equipamento[1], "copia": equipamento[2], "total_copias": equipamento[3] or 0, "imprime": equipamento[4], "total_impressoes": equipamento[5] or 0, "scaneia": equipamento[6], "total_digitalizacoes": equipamento[7] or 0, "painel_controle": equipamento[8] or None})

        return equipamentos