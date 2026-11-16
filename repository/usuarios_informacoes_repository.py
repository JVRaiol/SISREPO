from repository.database import Database

class usuariosInformacoesRepository():

    def __init__(self, instancia_database):

        self.db = instancia_database
        self.cursor = self.db.cursor
    
    def loguin_autenticar(self, loguin, senha): 

        erro = False
        sucesso = True

        '''como matricula é integer no banco, se o usuario entrar com um numero e a funcao fizer uma verificacao na matricula, pode dar erro. Por isso
          que é melhor fazer a verificacao logo antes de passar pro banco'''
        
        if loguin.isdigit():
            matricula = int(loguin)
            
        else:
            matricula = None


        query = """
            SELECT *
            FROM usuariosInformacoes
            WHERE nome = %s
            OR matricula = %s
            OR nomeUsuario = %s
        """

        self.cursor.execute(query, (loguin, matricula, loguin))

        usuario = self.cursor.fetchone()

        if usuario is None:
            return erro

        # a senha do usuário está na posição 6 quando retorna em forma de tupla
        if usuario[6] == senha:
            return sucesso

        return erro

    def buscar_dados_usuario_por_loguin(self, loguin):

        if loguin.isdigit():
            matricula = int(loguin)

        else:
            matricula = None

        query = """
                SELECT * FROM usuariosInformacoes
                WHERE nome = %s
                OR matricula = %s
                OR nomeUsuario = %s
                """
        
        self.cursor.execute(query, (loguin, matricula, loguin))

        return self.cursor.fetchone()

    def mudar_a_senha(self, senha_nova, num_matricula):

        erro = False
        sucesso = True

        senha = senha_nova
        matricula = num_matricula 

        query = "UPDATE usuariosInformacoes SET senha = %s WHERE matricula = %s"

        self.cursor.execute(query, (senha, matricula))

        #Caso nada tenha sido alterado no banco
        if self.cursor.rowcount == 0:
            return erro

        self.db.salvar()
        return sucesso
            
                                        