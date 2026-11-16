import json

class janelaPrincipalController():

    def __init__(self, widgets, service):

        self.service = service
        self.widgets = widgets


    def autenticar_loguin(self, loguin, senha, turno):

        # tira espaços que o usuário possa ter deixado nas pontas do usuário (a senha não é mexida)
        loguin = loguin.strip()

        # True se o loguin deu certo, False se não deu (campos vazios e nome minúsculo vêm como ValueError)
        autenticado = self.service.autenticar_loguin(loguin, senha, turno)

        return autenticado

    #metodo utilizado para verificacao de seguranca antes de mudar a senha
    def validar_operador(self, nome_completo, num_matricula, data_nascimento): 

        nome_completo = nome_completo.strip()
        num_matricula = num_matricula.strip()
        data_nascimento = data_nascimento.strip()

        validacao = self.service.validar_operador(nome_completo, num_matricula, data_nascimento)

        return validacao

    #metodo utilizado para a mudanca da senha, após a verificacao
    def alterar_senha(self, senha_nova, confirmacao, num_matricula):

        #se a matricula for com espaços pode dar erro, aqui isso é tratado
        num_matricula = num_matricula.strip()

        # True se a senha foi alterada, False se não foi 
        alterada = self.service.alterar_senha(senha_nova, confirmacao, num_matricula)

        return alterada
    

    def buscar_valores(self, copias, impressao, digitalizacao, encadernacao):

        # produto quantidade digitada (campo vazio conta como 0)
        entradas = {
            'Cópias': int(copias or 0),
            'Impressão': int(impressao or 0),
            'Digitalização': int(digitalizacao or 0),
            'Encadernação': int(encadernacao or 0),
        }

        # só vai ao service quem tem quantidade maior que zero
        produtos = [p for p, q in entradas.items() if q > 0]
        quantidades = [entradas[p] for p in produtos]

        valores = self.service.buscar_valores_rapidos(produtos, quantidades)

        return valores
    

    def registrar_pix(self, nomePagador, valorPix):

        pagador = nomePagador.strip() #esse strip tira espaços caso forem enviados por engano pelo usuário (o banco nao aceita espaço)
        valor = float(valorPix or 0)

        dados = self.service.consultar_dados_operador_logado()

        if dados is None:
            raise ValueError("Nenhum operador logado no sistema")


        turno = dados["turnoTrabalhado"]
        operador = dados["nome"]

        self.service.registrar_pix(operador, valor, pagador, turno)


    def registrar_promocao(self, promocoes):

        promocoes_revisadas = {}

        for produto, (quantidade, valor) in promocoes.items():

            try:
                promocoes_revisadas[produto] =(int(quantidade or 0), float(valor or 0))
            except ValueError:
                raise ValueError(f"Quantidade ou valor inválido em {produto}")

        dados = self.service.consultar_dados_operador_logado()

        if dados is None:
            raise ValueError("Nenhum operador logado no sistema")

        operador = dados["nome"]
        turno = dados["turnoTrabalhado"]

        self.service.registrar_promocao(operador, turno, promocoes_revisadas)

    def calcular_promocao(self, promocoes):

        promocoes_revisadas = {}

        for produto, (quantidade, valor) in promocoes.items():

            try:
                quantidade_numero = int(quantidade or 0)
                valor_numero = float(valor or 0)
            except ValueError:
                #Nao quebra o programa enquanto o usuario digita 
                continue

            # só entra no cálculo o produto que ja tem quantidade e valor
            if quantidade_numero > 0 and valor_numero > 0:
                promocoes_revisadas[produto] = (quantidade_numero, valor_numero)

        calculo = self.service.calcular_promocao(promocoes_revisadas)

        return calculo

    def consultar_operador_logado(self):

        dados = self.service.consultar_dados_operador_logado()

        if dados is None:
            return ""

        return dados.get("nome", "")
        


                                                                          
    


