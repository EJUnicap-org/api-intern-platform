from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional, Literal
from ..models.reimbursement import TypeRefundEnum, StatusRefundEnum


class ReimbursementCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1500)
    category: TypeRefundEnum = Field(..., description="Categoria do reembolso")
    value: Decimal = Field(..., gt=0, decimal_places=2)
    pix_key: str = Field(..., min_length=1, max_length=32)
    file_extension: str = Field(..., description="Extensão do arquivo (ex: .pdf, .png, .jpg)")


class ReimbursementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=1500)
    category: Optional[TypeRefundEnum] = Field(None)
    value: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    pix_key: Optional[str] = Field(None, min_length=1, max_length=32)
    receipt: Optional[str] = Field(None, max_length=255)
    status: Optional[StatusRefundEnum] = Field(None)


class ReimbursementResponse(BaseModel):
    id: int
    title: str
    description: str
    category: TypeRefundEnum
    value: Decimal
    pix_key: str
    receipt: Optional[str]
    status: StatusRefundEnum
    user_id: int
    date_time: datetime

    class Config:
        from_attributes = True


class PreSignedUrlResponse(BaseModel):
    file_extension: Literal[".pdf", ".png", ".jpg", ".jpeg"] = Field(...)
    upload_url: str = Field(..., description="URL pré-assinada para upload do arquivo")
    file_key: str = Field(..., description="Chave/caminho do arquivo no storage")
    expiration: int = Field(..., description="Tempo de expiração da URL em segundos")
    method: str = Field(default="PUT", description="Método HTTP para upload")


class ReimbursementCreateResponse(BaseModel):
    reimbursement: ReimbursementResponse
    presigned_url: PreSignedUrlResponse
