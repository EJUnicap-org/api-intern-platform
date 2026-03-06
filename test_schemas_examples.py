"""
Exemplos práticos: Como testar a rota POST /leads com JSON aninhado
"""

import httpx
import asyncio
import json

# ============================================================================
# 1. EXEMPLO: Criar Lead COM contatos
# ============================================================================

lead_data = {
    "name": "Tech Solutions LTDA",
    "cnpj": "12.345.678/0001-90",  # Com formatação (validator limpa)
    "status": "LEAD",
    "contacts": [
        {
            "name": "Maria Santos",
            "phone": "(11) 98888-8888",
            "cargo": "Diretora Comercial"
        },
        {
            "name": "Carlos Oliveira",
            "phone": "(11) 97777-7777",  
            "cargo": "Técnico"
        }
    ]
}

# ============================================================================
# 2. EXEMPLO: Criar Lead SEM contatos (mais simples)
# ============================================================================

simple_lead = {
    "name": "Empresa ABC",
    "cnpj": "98765432000123"  # Sem formatação (também aceita)
    # status e contacts são opcionais
}

# ============================================================================
# 3. EXEMPLO: Teste com httpx (sync ou async)
# ============================================================================

def test_create_lead_sync():
    """Teste síncrono da rota"""
    client = httpx.Client(base_url="http://localhost:8000")
    
    response = client.post("/leads", json=lead_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    client.close()


async def test_create_lead_async():
    """Teste assíncrono da rota"""
    client = httpx.AsyncClient(base_url="http://localhost:8000")
    
    response = await client.post("/leads", json=lead_data)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    await client.aclose()


# ============================================================================
# 4. EXEMPLO: Tratamento de Erros de Validação
# ============================================================================

# JSON INVÁLIDO - campo obrigatório faltando
invalid_lead_missing_key = {
    "cnpj": "12.345.678/0001-90",
    "status": "LEAD"
    # Falta "name" (obrigatório!)
}

# JSON INVÁLIDO - status não reconhecido
invalid_lead_bad_status = {
    "name": "Empresa XYZ",
    "cnpj": "12.345.678/0001-90",
    "status": "INVALID_STATUS"  # ← Não é LEAD, CLIENT ou ARQUIVED
}

# JSON INVÁLIDO - CNPJ com caracteres inválidos
invalid_lead_bad_cnpj = {
    "name": "Empresa XYZ",
    "cnpj": "ABC-XYZ-INVALID",  # ← Caracteres não numéricos
}

# JSON INVÁLIDO - contato com nome vazio
invalid_lead_empty_contact_name = {
    "name": "Empresa XYZ",
    "cnpj": "12.345.678/0001-90",
    "contacts": [
        {
            "name": "",  # ← Inválido: min_length=1
            "phone": "11999999999",
            "cargo": "CEO"
        }
    ]
}


def test_validation_errors():
    """Testa erros de validação do Pydantic"""
    client = httpx.Client(base_url="http://localhost:8000")
    
    test_cases = [
        ("Missing required field (name)", invalid_lead_missing_key),
        ("Invalid status", invalid_lead_bad_status),
        ("Invalid CNPJ", invalid_lead_bad_cnpj),
        ("Empty contact name", invalid_lead_empty_contact_name),
    ]
    
    for test_name, invalid_data in test_cases:
        response = client.post("/leads", json=invalid_data)
        print(f"\n{'='*60}")
        print(f"TEST: {test_name}")
        print(f"Status Code: {response.status_code}")
        print(f"Error Details:")
        error_response = response.json()
        print(json.dumps(error_response, indent=2, ensure_ascii=False))
    
    client.close()


# ============================================================================
# 5. EXEMPLO: Resposta com sucesso (201 Created)
# ============================================================================

success_response_example = {
    "id": 1,
    "name": "Tech Solutions LTDA",
    "cnpj": "12345678000190",  # CNPJ foi limpo pelo validator
    "status": "LEAD",
    "contacts": [
        {
            "id": 1,
            "name": "Maria Santos",
            "phone": "(11) 98888-8888",
            "cargo": "Diretora Comercial"
        },
        {
            "id": 2,
            "name": "Carlos Oliveira",
            "phone": "(11) 97777-7777",
            "cargo": "Técnico"
        }
    ]
}

# ============================================================================
# 6. EXEMPLO: Resposta com erro de validação (422 Unprocessable Entity)
# ============================================================================

validation_error_response_example = {
    "detail": [
        {
            "type": "missing",
            "loc": ["body", "name"],
            "msg": "Field required",
            "input": {
                "cnpj": "12.345.678/0001-90",
                "status": "LEAD"
            }
        }
    ]
}

# ============================================================================
# 7. EXEMPLO: Como o FastAPI converte ORM → Resposta
# ============================================================================

"""
A rota faz assim:

    organization = Organization(
        name="Tech Solutions LTDA",
        cnpj="12345678000190",
        status=statusEnum.Lead,
        contacts=[...]
    )
    db.add(organization)
    db.commit()
    db.refresh(organization)
    
    # Aqui FastAPI usa @app.post(..., response_model=OrganizationResponse)
    return organization  # ← Objeto ORM
    
    # Pydantic converte:
    # organization (ORM) + from_attributes=True
    #     → OrganizationResponse (Pydantic)
    #         → JSON serializado
    #             → Enviado ao cliente com status 201
"""

# ============================================================================
# 8. EXEMPLO: Fluindo dados por camadas
# ============================================================================

"""
FRONTEND                          PYTHON CODE                         DATABASE

JSON String    ────────────────→  Request Body
  "{"
  "  "name": "Tech",
  "  "cnpj": "12.345.678/0001-90",
  "  "contacts": [
  "    {"name": "João"}
  "  ]
  "}"

                ───Pydantic──→  OrganizationCreate (validated dict)
                                 {
                                   "name": "Tech",
                                   "cnpj": "12345678000190",  ← limpo!
                                   "status": "LEAD",           ← default
                                   "contacts": [
                                     {"name": "João", ...}
                                   ]
                                 }

                ───FastAPI──→   Organization (ORM Model)
                               │
                               ├─ id: 1
                               ├─ name: "Tech"
                               ├─ cnpj: "12345678000190"
                               ├─ status: StatusEnum.Lead
                               └─ contacts: [
                                    OrganizationContact(
                                      id: 1,
                                      name: "João",
                                      organization_id: 1
                                    )
                                  ]

                ───SQLAlchemy──→ INSERT INTO organization ...
                                 INSERT INTO organization_contact ...
                                                               ✓ SAVED

                ←─SQLAlchemy────  Organization (ORM, reloaded)

                ←─Pydantic────   OrganizationResponse
                                {
                                  "id": 1,
                                  "name": "Tech",
                                  "status": "LEAD",
                                  "contacts": [
                                    {
                                      "id": 1,
                                      "name": "João",
                                      ...
                                    }
                                  ]
                                }

JSON String    ←──────────────   {"id": 1, "name": "Tech", ...}

FRONTEND RECEBE                   Status: 201 Created
"""

# ============================================================================
# 9. EXEMPLO: Comparison de Schemas
# ============================================================================

"""
Para RECEBER dados (criar/atualizar):
├─ OrganizationCreate (Pydantic)
│  ├─ name: str               ← sem ID, IDs são gerados no DB
│  ├─ cnpj: str               ← valores que o usuário envia
│  ├─ status: str
│  └─ contacts: list[OrganizationContactCreate]
│

Para ENVIAR dados (responder):
├─ OrganizationResponse (Pydantic)
│  ├─ id: int                 ← ID retornado do DB
│  ├─ name: str               ← dados salvos confirmados
│  ├─ cnpj: str
│  ├─ status: str
│  └─ contacts: list[OrganizationContactResponse]
│     ├─ id: int              ← IDs dos contatos
│     ├─ name: str
│     └─ ...

Models.Organization (SQLAlchemy ORM):
├─ __tablename__ = "organization"
├─ id: mapped_column(primary_key=True)
├─ name: mapped_column(String(100))
├─ cnpj: mapped_column(String(18))
├─ status: mapped_column(Enum)
└─ contacts: relationship(...)  ← conecta com OrganizationContact
"""


if __name__ == "__main__":
    # Descomente para testar:
    
    # test_create_lead_sync()
    # asyncio.run(test_create_lead_async())
    # test_validation_errors()
    
    print("Exemplos carregados. Descomente as funções para testar.")
