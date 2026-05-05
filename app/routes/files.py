import os
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.schemas.files import UploadUrlRequest, UploadUrlResponse
import logging

from app.utils.security import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/files", tags=["Files"])

@router.post(
    "/upload-url",
    response_model=UploadUrlResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gera uma URL pré-assinada segura para upload direto no R2",
)
def create_presigned_put(
    payload: UploadUrlRequest,
    current_user: User = Depends(get_current_user)
):
    bucket_name = os.environ.get("R2_BUCKET_NAME")
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY_ID")
    secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

    if not all([bucket_name, account_id, access_key, secret_key]):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuração de armazenamento ausente no servidor.",
        )

    # Prevenção de Colisão
    safe_name = payload.file_name.replace(" ", "_")
    unique_object_name = f"uploads/users/{current_user.id}/{uuid.uuid4().hex}_{safe_name}"

    s3_client = boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="auto",
    )

    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod='put_object',
            Params={
                'Bucket': bucket_name,
                'Key': unique_object_name,
                'ContentType': payload.content_type
            },
            ExpiresIn=3600
        )
    except ClientError as e:
        logger.error(f"Erro ao gerar assinatura do R2: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao estabelecer conexão segura para upload.",
        ) from e

    public_base_url = "https://pub-772a5d293cb64e0fb615a61ac0ca867a.r2.dev"

    return UploadUrlResponse(
        upload_url=presigned_url,
        method="PUT",
        file_url=f"{public_base_url}/{unique_object_name}"
    )