import json
from pathlib import Path
from datetime import datetime
from service.relatorio_pdf import gerar_pdf_relatorio_salvo

class StorageService():

    def __init__(self, database_service):
        
        self.storage_repository = database_service.storage_repository
        self.registros_pix_repository = database_service.registros_pix_repository
        self.relatorio_repository = database_service.relatorio_repository
        self.registros_promo_repository = database_service.registros_promo_repository

    def consultar_arquivos_publicos(self):

        arquivos = self.storage_repository.arquivos_publicos()

        return arquivos

    def consultar_ultimos_10_relatorios(self):

        relatorios = self.storage_repository.consultar_ultimos_10_relatorios()

        lista_de_relatorios = []

        for relatorio in relatorios:

            relatorio_dict = {
                "id": relatorio[0],
                "data": relatorio[1].strftime("%d/%m/%Y %H:%M:%S"),
                "operador": relatorio[2],
                "turno": relatorio[3],
                "copias": relatorio[4],
                "perdidas_copias": relatorio[5],
                "copias_contabilizadas_no_dia": relatorio[6],
                "total_real_copias": float(relatorio[7] or 0),
                "impressoes": relatorio[8],
                "perdidas_impressoes": relatorio[9],
                "impressoes_contabilizadas_no_dia": relatorio[10],
                "total_real_impressoes": float(relatorio[11] or 0),
                "digitalizacao": relatorio[12],
                "perdidas_digitalizacao": relatorio[13],
                "digitalizacao_contabilizadas_no_dia": relatorio[14],
                "total_real_digitalizacao": float(relatorio[15] or 0),
                "encadernacao": relatorio[16],
                "total_real_encadernacao": float(relatorio[17] or 0),
                "observacoes": relatorio[18] or ""
            }

            registros_pix = self.registros_promo_repository.buscar_registro_por_operador_data_e_turno(relatorio[1].date(), relatorio[2], relatorio[3])

            relatorio_dict["registros_pix"] = [{"nome": pix[4], "valor": float(pix[5] or 0)} for pix in registros_pix]
            relatorio_dict["total_pix"] = sum(p["valor"] for p in relatorio_dict["registros_pix"])

            lista_de_relatorios.append(relatorio_dict)

        return lista_de_relatorios


    def consultar_relatorios_por_data_e_turno(self, data, turno):


        if data is None or turno is None or turno.strip() == "Selecione":
            raise ValueError(f"A consulta precisa de data e turno para ser efetuada")            

        try:
            data = datetime.strptime(data.strip(), "%d/%m/%Y").date()
        except ValueError:
            raise ValueError("Data inválida. Use o formato DD/MM/AAAA.")
            
        turno = turno.strip()

        relatorios = self.storage_repository.consultar_relatorios_por_data_e_turno(data, turno)

        lista_de_relatorios = []

        for relatorio in relatorios:

            relatorio_dict = {
                "id": relatorio[0],
                "data": relatorio[1].strftime("%d/%m/%Y %H:%M:%S"),
                "operador": relatorio[2],
                "turno": relatorio[3],
                "copias": relatorio[4],
                "perdidas_copias": relatorio[5],
                "copias_contabilizadas_no_dia": relatorio[6],
                "total_real_copias": float(relatorio[7] or 0),
                "impressoes": relatorio[8],
                "perdidas_impressoes": relatorio[9],
                "impressoes_contabilizadas_no_dia": relatorio[10],
                "total_real_impressoes": float(relatorio[11] or 0),
                "digitalizacao": relatorio[12],
                "perdidas_digitalizacao": relatorio[13],
                "digitalizacao_contabilizadas_no_dia": relatorio[14],
                "total_real_digitalizacao": float(relatorio[15] or 0),
                "encadernacao": relatorio[16],
                "total_real_encadernacao": float(relatorio[17] or 0),
                "observacoes": relatorio[18] or "",
                "detalhes": json.loads(relatorio[19]) if relatorio[19] else None
            }

            registros_pix = self.registros_pix_repository.buscar_registro_por_operador_data_e_turno(relatorio[1].date(), relatorio[2], relatorio[3])

            relatorio_dict["registros_pix"] = [{"nome": pix[4], "valor": float(pix[5] or 0)} for pix in registros_pix]
            relatorio_dict["total_pix"] = sum(p["valor"] for p in relatorio_dict["registros_pix"])

            registros_promocoes = self.registros_promo_repository.buscar_registro_por_operador_data_e_turno(relatorio[1].date(), relatorio[2], relatorio[3])

            relatorio_dict["registros_promocoes"] = [{"produto": promo[4], "quantidade": promo[5], "valor_unidade": float(promo[6] or 0), "valor_total": float(promo[7] or 0)} for promo in registros_promocoes]
            relatorio_dict["total_promocoes"] = sum(p["valor_total"] for p in relatorio_dict["registros_promocoes"])

            lista_de_relatorios.append(relatorio_dict)

        return lista_de_relatorios

    def baixar_arquivo(self, nome, destino):

        conteudo = self.storage_repository.download_arquivo(nome)
        Path(destino).write_bytes(conteudo)

    def gerar_pdf_relatorio(self, relatorio, destino):

        return gerar_pdf_relatorio_salvo(relatorio, destino)

    







        