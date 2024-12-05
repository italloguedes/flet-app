import flet as ft
import psycopg2
from psycopg2 import sql
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import hashlib
import os

# Configuração do Banco de Dados no Supabase


# Configuração do banco de dados
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),  # Usando variável de ambiente ou valor padrão
    "port": int(os.getenv("DB_PORT")),  # Usando variável de ambiente ou valor padrão
    "dbname": os.getenv("DB_NAME"),  # Usando variável de ambiente ou valor padrão
    "user": os.getenv("DB_USER"),  # Usando variável de ambiente ou valor padrão
    "password": os.getenv("DB_PASSWORD"),  # Usando variável de ambiente ou valor padrão
}

# Configuração do servidor de e-mail
SMTP_SERVER = os.getenv("SMTP_SERVER")  # Usando variável de ambiente ou valor padrão
SMTP_PORT = int(os.getenv("SMTP_PORT"))  # Usando variável de ambiente ou valor padrão
SMTP_EMAIL = os.getenv("SMTP_EMAIL")  # Usando variável de ambiente ou valor padrão
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  # Usando variável de ambiente ou valor padrão


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
                dia_atual TIMESTAMP
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

def enviar_email(destinatario, nome, cpf, tipo_email):
    assunto = ""
    mensagem = ""

    if tipo_email == "atendimento":
        assunto = "Confirmação de Atendimento - Sala Sensorial/Alece"
        mensagem = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Confirmação de Atendimento</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background-color: #f4f4f9;
                    color: #333;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: auto;
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    color: #4CAF50;
                    font-size: 24px;
                    margin-bottom: 10px;
                }}
                p {{
                    line-height: 1.6;
                    margin: 10px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 14px;
                    color: #777;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Olá {nome},</h1>
                <p>Seu atendimento foi realizado com sucesso!</p>
                <p>Importante: o prazo médio para entrega da sua CIN é de 30 dias. Fique atento ao seu e-mail!</p>
                <p>Para mais informações, entre em contato pelo telefone (85) 2180-6587.</p>
            </div>
            <div class="footer">
                &copy; {datetime.now().year} Sala Sensorial - ALECE. Todos os direitos reservados.
            </div>
        </body>
        </html>
        """
    elif tipo_email == "cin_pronta":
        assunto = "CIN Pronta para Retirada - Sala Sensorial/Alece"
        mensagem = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CIN Pronta</title>
            <style>
                body {{
                    font-family: 'Arial', sans-serif;
                    background-color: #f4f4f9;
                    color: #333;
                    margin: 0;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: auto;
                    background-color: white;
                    border-radius: 8px;
                    padding: 20px;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    color: #4CAF50;
                    font-size: 24px;
                    margin-bottom: 10px;
                }}
                p {{
                    line-height: 1.6;
                    margin: 10px 0;
                }}
                .footer {{
                    margin-top: 20px;
                    font-size: 14px;
                    color: #777;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Olá {nome},</h1>
                <p>Estamos felizes em informar que sua CIN (Carteira de Identidade Nacional) está pronta para retirada.</p>
                <p><strong>Instruções para Retirada:</strong></p>
                <p>Local: Assembleia Legislativa, Anexo III, Sala Sensorial</p>
                <p>Endereço: Av. Pontes Vieira, 2300, Fortaleza - CE</p>
                <p>Horário: 08h às 11:30 e 13h às 16h</p>
                <p>Para mais informações, entre em contato pelo telefone (85) 2180-6587.</p>
            </div>
            <div class="footer">
                &copy; {datetime.now().year} Sala Sensorial - ALECE. Todos os direitos reservados.
            </div>
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
        dia_atual = datetime.now()
        created_at = datetime.now()
        updated_at = datetime.now()

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO atendimentos (nome, cpf, email, solicitante, horario, dia_atual, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (nome, cpf, email, solicitante, horario, dia_atual, created_at, updated_at)
            )
            conn.commit()
            enviar_email(email, nome, cpf, "atendimento")
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

            # Verificar se o CPF existe na tabela atendimentos
            cursor.execute(
                """
                SELECT email, nome FROM atendimentos WHERE cpf = %s
                """,
                (cpf,)
            )
            atendimento = cursor.fetchone()

            if atendimento:
                # Capturar email e nome do registro encontrado
                destinatario, nome_atendimento = atendimento

                # Inserir a CIN na tabela de cins
                cursor.execute(
                    """
                    INSERT INTO cins (nome, cpf, status, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (nome, cpf, status, created_at, updated_at)
                )
                conn.commit()

                # Enviar e-mail de confirmação
                try:
                    enviar_email(destinatario, nome_atendimento, cpf, "cin_pronta")
                    page.snack_bar = ft.SnackBar(ft.Text("CIN cadastrada com sucesso e e-mail enviado!"))
                except Exception as ex_email:
                    print(f"Erro ao enviar e-mail: {ex_email}")
                    page.snack_bar = ft.SnackBar(ft.Text("CIN cadastrada, mas houve erro ao enviar o e-mail."))
            else:
                page.snack_bar = ft.SnackBar(ft.Text("CPF não encontrado na tabela de atendimentos."))
            
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
               
    def logout(e):
        login_view(page)

    menu = ft.AppBar(
        title=ft.Text("Gestão de Atendimentos e CIN"),
        actions=[
            ft.ElevatedButton("Consulta", on_click=lambda e: consulta_atendimentos_view(page)),
            ft.ElevatedButton("Cadastro de Atendimento", on_click=lambda e: cadastro_atendimento_view(page)),
            ft.ElevatedButton("Cadastro CINS", on_click=lambda e: cadastro_cin_view(page)),
            ft.ElevatedButton("Logout", on_click=lambda e: logout(page)),
        ]
    )
    page.appbar = menu
    page.update()
    
    
def main(page):
    page.title = "Sistema de Atendimentos"
    page.theme_mode = "dark"
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    init_db()
    login_view(page)

ft.app(target=main)