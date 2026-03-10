import os
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Query, status, Depends
import logging

from app.schemas.files import PresignedPostResponse
from app.utils.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["Files"])

@router.post(
    "/upload-url",
    response_model=PresignedPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gera uma URL pré-assinada segura para upload direto no R2",
)
def create_presigned_post(
    file_name: str = Query(..., description="Nome original do arquivo"),
    content_type: str = Query(..., description="MIME type (ex: application/pdf)"),
    current_user: User = Depends(get_current_user)  # 1. A PORTA ESTÁ TRANCADA
):
    """
    Gera credenciais POST seguras para o front-end enviar arquivos diretamente ao Cloudflare R2.
    """
    bucket_name = os.environ.get("R2_BUCKET_NAME")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

    if not all([bucket_name, account_id, access_key, secret_key]):
        logger.error("Vazamento de variáveis de ambiente do Cloudflare R2.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuração de armazenamento ausente no servidor.",
        )

    # 2. PREVENÇÃO DE COLISÃO: Higieniza o nome e injeta um UUID e o ID do usuário
    safe_name = file_name.replace(" ", "_")
    unique_object_name = f"uploads/users/{current_user.id}/{uuid.uuid4().hex}_{safe_name}"

    # 3. INFRAESTRUTURA R2: Forçando o endpoint da Cloudflare e a região correta
    s3_client = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )

    # 4. TRAVA DE TAMANHO: Assinatura criptográfica travada em 5MB (5242880 bytes)
    fields = {"Content-Type": content_type}
    conditions = [
        {"Content-Type": content_type},
        ["content-length-range", 1, 5242880] 
    ]

    try:
        response = s3_client.generate_presigned_post(
            Bucket=bucket_name,
            Key=unique_object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=3600, # A URL morre em 1 hora
        )
    except ClientError as e:
        logger.error(f"Erro ao gerar assinatura do R2: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao estabelecer conexão segura para upload.",
        ) from e

    return response