import json
from pathlib import Path

class EquipamentosService():

    def __init__(self, database_service):
        self.equipamentos_repository = database_service.equipamentos_repository


    def consultar_equipamentos_cadastrados(self):

        equipamentos = self.equipamentos_repository.buscar_todos_os_dados()

        equipamentos_organizados = {}

        for equipamento in equipamentos:
            
            equipamento_id = equipamento[0]
            equipamento_nome = equipamento[1]
            equipamento_copia = equipamento[2]
            equipamento_imprime = equipamento[4]
            equipamento_scaneia = equipamento[6]
            equipamento_painel_controle = equipamento[8]
            equipamento_pausado = equipamento[9]

            equipamentos_organizados[equipamento_id] = {
                "nome": equipamento_nome,
                "copia": equipamento_copia,
                "imprime": equipamento_imprime,
                "scaneia": equipamento_scaneia,
                "painel_controle": equipamento_painel_controle,
                "pausado": equipamento_pausado
            }

        return equipamentos_organizados

    def consultar_informacoes_equipamento(self, id, nome):

        dados = {}

        id_equipamento = id
        nome_equipamento = nome

        dados["id"] = id_equipamento
        dados["nome"] = nome_equipamento

        informacoes = self.equipamentos_repository.buscar_equipamento_por_filtro(dados)

        return informacoes

    def cadastrar_novo_equipamento(self, nome, copia, totalCopias, imprime, totalImpressoes, scaneia, totalDigitalizacao,  painel_controle):

        if not nome:
            raise ValueError("O campo 'nome' é obrigatório.")

        if not imprime and not copia and not scaneia:
            raise ValueError("É necessário informar as funcionalidades do equipamento para ser cadastrado.")

        dados = {}

        dados["nome"] = nome
        dados["copia"] = copia
        dados["totalCopias"] = totalCopias or 0
        dados["imprime"] = imprime
        dados["totalImpressoes"] = totalImpressoes or 0
        dados["scaneia"] = scaneia
        dados["totalDigitalizacao"] = totalDigitalizacao or 0
        dados["painelControle"] = painel_controle

        self.equipamentos_repository.cadastrar_novo_equipamento(dados)

        """
        TAMBEM PODERIA FICAR NO FORMATO:

        dados = {
            "nome": nome,
            "copia": copia,
            "totalCopias": totalCopias or 0,
            "imprime": imprime,
            "totalImpressoes": totalImpressoes or 0,
            "scaneia": scaneia,
            "totalDigitalizacao": totalDigitalizacao or 0,
            "painelControle": painel_controle
        }
        """

    def pausar_equipamento(self, id):

        if not id:
            raise ValueError("Não foi possível pausar o equipamento.")

        self.equipamentos_repository.equipamento_pausado_ou_ativo(id, True)


    def ativar_equipamento(self, id):

        if not id:
            raise ValueError("Não foi possível ativar o equipamento.")

        self.equipamentos_repository.equipamento_pausado_ou_ativo(id, False)

   
    def deletar_equipamento(self, id):

        if not id:
            raise ValueError("Não foi possível deletar o equipamento.")

        self.equipamentos_repository.deletar_equipamento(id)

    
    def consultar_equipamento_por_id(self, id):

        resultado = self.equipamentos_repository.buscar_equipamento_por_filtro({"id": id})

        if not resultado:
            raise ValueError("Equipamento não encontrado. Ele pode ter sido deletado.")

        equipamento = resultado[0]

        return {
            "id": equipamento[0],
            "nome": equipamento[1],
            "copia": bool(equipamento[2]),
            "totalCopias": equipamento[3] or 0,
            "imprime": bool(equipamento[4]),
            "totalImpressoes": equipamento[5] or 0,
            "scaneia": bool(equipamento[6]),
            "totalDigitalizacao": equipamento[7] or 0,
            "painel_controle": equipamento[8],
            "pausado": bool(equipamento[9]),
        }


    def alterar_dados_equipamento(self, id, nome, total_copias, total_impressoes, total_digitalizacao):

        if not nome:
            raise ValueError("O campo 'nome' é obrigatório.")

        if min(total_copias, total_impressoes, total_digitalizacao) < 0:
            raise ValueError("Os totais não podem ser negativos.")

        equipamento = self.consultar_equipamento_por_id(id)

        dados = {"nome": nome}

        if equipamento["copia"]:
            dados["totalCopias"] = total_copias

        if equipamento["imprime"]:
            dados["totalImpressoes"] = total_impressoes

        if equipamento["scaneia"]:
            dados["totalDigitalizacao"] = total_digitalizacao

        self.equipamentos_repository.atualizar_equipamento(id, dados)



        