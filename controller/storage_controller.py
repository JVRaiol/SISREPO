class StorageController():
 
    def __init__(self, widgets, storage_service):
         
         self.storage_service = storage_service
         self.widgets = widgets

    def consultar_arquivos_publicos(self):

        arquivos = self.storage_service.consultar_arquivos_publicos()

        return arquivos

    def consultar_ultimos_10_relatorios(self):

        relatorios = self.storage_service.consultar_ultimos_10_relatorios()

        return relatorios

    def consultar_relatorios_por_data_e_turno(self, data, turno):

        relatorios = self.storage_service.consultar_relatorios_por_data_e_turno(data, turno)

        return relatorios

    def baixar_arquivo(self, nome, destino):

        return self.storage_service.baixar_arquivo(nome, destino)

    def gerar_pdf_relatorio(self, relatorio, destino):

        return self.storage_service.gerar_pdf_relatorio(relatorio, destino)