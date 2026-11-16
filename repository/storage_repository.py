from repository.database import Database
from supabase import create_client


class StorageRepository:
   
    def __init__(self, instancia_database):
        
        self.db = instancia_database
        
        self.url = self.db.url
        self.key = self.db.key

        self.cursor = self.db.cursor

        self.base_conection = create_client(self.url, self.key)


    def arquivos_publicos(self):

        arquivos = self.base_conection.storage.from_("public_folder").list(options={"limit": 15, "sortBy": {"column": "created_at", "order": "desc"}})
        lista_de_arquivos = []

        for arquivo in arquivos:
            
            nome = arquivo["name"]

            if nome == ".emptyFolderPlaceholder":
                continue   #emptuyfolderplaceholder é um arquivo que o supabase cria de forma automática quando a pasta está vazia, então não queremos que ele apareça na lista

            lista_de_arquivos.append(nome)

        
        return lista_de_arquivos

    def consultar_ultimos_10_relatorios(self):

        quantidade = 10

        comando = "SELECT * FROM relatorio ORDER BY data DESC LIMIT %s"

        self.cursor.execute(comando, (quantidade,))

        return self.cursor.fetchall()


    def consultar_relatorios_por_data_e_turno(self, data, turno):

        self.cursor.execute( "SELECT * FROM relatorio WHERE data >= %s AND data < %s::date + INTERVAL '1 day' AND turno = %s ORDER BY data DESC", (data, data, turno))

        return self.cursor.fetchall()

    
    def download_arquivo(self, nome_arquivo):

        return self.base_conection.storage.from_("public_folder").download(nome_arquivo)


    
       

    