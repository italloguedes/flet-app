import flet as ft
import psycopg2
from psycopg2 import sql
from datetime import datetime

# Configuração do Banco de Dados no Supabase
DB_CONFIG = {
    "host": "aws-0-us-west-1.pooler.supabase.com",
    "port": 6543,
    "dbname": "postgres",
    "user": "postgres.gfxabtythrcxoyykzcxi",
    "password": "MIp6cj7zla9MlZoR"  # Substitua pelo password real
}

def init_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        # Criação das tabelas
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome TEXT,
                email TEXT UNIQUE,
                senha TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS atendimentos (
                id SERIAL PRIMARY KEY,
                nome TEXT,
                cpf TEXT,
                email TEXT,
                solicitante TEXT,
                horario TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        cursor.close()
        conn.close()

# Tela de Login
def login_view(page):
    def validar_login(e):
        email = email_field.value
        senha = senha_field.value
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM usuarios WHERE email = %s AND senha = %s",
                (email, senha)
            )
            user = cursor.fetchone()
        except Exception as ex:
            print(f"Erro na validação do login: {ex}")
            user = None
        finally:
            cursor.close()
            conn.close()

        if user:
            page.clean()
            main_panel(page)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Login inválido!"))
            page.snack_bar.open = True
            page.update()

    email_field = ft.TextField(label="Email")
    senha_field = ft.TextField(label="Senha", password=True)
    login_btn = ft.ElevatedButton(text="Entrar", on_click=validar_login)
    page.add(ft.Column([email_field, senha_field, login_btn]))

# Tela de Cadastro de Atendimento
def cadastro_atendimento_view(page):
    def cadastrar_atendimento(e):
        nome = nome_field.value
        cpf = cpf_field.value
        email = email_field.value
        solicitante = solicitante_field.value
        horario = datetime.now()  # Preenche automaticamente com o horário atual

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO atendimentos (nome, cpf, email, solicitante, horario)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nome, cpf, email, solicitante, horario)
            )
            conn.commit()
            page.snack_bar = ft.SnackBar(ft.Text("Atendimento cadastrado com sucesso!"))
            page.snack_bar.open = True
            page.update()
        except Exception as ex:
            print(f"Erro ao cadastrar atendimento: {ex}")
        finally:
            cursor.close()
            conn.close()

    def voltar_inicio(e):
        page.clean()
        main_panel(page)

    nome_field = ft.TextField(label="Nome")
    cpf_field = ft.TextField(label="CPF")
    email_field = ft.TextField(label="Email")
    solicitante_field = ft.TextField(label="Solicitante")
    cadastrar_btn = ft.ElevatedButton(text="Cadastrar", on_click=cadastrar_atendimento)
    voltar_btn = ft.ElevatedButton(text="Voltar", on_click=voltar_inicio)

    page.add(ft.Column([
        nome_field, cpf_field, email_field, solicitante_field, cadastrar_btn, voltar_btn
    ]))

# Painel Principal
def main_panel(page):
    def abrir_consulta(e):
        pass  # Implementar função de consulta

    def abrir_cadastro(e):
        page.clean()
        cadastro_atendimento_view(page)

    def abrir_relatorio(e):
        pass  # Implementar função de relatório

    def deslogar(e):
        page.clean()
        login_view(page)

    page.add(ft.Column([
        ft.ElevatedButton("Consulta", on_click=abrir_consulta),
        ft.ElevatedButton("Cadastro de Atendimento", on_click=abrir_cadastro),
        ft.ElevatedButton("Gerar Relatório", on_click=abrir_relatorio),
        ft.ElevatedButton("Logout", on_click=deslogar)
    ]))

# Inicializar o app
def main(page: ft.Page):
    init_db()
    login_view(page)

ft.app(target=main)
