import os
import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from ..models.reimbursement import Reimbursement, StatusRefundEnum
from ..schemas.reimbursement import ReimbursementCreate, PreSignedUrlResponse

logger = logging.getLogger(__name__)

class ReimbursementService:
    
    @staticmethod
    async def create_reimbursement(
        data: ReimbursementCreate, user_id: int, db: AsyncSession
    ) -> dict:
        """
        Cria o registro financeiro e gera a URL de upload PUT.
        """
        # 1. Higienização e Mapeamento de MIME Type
        ext = data.file_extension.lower()
        mime_types = {
            ".pdf": "application/pdf",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg"
        }
        
        if ext not in mime_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Extensão de arquivo não suportada para comprovantes."
            )
            
        content_type = mime_types[ext]

        # 2. Gera a chave do objeto no R2
        file_key = f"reimbursements/{user_id}/{uuid.uuid4().hex}{ext}"

        # 3. Salva no banco (O "Arquivo Órfão" é mitigado, pois se o upload falhar, 
        # o status continuará AWAITING e o financeiro pode cobrar o arquivo depois)
        new_reimb = Reimbursement(
            title=data.title,
            description=data.description,
            category=data.category,
            value=data.value,
            pix_key=data.pix_key,
            receipt=file_key, 
            status=StatusRefundEnum.AWAITING,
            user_id=user_id
        )
        db.add(new_reimb)
        await db.commit()
        await db.refresh(new_reimb)

        # 4. Carrega as credenciais
        bucket_name = os.environ.get("R2_BUCKET_NAME")
        account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        access_key = os.environ.get("R2_ACCESS_KEY_ID")
        secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")

        if not all([bucket_name, account_id, access_key, secret_key]):
            logger.error("Vazamento/Ausência de variáveis do Cloudflare R2.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha na configuração do servidor de arquivos.",
            )

        # 5. Gera a URL pré-assinada do tipo PUT
        s3_client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )

        try:
            upload_url = s3_client.generate_presigned_url(
                ClientMethod='put_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': file_key,
                    'ContentType': content_type # Trava o upload para aceitar apenas o tipo correto
                },
                ExpiresIn=3600
            )
        except ClientError as e:
            logger.error(f"Erro ao gerar URL PUT para reembolso: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao gerar link seguro de upload."
            )

        # 6. Monta o contrato de resposta
        presigned_response = PreSignedUrlResponse(
            file_extension=ext,
            upload_url=upload_url,
            file_key=file_key,
            expiration=3600,
            method="PUT"
        )

        return {"reimbursement": new_reimb, "presigned_url": presigned_response}