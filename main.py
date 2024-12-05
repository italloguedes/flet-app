import flet as ft
import psycopg2
from psycopg2 import sql
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

# Configuração do Banco de Dados
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
}

# Configuração do servidor de e-mail
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

# Inicialização do banco de dados
def init_db():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

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
                dia_atual TIMESTAMP,
                horario TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO usuarios (nome, email, senha)
            SELECT 'Admin', 'admin@admin.com', 'admin123'
            WHERE NOT EXISTS (
                SELECT 1 FROM usuarios WHERE email = 'admin@admin.com'
            )
            """
        )
        conn.commit()
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        cursor.close()
        conn.close()

# Função para enviar e-mails
def enviar_email(destinatario, nome):
    assunto = "Confirmação de Atendimento"
    mensagem = f"""
    <html>
    <body>
        <h1>Olá {nome},</h1>
        <p>Seu atendimento foi realizado com sucesso!</p>
    </body>
    </html>
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(mensagem, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, destinatario, msg.as_string())

        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# View de Login
def login_view(page):
    def validar_login(e):
        email = email_field.value.strip()
        senha = senha_field.value.strip()

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
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        if user:
            page.clean()
            cadastro_atendimento_view(page)
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Login ou senha inválidos!", color="red"))
            page.snack_bar.open = True
            page.update()

    email_field = ft.TextField(label="Email", autofocus=True, width=300)
    senha_field = ft.TextField(label="Senha", password=True, width=300)
    login_btn = ft.ElevatedButton(
        text="Entrar",
        on_click=validar_login,
        style=ft.ButtonStyle(color="white", bgcolor="#007BFF")
    )

    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Login", size=30, weight="bold", color="#333"),
                    email_field,
                    senha_field,
                    login_btn
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            padding=30,
            bgcolor="#F5F5F5",
            border_radius=10
        )
    )

# View de Cadastro de Atendimento
def cadastro_atendimento_view(page):
    def cadastrar_atendimento(e):
        nome = nome_field.value
        cpf = cpf_field.value
        email = email_field.value
        solicitante = solicitante_field.value
        dia_atual = datetime.now()
        horario = datetime.now()

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO atendimentos (nome, cpf, email, solicitante, dia_atual, horario)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (nome, cpf, email, solicitante, dia_atual, horario)
            )
            conn.commit()

            enviar_email(email, nome)
            page.snack_bar = ft.SnackBar(ft.Text("Atendimento cadastrado com sucesso!", color="green"))
            page.snack_bar.open = True
        except Exception as ex:
            print(f"Erro ao cadastrar atendimento: {ex}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    nome_field = ft.TextField(label="Nome")
    cpf_field = ft.TextField(label="CPF")
    email_field = ft.TextField(label="Email")
    solicitante_field = ft.TextField(label="Solicitante")
    cadastro_btn = ft.ElevatedButton(
        text="Cadastrar",
        on_click=cadastrar_atendimento,
        style=ft.ButtonStyle(color="white", bgcolor="#28A745")
    )

    page.add(
        ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Cadastro de Atendimento", size=30, weight="bold", color="#333"),
                    nome_field,
                    cpf_field,
                    email_field,
                    solicitante_field,
                    cadastro_btn
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            alignment=ft.alignment.center,
            padding=30,
            bgcolor="#F5F5F5",
            border_radius=10
        )
    )

# Inicialização do App
def main(page):
    page.title = "Sistema de Atendimentos"
    page.theme_mode = "light"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    init_db()
    login_view(page)

ft.app(target=main)
