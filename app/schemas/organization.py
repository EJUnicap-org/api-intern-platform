from pydantic import BaseModel, Field, validator


class OrganizationContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(default="", max_length=20)
    cargo: str = Field(default="", max_length=50)


class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    cnpj: str = Field(..., min_length=14, max_length=18)
    status: str = Field(default="LEAD")
    contacts: list[OrganizationContactCreate] = Field(default=[])

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["LEAD", "CLIENTE", "ARQUIVADO"]
        if v.upper() not in valid_statuses:
            raise ValueError(f'status deve ser um de: {valid_statuses}')
        return v.upper()

    @validator('cnpj')
    def validate_cnpj(cls, v):
        cnpj_clean = v.replace('.', '').replace('/', '').replace('-', '')
        if not cnpj_clean.isdigit():
            raise ValueError('CNPJ deve conter apenas números')
        return cnpj_clean


class OrganizationContactResponse(BaseModel):
    id: int
    name: str
    phone: str
    cargo: str

    class Config:
        from_attributes = True


class OrganizationResponse(BaseModel):
    id: int
    name: str
    cnpj: str
    status: str
    contacts: list[OrganizationContactResponse] = []

    class Config:
        from_attributes = True


class StatusUpdate(BaseModel):
    """Recebe apenas o novo status para atualização de organização."""
    status: str = Field(..., description="Novo status: LEAD, CLIENTE ou ARQUIVADO")

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["LEAD", "CLIENTE", "ARQUIVADO"]
        if v.upper() not in valid_statuses:
            raise ValueError(f'status deve ser um de: {valid_statuses}')
        return v.upper()
    
class OrganizationUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    cnpj: str | None = Field(None, min_length=14, max_length=18)

    @validator('cnpj')
    def validate_cnpj(cls, v):
        if v is None:
            return v 
            
        cnpj_clean = v.replace('.', '').replace('/', '').replace('-', '')
        if not cnpj_clean.isdigit():
            raise ValueError('CNPJ deve conter apenas números')
        return cnpj_clean