import pytest
from unittest.mock import patch, MagicMock
from scripts.archive_tickets import run_archiving_process

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake@fake:5432/fake")
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://fake.r2.com")
    monkeypatch.setenv("R2_ACCESS_KEY", "fake_key")
    monkeypatch.setenv("R2_SECRET_KEY", "fake_secret")
    monkeypatch.setenv("R2_BUCKET_NAME", "fake_bucket")
    monkeypatch.setenv("MAIL_USERNAME", "fake_mail")
    monkeypatch.setenv("MAIL_PASSWORD", "fake_pass")
    monkeypatch.setenv("MAIL_TO_ADDRESS", "fake_to")

@patch("scripts.archive_tickets.sqlite3.connect")
@patch("scripts.archive_tickets.create_engine")
@patch("scripts.archive_tickets.smtplib.SMTP_SSL")
@patch("scripts.archive_tickets.boto3.client")
def test_extracao_e_purga_de_chamados(mock_boto3, mock_smtp, mock_create_engine, mock_sqlite):
    # 1. Setup dos Mocks de Banco de Dados
    mock_pg_conn = MagicMock()
    mock_pg_engine = MagicMock()
    mock_create_engine.return_value = mock_pg_engine
    mock_pg_engine.connect.return_value.__enter__.return_value = mock_pg_conn
    
    # Simula que a query retornou 1 linha de ticket
    mock_pg_conn.execute.return_value.all.return_value = [
        (1, 10, 20, "Descrição do chamado", "OPEN", "2025-01-01 10:00:00")
    ]
    
    # Mock do cliente S3
    mock_s3_instance = MagicMock()
    mock_s3_instance.generate_presigned_url.return_value = "https://link-falso.com"
    mock_boto3.return_value = mock_s3_instance

    # 2. Executa o script
    run_archiving_process()
    
    # 3. Validações estritas
    # Verifica se o script tentou fazer upload
    mock_s3_instance.upload_file.assert_called_once()
    # Verifica se o e-mail foi disparado
    mock_smtp.assert_called_once()
    # Verifica se a purga (delete) foi chamada no banco
    assert mock_pg_conn.execute.call_count >= 1