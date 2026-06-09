import sqlite3
import os
import sys
import boto3
from botocore.config import Config
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from sqlalchemy import create_engine, text

# 1. Validador Estrito de Ambiente (Permanece global, pois é apenas a definição da função)
def get_env_or_die(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        print(f"❌ ERRO FATAL: Variável de ambiente '{var_name}' não encontrada.")
        sys.exit(1)
    return value

# Variáveis globais seguras (não interagem com I/O nem dependem de .env)
SEMESTER_SUFFIX = datetime.now().strftime("%Y_S%H%M")
SQLITE_FILE = f"/tmp/auditoria_chamados_{SEMESTER_SUFFIX}.sqlite"
FILE_NAME = f"auditoria_chamados_{SEMESTER_SUFFIX}.sqlite"

def purge_old_postgres_data(pg_engine):
    print("🗑️ Iniciando purga definitiva de dados transacionais...")
    
    delete_query = text("""
        DELETE FROM tickets 
        WHERE created_at < NOW() - INTERVAL '6 months'
    """)
    
    with pg_engine.begin() as pg_conn:
        result = pg_conn.execute(delete_query)
        linhas_deletadas = result.rowcount
        
    print(f"✅ Expurgo concluído com precisão. {linhas_deletadas} tuplas mortas no PostgreSQL.")

# A função agora recebe as credenciais de e-mail explicitamente via parâmetro
def enviar_email_diretoria(url_segura: str, qtd_registros: int, mail_user: str, mail_pass: str, mail_to: str):
    msg = MIMEText(f"""Aviso de Sistema: Arquivamento Semestral Concluído.
    
Foram expurgados e arquivados {qtd_registros} chamados da base ativa.
O arquivo SQLite consolidado está disponível no link seguro abaixo (expira em 7 dias):

{url_segura}
""")
    msg["Subject"] = "🗄️ Relatório de Auditoria Disponível (Link Seguro)"
    msg["From"] = mail_user
    msg["To"] = mail_to
    
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(mail_user, mail_pass)
        server.send_message(msg)

def run_archiving_process():
    # 2. CARREGAMENTO ISOLADO DE VARIÁVEIS CRÍTICAS
    # Protegido do coletor do Pytest. Só roda quando a função é explicitamente invocada.
    DATABASE_URL = get_env_or_die("DATABASE_URL")
    R2_ENDPOINT = get_env_or_die("R2_ENDPOINT_URL")
    R2_ACCESS_KEY = get_env_or_die("R2_ACCESS_KEY")
    R2_SECRET_KEY = get_env_or_die("R2_SECRET_KEY")
    R2_BUCKET_NAME = get_env_or_die("R2_BUCKET_NAME")
    MAIL_USERNAME = get_env_or_die("MAIL_USERNAME")
    MAIL_PASSWORD = get_env_or_die("MAIL_PASSWORD") 
    MAIL_TO = get_env_or_die("MAIL_TO_ADDRESS")
    
    print(f"⚙️ Iniciando Cold Archiving: {SQLITE_FILE}")
    
    # --- FASE 1: EXTRAÇÃO E CARGA (ETL) ---
    pg_engine = create_engine(DATABASE_URL)
    sqlite_conn = sqlite3.connect(SQLITE_FILE)
    sqlite_cursor = sqlite_conn.cursor()
    
    sqlite_cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets_archived (
            id INTEGER PRIMARY KEY,
            author_id INTEGER,
            assigned_to_id INTEGER,
            description TEXT,
            status TEXT,
            created_at TIMESTAMP
        )
    """)
    
    fetch_query = text("""
        SELECT id, author_id, assigned_to_id, description, status, created_at 
        FROM tickets 
        WHERE created_at < NOW() - INTERVAL '6 months'
    """)
    
    with pg_engine.connect() as pg_conn:
        result = pg_conn.execute(fetch_query)
        rows = [tuple(row) for row in result.all()]
        
        if not rows:
            print("✅ Nenhum chamado antigo para arquivar. Processo encerrado.")
            return
        
        sqlite_cursor.executemany("""
            INSERT INTO tickets_archived 
            (id, author_id, assigned_to_id, description, status, created_at) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, rows)
        
    sqlite_conn.commit()
    sqlite_conn.close()
    print(f"📦 Sucesso! {len(rows)} chamados foram isolados no arquivo SQLite.")

    # --- FASE 2: UPLOAD E NOTIFICAÇÃO ---
    print("☁️ Iniciando upload seguro para o Cloudflare R2...")
    
    r2_client = boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version="s3v4")
    )
    
    # Faz o upload
    r2_client.upload_file(SQLITE_FILE, R2_BUCKET_NAME, FILE_NAME)
    
    # Gera a URL Assinada (7 dias)
    presigned_url = r2_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": R2_BUCKET_NAME, "Key": FILE_NAME},
        ExpiresIn=604800
    )
    
    print("📧 Disparando e-mail de notificação...")
    # Repassando as variáveis locais para a função externa
    enviar_email_diretoria(presigned_url, len(rows), MAIL_USERNAME, MAIL_PASSWORD, MAIL_TO)
    
    purge_old_postgres_data(pg_engine)
    
    print("✅ Processo de arquivamento concluído com sucesso!")

if __name__ == "__main__":
    run_archiving_process()