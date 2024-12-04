import flet as ft
import psycopg2
from psycopg2 import sql
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib

# Configuração do Banco de Dados no Supabase
DB_CONFIG = {
    "host": "aws-0-us-west-1.pooler.supabase.com",
    "port": 6543,
    "dbname": "postgres",
    "user": "postgres.gfxabtythrcxoyykzcxi",
    "password": "MIp6cj7zla9MlZoR"  # Substitua pelo password real
}

# Configuração do servidor de e-mail
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "sala.sensorial.alece@gmail.com"
SMTP_PASSWORD = "wqckvxkttebescrd"

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
        # Inserir usuário admin padrão (se não existir)
        cursor.execute(
            """
            INSERT INTO usuarios (nome, email, senha)
            SELECT 'Admin', 'admin@admin.com', %s
            WHERE NOT EXISTS (
                SELECT 1 FROM usuarios WHERE email = 'admin@admin.com'
            )
            """,
            (hashlib.sha256(b"admin123").hexdigest(),)
        )
        conn.commit()
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")
    finally:
        cursor.close()
        conn.close()

def enviar_email(destinatario, nome, cpf):
    assunto = "Sala Sensorial/Alece"
    mensagem = f"""
    Olá {nome}, {cpf}
    Seu atendimento foi feito com sucesso e o prazo para retirada é de 30 dias.

    [Instruções detalhadas]
    """
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = destinatario
        msg["Subject"] = assunto
        msg.attach(MIMEText(mensagem, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, destinatario, msg.as_string())

        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Função para hashear senha
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Funções de Tela
def login_view(page):
    def validar_login(e):
        email = email_field.value.strip()
        senha = senha_field.value.strip()
        senha_hashed = hash_password(senha)  # Gerar o hash da senha

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM usuarios WHERE email = %s AND senha = %s",
                (email, senha)  # Comparar com o hash armazenado no banco
            )
            user = cursor.fetchone()  # Buscar o usuário
        except Exception as ex:
            print(f"Erro na validação do login: {ex}")
            user = None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        if user:
            # Login bem-sucedido
            page.clean()  # Limpa a tela antes de exibir a nova view
            main_panel(page)
        else:
            # Credenciais inválidas
            page.snack_bar = ft.SnackBar(ft.Text("Login ou senha inválidos!"))
            page.snack_bar.open = True
            page.update()

    # Campos de entrada do formulário de login
    email_field = ft.TextField(label="Email", autofocus=True, width=300)
    senha_field = ft.TextField(label="Senha", password=True, width=300)
    login_btn = ft.ElevatedButton(text="Entrar", on_click=validar_login)

    # Adicionando os campos ao layout da página
    page.add(
        ft.Row(
            controls=[ 
                ft.Column(
                    controls=[email_field, senha_field, login_btn],
                    spacing=20,  # Define o espaçamento entre os campos
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True  # Expande para ocupar a tela
        )
    )

def cadastro_atendimento_view(page):
    def cadastrar_atendimento(e):
        nome = nome_field.value
        cpf = cpf_field.value
        email = email_field.value
        solicitante = solicitante_field.value
        horario = datetime.now()

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
            enviar_email(email, nome, cpf)
            page.snack_bar = ft.SnackBar(ft.Text("Atendimento cadastrado com sucesso!"))
            page.snack_bar.open = True
            page.update()
            
            # Limpa os campos após o cadastro
            nome_field.value = ""
            cpf_field.value = ""
            email_field.value = ""
            solicitante_field.value = ""
            page.update()
        except Exception as ex:
            print(f"Erro ao cadastrar atendimento: {ex}")
        finally:
            cursor.close()
            conn.close()

    nome_field = ft.TextField(label="Nome", width=300)
    cpf_field = ft.TextField(label="CPF", width=300)
    email_field = ft.TextField(label="Email", width=300)
    solicitante_field = ft.TextField(label="Solicitante", width=300)
    cadastrar_btn = ft.ElevatedButton(text="Cadastrar", on_click=cadastrar_atendimento)
    page.add(
        ft.Row(
            controls=[ 
                ft.Column(
                    controls=[nome_field, cpf_field, email_field, solicitante_field, cadastrar_btn],
                    spacing=20,  # Define o espaçamento entre os campos
                    alignment=ft.MainAxisAlignment.CENTER
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True  # Expande para ocupar a tela
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

def main_panel(page):
    page.clean()  # Limpa a tela antes de adicionar os novos controles
    page.add(
        ft.Row(
            controls=[
                ft.ElevatedButton("Consulta", on_click=lambda e: consulta_atendimentos_view(page)),
                ft.ElevatedButton("Cadastro de Atendimento", on_click=lambda e: cadastro_atendimento_view(page)),
            ],
            spacing=20
        )
    )

def main(page):
    page.title = "Sistema de Atendimento"
    login_view(page)

ft.app(target=main)
