from repository.registros_promo_repository import RegistrosPromoRepository
from repository.operadores_repository import OperadoresRepository
from repository.equipamentos_repository import EquipamentosRepository
from repository.valores_repository import valoresRepository
from repository.relatorio_repository import RelatorioRepository
from repository.registros_loguin_repository import RegistrosLoguinRepository
from repository.registros_pix_repository import RegistrosPixRepository
from service.database_service import DatabaseService
from datetime import datetime

import json
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    PASTA_DADOS = Path(os.environ.get("APPDATA", str(Path.home()))) / "SISREPO"
else:
    PASTA_DADOS = Path(__file__).resolve().parent.parent


class JanelaPrincipalService():

    def __init__(self, database_service, operador_responsavel):

        self.operador_responsavel = operador_responsavel
        self.valores_repository = database_service.valores_repository
        self.registros_pix_repository = database_service.registros_pix_repository
        self.registros_promo_repository = database_service.registros_promo_repository
        self.usuarios_informacoes_repository = database_service.usuarios_informacoes_repository
        self.operadores_repository = database_service.operadores_repository

    

    def buscar_valores_rapidos(self, produtos, quantidades):

        valores = {}
        unitarios = {}  

        for produto, quantidade in zip(produtos, quantidades):

            valor = self.valores_repository.buscar_valor_por_produto(produto)

            # produto sem preço cadastrado: interrompe em vez de gerar um total errado
            if valor is None:
                raise ValueError(f"Produto sem valor cadastrado: {produto}")

            valores[produto] = valor[2] * quantidade
            unitarios[produto] = valor[2] 

        valores["total"] = sum(valores.values())
        valores["unitarios"] = unitarios

        return valores


    def registrar_pix(self, operador, valor, pagador, turno):

        dados = {}

        #lembrando que a legenda de cada campo do dicionnario deve ter o mesmo nome da coluna para transferir ao repository
        dados["operadorResponsavel"] = operador

        dados["valor"] = valor

        dados["nomeDoPagador"] = pagador

        dados["turno"] = turno

        if dados["valor"] == 0:
            print("Não é possível registrar um pagamento com valor igual a zero.")
            raise ValueError("Não é possível registrar um pagamento com valor igual a zero.")

        else:
            self.registros_pix_repository.criar_novo_registro_pix(dados)

            

    def calcular_promocao(self, dados:dict):

        calculo = {}

        for produto, dados_produto in dados.items():

            quantidade = dados_produto[0]
            valor = dados_produto[1]

            total = quantidade * valor

            calculo[produto] = {
                "quantidade": quantidade,
                "valor_unitario": valor,
                "total": total
            }

        return calculo



    def autenticar_loguin(self, loguin, senha, turno): 

        if not loguin and not senha:
            raise ValueError("Digite o seu Usuário e Senha para realizar o login") 

        if not loguin and senha: 
            raise ValueError("Digite seu Usuário para realizar o login")

        if loguin and not senha:
            raise ValueError("Digite sua Senha para realizar o login")

        if " " in loguin and not loguin.isupper():
            raise ValueError("Caso esteja efetuando login com nome seu completo, é necessário que todas as letras sejam digitadas maiúsculas")

        if turno == "" or not turno:
            raise ValueError("Selecione o turno que você está trabalhando")

        autenticado = self.usuarios_informacoes_repository.loguin_autenticar(loguin, senha)

        #se o loguin der certo, salvará as informações do operador no arquivo json
        if autenticado == True: 
            self.salvar_operador_logado(loguin, turno)

        return autenticado


   
    def consultar_dados_operador_logado(self):

        ARQUIVO_OPERADOR = PASTA_DADOS / "registroUser.json"

        try:
            with open(ARQUIVO_OPERADOR, "r", encoding="utf-8") as arquivoJson:
                dados = json.load(arquivoJson)
                return dados

        # arquivo inexistente, vazio significa que ninguém está logado 
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            return None


    
    def salvar_operador_logado(self, loguin, turno):

        PASTA_DADOS.mkdir(parents=True, exist_ok=True)
        
        usuario = self.usuarios_informacoes_repository.buscar_dados_usuario_por_loguin(loguin)

        ARQUIVO_OPERADOR = PASTA_DADOS / "registroUser.json"

        dados = {
            "nome": usuario[2],
            "matricula": usuario[3],
            "nomeUsuario": usuario[4],
            "turnoTrabalhado": turno,
            "turnoLotado": usuario[5],
            "dataHoraLoguin": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        }
        
        with open(ARQUIVO_OPERADOR, "w", encoding="utf-8") as arquivoJson:
            json.dump(dados, arquivoJson, ensure_ascii=False, indent=4)



    def validar_operador(self, nome_completo, num_matricula, data_nascimento):

        #verifica se algum campo vai vazio
        if not nome_completo or not num_matricula or not data_nascimento:
            raise ValueError("Preencha o nome completo, o seu número de matrícula e a sua data de nascimento.")

        if not nome_completo.isupper(): 
            raise ValueError("O nome completo deve ser digitado em letra maiúscula")

        # converte o texto digitado (dd/mm/aaaa) em data de verdade
        try:
            data = datetime.strptime(data_nascimento, "%d/%m/%Y").date()
        except ValueError:
            raise ValueError("Data inválida. Use o formato dd/mm/aaaa.")

        validar = self.operadores_repository.validar_operador(nome_completo, num_matricula, data)
        return validar



    def alterar_senha(self, senha_nova, confirmacao, num_matricula):

        #aqui veriifica se algum dos campos vai vazio, não pode ir vazio o campo nova senha e nem confirmar senha
        if not senha_nova or not confirmacao:
            raise ValueError("Preencha a nova senha e a confirmação.")

        if senha_nova != confirmacao:
            raise ValueError("As senhas digitadas não são iguais.")

        # aqui é uma persistencia, só pode ir números para banco.
        if not num_matricula.isdigit():
            raise ValueError("Matrícula inválida.")

        # True se a senha foi alterada, False se não achou usuário com essa matrícula
        return self.usuarios_informacoes_repository.mudar_a_senha(senha_nova, int(num_matricula))

    

    def registrar_promocao(self, operador, turno, promocoes_revisadas):

        operador = operador.strip()
        turno = turno.strip()

        if not promocoes_revisadas:
            raise ValueError("Nenhuma promoção válida para registrar.")

        for produto, (quantidade, valor) in promocoes_revisadas.items():

            if quantidade <= 0 or valor <=0:
                raise ValueError(f"Você não pode registrar uma promoção com quantidade ou valor menor que zero para {produto}.")

        dados_para_calcular = {}

        for produto, (quantidade, valor) in promocoes_revisadas.items():

            dados_para_calcular[produto] = (quantidade, valor)

            calculo = self.calcular_promocao(dados_para_calcular)

        for produto, resultado in calculo.items():

            dados_para_registro = {
                "operadorResponsavel": operador,
                "turno": turno,
                "produto": produto,
                "quantidade": resultado["quantidade"],
                "valorUnitario": resultado["valor_unitario"],
                "valorTotal": resultado["total"]
            }

            self.registros_promo_repository.criar_novo_registro_promo(dados_para_registro)


 

       







    




            
            


