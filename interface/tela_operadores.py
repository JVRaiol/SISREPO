from kivy.properties import DictProperty, ListProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from interface.caixa_de_mensagem import mensagem_sucesso, mensagem_aviso, mensagem_erro, mensagem_confirmacao


class TelaOperadores(BoxLayout):

    controller = None
    pagina = StringProperty('vazio')
    
    operadores_exibidos = ListProperty([])
    
    operador_exibido = DictProperty({
        "nome": "", "matricula": "", "cargo": "",
        "turno": "", "nascimento": "", "cadastro": "",
    })

    def buscar_operador_por_filtro(self):

        ids = self.ids

        nome = ids.campo_nome.text.strip() or None
        matricula = ids.campo_matricula.text.strip() or None
        turno = ids.campo_turno.text.strip() or None
        cargo = ids.campo_cargo.text.strip() or None

        try:
            operadores = self.controller.buscar_operador_por_filtro(
                nome=nome,
                matricula=matricula,
                turno=turno,
                cargo=cargo,
            )

        except Exception as erro:
            print(erro)
            mensagem_erro("Operadores", "Não foi possível buscar os operadores.\nTente novamente.")
            return

        self.operadores_exibidos = operadores
        self._atualizar_lista()
        self.pagina = 'lista'

    def _atualizar_lista(self):

        self.ids.lista.data = [
            {"operador_id": operador["id"], "nome": operador["nome"]}
            for operador in self.operadores_exibidos
        ]

    def mostrar_lista(self):

        self.pagina = 'lista'

    def ver_informacoes_operador(self, operador_id):

        operador = None

        for item in self.operadores_exibidos:

            if item["id"] == operador_id:
                operador = item
                break

        if operador is None:
            mensagem_aviso("Operadores", "Operador não encontrado.\nFaça a busca novamente.")
            return

        self.operador_exibido = operador
        self.pagina = 'detalhes'

    def pedir_exclusao(self):

        operador = self.operador_exibido

        mensagem_confirmacao(
            "Deletar operador",
            f"Tem certeza que deseja deletar o operador\n'{operador['nome']}'?\nEle também perderá o acesso ao sistema.\nEssa ação não pode ser desfeita.",
            ao_confirmar=lambda: self.deletar_operador(operador),
            texto_botao="Deletar",
        )

    def deletar_operador(self, operador):

        try:
            self.controller.deletar_operador(operador["id"], operador["matricula"])

        except ValueError as erro:
            mensagem_aviso("Operadores", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Operadores", "Não foi possível deletar o operador.\nTente novamente.")
            return

        self.operadores_exibidos = [item for item in self.operadores_exibidos if item["id"] != operador["id"]]
        self._atualizar_lista()
        self.pagina = 'lista'

        mensagem_sucesso("Operadores", "Operador deletado com sucesso!")

    def cadastrar_operador(self):

        ids = self.ids

        try:
            self.controller.cadastrar_operador(
                nome=ids.novo_nome.text.strip(),
                nome_usuario=ids.novo_nome_usuario.text.strip(),
                cargo=ids.novo_cargo.text.strip(),
                turno=ids.novo_turno.text.strip(),
                matricula=ids.novo_matricula.text.strip(),
                data_nascimento=ids.novo_nascimento.text.strip(),
                senha=ids.novo_senha.text.strip(),
                senha_confirmacao=ids.novo_senha_confirmar.text.strip(),
            )

        except ValueError as erro:
            mensagem_aviso("Cadastro de operador", str(erro))
            return

        except Exception as erro:
            print(erro)
            mensagem_erro("Cadastro de operador", "Não foi possível cadastrar o operador.\nTente novamente.")
            return

        ids.novo_nome.text = ""
        ids.novo_nome_usuario.text = ""
        ids.novo_cargo.text = "Selecione"
        ids.novo_turno.text = "Selecione"
        ids.novo_matricula.text = ""
        ids.novo_nascimento.text = ""
        ids.novo_senha.text = ""

        mensagem_sucesso("Cadastro de operador", "Operador cadastrado com sucesso!")