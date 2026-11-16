"""Conversa com o Gemini (biblioteca google-genai).

Todo o contato com o SDK do Google fica neste arquivo. O resto do projeto só enxerga "gerar uma resposta" e
"devolver o resultado das ferramentas", então trocar de IA no futuro mexe só aqui.
"""

import time


class ErroAssistente(Exception):
    # erro com mensagem já pronta para mostrar ao operador no chat
    pass


class RespostaModelo:
    def __init__(self, texto, chamadas, conteudo):
        self.texto = texto          # texto da resposta (pode ser vazio quando o modelo só pediu ferramentas)
        self.chamadas = chamadas    # lista de (nome_da_ferramenta, argumentos)
        self.conteudo = conteudo    # resposta original do modelo, que PRECISA voltar inteira para o histórico


class GeminiCliente:

    PAUSAS = (2, 5)   # esperas entre as tentativas quando o Google está sobrecarregado (3 tentativas no total)

    def __init__(self, api_key, modelo, ferramentas, tempo_limite=60):

        from google import genai
        from google.genai import errors, types

        self.errors = errors
        self.types = types
        self.modelo = modelo

        self.client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=tempo_limite * 1000))

        declaracoes = []

        for ferramenta in ferramentas.values():

            argumentos = {"name": ferramenta.nome, "description": ferramenta.descricao}

            if ferramenta.parametros:
                argumentos["parameters"] = ferramenta.parametros

            declaracoes.append(types.FunctionDeclaration(**argumentos))

        self.ferramentas = types.Tool(function_declarations=declaracoes)

    # ------------------------------------------------------------ montagem do histórico

    def mensagem_usuario(self, texto):
        return self.types.Content(role="user", parts=[self.types.Part(text=texto)])

    def mensagem_modelo(self, texto):
        return self.types.Content(role="model", parts=[self.types.Part(text=texto)])

    def resultados(self, lista):
        # lista de (nome, resultado): vira a "resposta das ferramentas" que o modelo lê
        partes = [self.types.Part.from_function_response(name=nome, response={"resultado": resultado}) for nome, resultado in lista]
        return self.types.Content(role="user", parts=partes)

    def inicio_de_turno(self, conteudo):
        # True se é uma mensagem escrita pelo operador (e não o resultado de uma ferramenta)
        if conteudo.role != "user":
            return False

        return any(parte.text for parte in conteudo.parts or []) and not any(parte.function_response for parte in conteudo.parts or [])

    # ------------------------------------------------------------ chamada

    def gerar(self, historico, instrucao):

        types = self.types

        configuracao = types.GenerateContentConfig(
            system_instruction=instrucao,
            tools=[self.ferramentas],
            # as ferramentas são executadas pelo nosso código (com confirmação), nunca automaticamente pelo SDK
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0.2,
        )

        resposta = self._com_novas_tentativas(lambda: self.client.models.generate_content(model=self.modelo, contents=historico, config=configuracao))

        candidato = resposta.candidates[0] if resposta.candidates else None

        if candidato is None or candidato.content is None or not candidato.content.parts:
            print("Resposta vazia do modelo:", getattr(candidato, "finish_reason", None))
            raise ErroAssistente("Não consegui gerar uma resposta para isso. Tente escrever de outro jeito.")

        partes = candidato.content.parts

        texto = "".join(parte.text for parte in partes if parte.text and not parte.thought)
        chamadas = [(parte.function_call.name, dict(parte.function_call.args or {})) for parte in partes if parte.function_call]

        return RespostaModelo(texto.strip(), chamadas, candidato.content)

    def _com_novas_tentativas(self, chamada):

        ultimo_erro = None

        for tentativa in range(len(self.PAUSAS) + 1):

            try:
                return chamada()

            except self.errors.APIError as erro:
                codigo = getattr(erro, "code", None)
                print(f"Erro do Gemini (tentativa {tentativa + 1}): {codigo} {erro}")

                if codigo not in (429, 500, 502, 503, 504):
                    raise ErroAssistente(self._mensagem_do_erro(codigo))

                ultimo_erro = erro

            except Exception as erro:
                # queda de internet, tempo esgotado etc. (erros do httpx)
                if type(erro).__module__.split(".")[0] not in ("httpx", "httpcore", "ssl", "socket"):
                    raise

                print(f"Erro de conexão com o Gemini (tentativa {tentativa + 1}): {erro}")
                ultimo_erro = erro

            if tentativa < len(self.PAUSAS):
                time.sleep(self.PAUSAS[tentativa])

        raise ErroAssistente(self._mensagem_do_erro(getattr(ultimo_erro, "code", None)))

    def _mensagem_do_erro(self, codigo):

        if codigo == 429:
            return "O limite de uso do assistente foi atingido por agora. Aguarde um pouco e tente de novo."

        if codigo in (401, 403):
            return "A chave do assistente não foi aceita. Confira a GEMINI_API_KEY no .env."

        if codigo == 404:
            return "O modelo configurado não foi encontrado. Confira a GEMINI_MODELO no .env."

        if codigo == 400:
            return "O assistente recusou o pedido. Tente começar uma Nova conversa."

        if codigo in (500, 502, 503, 504):
            return "O assistente está sobrecarregado agora, tente de novo em instantes."

        return "Não consegui falar com o assistente agora. Verifique a internet e tente de novo."