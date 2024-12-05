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

def consulta_atendimentos_view(page):
    def consultar_atendimentos(e):
        # Recupera o texto do campo de pesquisa
        consulta = consulta_field.value.strip()

        if consulta:  # Verifica se o campo de busca não está vazio
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                # Busca por nome ou CPF
                cursor.execute(
                    """
                    SELECT * FROM atendimentos
                    WHERE nome ILIKE %s OR cpf ILIKE %s
                    """,
                    (f"%{consulta}%", f"%{consulta}%")  # Pesquisa usando LIKE com '%'
                )
                atendimentos = cursor.fetchall()

                if atendimentos:
                    # Exibe os resultados encontrados
                    resultados = "\n".join([f"Nome: {a[1]}, CPF: {a[2]}, Solicitante: {a[4]}, Horário: {a[5]}" for a in atendimentos])
                    page.snack_bar = ft.SnackBar(ft.Text(f"Atendimentos encontrados:\n{resultados}"))
                    page.snack_bar.open = True
                    page.update()
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Nenhum atendimento encontrado."))
                    page.snack_bar.open = True
                    page.update()

            except Exception as ex:
                print(f"Erro ao consultar atendimentos: {ex}")
                page.snack_bar = ft.SnackBar(ft.Text("Erro ao realizar a consulta."))
                page.snack_bar.open = True
                page.update()
            finally:
                cursor.close()
                conn.close()

    consulta_field = ft.TextField(label="Nome ou CPF", width=300)
    consultar_btn = ft.ElevatedButton(text="Consultar", on_click=consultar_atendimentos)

    # Adiciona os controles da busca na tela
    page.add(
        ft.Row(
            controls=[
                ft.Column(
                    controls=[consulta_field, consultar_btn],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )
    )
    
def cadastro_cin_view(page):
    def cadastrar_cin(e):
        nome = nome_field.value
        cpf = cpf_field.value
        status = "Pronta"  # Status padrão
        created_at = datetime.now()
        updated_at = datetime.now()

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO cins (nome, cpf, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (nome, cpf, status, created_at, updated_at)
            )
            conn.commit()

            # Mostrar mensagem de sucesso
            page.snack_bar = ft.SnackBar(ft.Text("CIN cadastrada com sucesso!"))
            page.snack_bar.open = True
            page.update()

        except Exception as ex:
            print(f"Erro ao cadastrar CIN: {ex}")
            page.snack_bar = ft.SnackBar(ft.Text("Erro ao cadastrar CIN."))
            page.snack_bar.open = True
            page.update()

        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    # Campos de entrada para o cadastro de CIN
    nome_field = ft.TextField(label="Nome", width=300)
    cpf_field = ft.TextField(label="CPF", width=300)
    cadastrar_btn = ft.ElevatedButton(text="Cadastrar CIN", on_click=cadastrar_cin)

    # Adicionar campos ao layout
    page.add(
        ft.Row(
            controls=[
                ft.Column(
                    controls=[nome_field, cpf_field, cadastrar_btn],
                    spacing=20,
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )
    )


def main_panel(page):
    page.clean()  # Limpa a tela antes de adicionar os novos controles
    page.add(
        ft.Row(
            controls=[
                ft.ElevatedButton("Consulta", on_click=lambda e: consulta_atendimentos_view(page)),
                ft.ElevatedButton("Cadastro de Atendimento", on_click=lambda e: cadastro_atendimento_view(page)),
                ft.ElevatedButton("Cadastrar Cin", on_click=lambda e: cadastro_cin_view(page)),
            ],
            spacing=20
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
