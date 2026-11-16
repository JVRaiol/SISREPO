from datetime import date, datetime


class RelatorioController():

    def __init__(self, widgets, service, janela_principal_service):

        self.service = service
        self.janela_principal_service = janela_principal_service
        self.widgets = widgets


    def listar_equipamentos(self):

        return self.service.consultar_equipamentos_para_relatorio()


    def calcular_relatorio(self, equipamentos, encadernacao):

        equipamentos_revisados, encadernacao = self.revisar_entradas(equipamentos, encadernacao)
        operador, turno, data = self.consultar_dados_do_turno()

        return self.service.calcular_relatorio(equipamentos_revisados, operador, turno, data, encadernacao)


    def gerar_relatorio(self, equipamentos, encadernacao, observacoes, destino):

        equipamentos_revisados, encadernacao = self.revisar_entradas(equipamentos, encadernacao)
        operador, turno, data = self.consultar_dados_do_turno()

        return self.service.gerar_relatorio(equipamentos_revisados, operador, turno, data, encadernacao, observacoes, destino)


    def nome_sugerido_pdf(self):

        #   nome que já aparece preenchido na janela de salvar
        _, turno, _ = self.consultar_dados_do_turno()

        return f"relatorio_{datetime.now():%Y-%m-%d_%H%M%S}_{str(turno).replace(' ', '_')}.pdf"


    def revisar_entradas(self, equipamentos, encadernacao):

        equipamentos_revisados = []

        for equipamento in equipamentos:

            revisado = {"nome": equipamento["nome"]}

            for campo, valor in equipamento.items():

                if campo == "nome":
                    continue

                try:
                    revisado[campo] = int(valor or 0)
                except ValueError:
                    # não quebra o programa enquanto o usuário digita
                    revisado[campo] = 0

            equipamentos_revisados.append(revisado)

        try:
            encadernacao = int(encadernacao or 0)
        except ValueError:
            encadernacao = 0

        return equipamentos_revisados, encadernacao


    def consultar_dados_do_turno(self):

        dados = self.janela_principal_service.consultar_dados_operador_logado()

        if dados is None:
            raise ValueError("Nenhum operador logado no sistema")

        operador = dados["nome"]
        turno = dados["turnoTrabalhado"]
        data = date.today()

        return operador, turno, data