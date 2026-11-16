
import os
import psycopg2 
from dotenv import load_dotenv 

class Database:
    
    def __init__(self, ao_progredir=None):

        # função opcional que a tela de carregamento usa para receber o progresso
        self.ao_progredir = ao_progredir or (lambda porcentagem, mensagem: None)
        
        #pega as informações do .env
        load_dotenv()

        #pega os dados de conexão do .env (senha, host, usuario, etc...) e atribui as variaveis seguintes
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASS")
        self.port = os.getenv("DB_PORT")

        #dados de api
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")

        print("HOST:", repr(self.host))
        print("USER:", repr(self.user))
        print("PORT:", repr(self.port))

        try:
            # abre a conexao com o supabase na nuvem, aqui a conexao com o banco começa
            self.ao_progredir(5, "Conectando ao banco de dados...")
            self.conexao = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port,
                connect_timeout=10  # desiste em 10s em vez de esperar para sempre
            )
            self.ao_progredir(35, "Conexão estabelecida")

            self.cursor = self.conexao.cursor()

            # Define o fuso horário da conexão como horário de Brasília
            self.cursor.execute("SET TIME ZONE 'America/Sao_Paulo';")

            # Cria e estrutura as tabelas no supabase se elas nao existirem, caso ja existam, ele nao faz nada
            self.ao_progredir(40, "Verificando tabelas...")
            self.organizar_banco()
            self.ao_progredir(85, "Iniciando Sistema...")
            print("Conexão única com o banco de dados estabelecida com sucesso!")

        except Exception as e:
            print(f"Erro crítico ao tentar conectar ao banco de dados: {e}")
            # repassa o erro para a tela de carregamento mostrar a falha
            raise

    def organizar_banco(self):

        # Tabela de operadores
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS operadoresRepografia (
                id SERIAL PRIMARY KEY,
                nomeCompleto TEXT NOT NULL,
                dataNascimento DATE,
                cargoOuFuncao TEXT,
                turnoLotado TEXT,
                matricula TEXT UNIQUE,
                dataCadastroSistema TIMESTAMP DEFAULT NOW()
            )
        """)

        # Tabela de valores
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS valoresProdut (
                id SERIAL PRIMARY KEY,
                produto TEXT UNIQUE,
                valor NUMERIC(10, 2)
            )
        """)

        # Tabela de relatórios
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS relatorio (
                id SERIAL PRIMARY KEY,
                data TIMESTAMP DEFAULT NOW(),
                operadorResponsavel TEXT,
                turno TEXT,
                
                copias INTEGER,
                perdidasCopias INTEGER,
                totalCopias INTEGER,
                totalRealCopias NUMERIC(10, 2),
                
                impressoes INTEGER,
                perdidasImpressoes INTEGER,
                totalImpressoes INTEGER,
                totalRealImpressoes NUMERIC(10, 2),
                
                digitalizacao INTEGER,
                perdidasDigitalizacao INTEGER,
                totalDigitalizacao INTEGER,
                totalRealDigitalizacao NUMERIC(10, 2),
                            
                encadernacao INTEGER,
                totalRealEncadernacao NUMERIC(10, 2),

                observacoes TEXT
                
            )
        """)

        # bancos criados antes da coluna de observações: adiciona a coluna sem mexer nos dados existentes
        self.cursor.execute("ALTER TABLE relatorio ADD COLUMN IF NOT EXISTS observacoes TEXT")

        #tabela com informações de pix
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrosPix (
                id SERIAL PRIMARY KEY,
                dataEHora TIMESTAMP DEFAULT NOW(),
                operadorResponsavel TEXT,
                turno TEXT,
                nomeDoPagador TEXT,
                valor NUMERIC(10, 2)
            )
        """)

        #tabelo com registros de promocoes feitas pelos operadores
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrosPromocoes(
                id SERIAL PRIMARY KEY,
                dataEHora TIMESTAMP DEFAULT NOW(),
                operadorResponsavel TEXT,
                turno TEXT,
                produto TEXT,
                quantidade INT,
                valorUnitario NUMERIC(10, 2),
                valorTotal NUMERIC(10, 2)
            )
        """)

        # Tabela de equipamentos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS equipamentosInformacoes (
                id SERIAL PRIMARY KEY,
                nome TEXT,
                copia BOOLEAN,
                totalCopias INTEGER,
                imprime BOOLEAN,
                totalImpressoes INTEGER,
                scaneia BOOLEAN,
                totalDigitalizacao INTEGER,
                painelControle TEXT,
                pausado BOOLEAN,
                dataHoraCadastroSistema TIMESTAMP DEFAULT NOW()
            )
        """)

        #Tabela com historico de logins dos operadores
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS registrosLoguin (
                id SERIAL PRIMARY KEY,
                dataHora TIMESTAMP DEFAULT NOW(),
                nomeOperador TEXT,
                turno TEXT,
                matriculaOperador TEXT,
                acao BOOLEAN
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuariosInformacoes (
                id SERIAL PRIMARY KEY,
                dataHoraCadastro TIMESTAMP DEFAULT NOW(),
                nome TEXT,
                matricula INTEGER,
                nomeUsuario TEXT, 
                turno TEXT,
                senha TEXT
            )
        """)    

        # Salva as alterações na nuvem (supabase)
        self.conexao.commit()

    def salvar(self):
        #Salva as alterações feitas pelos repositórios ou qualquer outra parte do codigo, repositorios por padrao
        self.conexao.commit()

    def fechar(self):
        #Fecha a conexão com segurança ao fechar o programa
        self.cursor.close()
        self.conexao.close()
