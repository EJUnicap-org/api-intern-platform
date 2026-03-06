# Schemas Pydantic - JSON Aninhado para FastAPI

## 📐 Arquitetura dos Schemas

```
Frontend (JSON)
      ↓
OrganizationCreate (Pydantic)
├── name: str
├── cnpj: str ✓ Validação customizada
├── status: str ✓ Validação customizada
└── contacts: list[OrganizationContactCreate]
    ├── name: str
    ├── phone: str
    └── cargo: str
      ↓
FastAPI Route (/leads POST)
      ↓
Organization (ORM Model)
├── id (PK)
├── name
├── cnpj
├── status
└── contacts (FK relationship)
    ├── id (PK)
    ├── name
    ├── phone
    ├── cargo
    └── organization_id (FK)
      ↓
DATABASE
```

---

## 📋 Exemplo 1: JSON Mínimo (sem contatos)

```json
{
  "name": "Empresa XYZ LTDA",
  "cnpj": "12345678000190"
}
```

**Resposta 201 Created:**
```json
{
  "id": 1,
  "name": "Empresa XYZ LTDA",
  "cnpj": "12345678000190",
  "status": "LEAD",
  "contacts": []
}
```

---

## 📋 Exemplo 2: JSON Completo (com contatos aninhados)

```json
{
  "name": "Tech Solutions LTDA",
  "cnpj": "12.345.678/0001-90",
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
```

**Resposta 201 Created:**
```json
{
  "id": 2,
  "name": "Tech Solutions LTDA",
  "cnpj": "12345678000190",
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
```

---

## ❌ Exemplo 3: Validação - Campo Obrigatório Faltando

**Request INVÁLIDO:**
```json
{
  "cnpj": "12.345.678/0001-90",
  "status": "LEAD"
}
```

**Resposta 422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": {...}
    }
  ]
}
```

---

## ❌ Exemplo 4: Validação - Status Inválido

**Request INVÁLIDO:**
```json
{
  "name": "Empresa ABC",
  "cnpj": "12.345.678/0001-90",
  "status": "INVALID_STATUS"
}
```

**Resposta 422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "status"],
      "msg": "Value error, status deve ser um de: ['LEAD', 'CLIENT', 'ARQUIVED']"
    }
  ]
}
```

---

## ❌ Exemplo 5: Validação - CNPJ Inválido

**Request INVÁLIDO:**
```json
{
  "name": "Empresa ABC",
  "cnpj": "ABC-INVALID-CNPJ",
  "status": "LEAD"
}
```

**Resposta 422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "cnpj"],
      "msg": "Value error, CNPJ deve conter apenas números (e opcionalmente . / -)"
    }
  ]
}
```

---

## 🔐 Validações Implementadas

| Campo | Tipo | Validações | Comportamento |
|-------|------|-----------|---|
| `name` | string | `required`, `min_length=1`, `max_length=100` | Obrigatório, 1-100 caracteres |
| `cnpj` | string | `required`, `min_length=14`, `max_length=18`, custom validator | Obrigatório, remove formatação, valida números |
| `status` | string | `default="LEAD"`, custom validator | Padrão é "LEAD", apenas ["LEAD", "CLIENT", "ARQUIVED"] |
| `contacts[].name` | string | `required`, `min_length=1`, `max_length=100` | Obrigatório, 1-100 caracteres |
| `contacts[].phone` | string | `default=""`, `max_length=20` | Opcional, máximo 20 caracteres |
| `contacts[].cargo` | string | `default=""`, `max_length=50` | Opcional, máximo 50 caracteres |

---

## 🛠️ Como os Validators Funcionam

### Validator customizado para `cnpj`:
```python
@validator('cnpj')
def validate_cnpj(cls, v):
    """Remove formatação comum de CNPJ e valida"""
    # Remove pontos, barras e hífens
    cnpj_clean = v.replace('.', '').replace('/', '').replace('-', '')
    if not cnpj_clean.isdigit():
        raise ValueError('CNPJ deve conter apenas números (e opcionalmente . / -)')
    return cnpj_clean
```

**O que faz:**
- Aceita: `"12.345.678/0001-90"` ou `"12345678000190"`
- Remove formatação automaticamente
- Valida que só tem números
- Rejeta: `"ABC-INVALID-CNPJ"`

### Validator customizado para `status`:
```python
@validator('status')
def validate_status(cls, v):
    """Valida que o status é um valor enum válido"""
    valid_statuses = ["LEAD", "CLIENT", "ARQUIVED"]
    if v not in valid_statuses:
        raise ValueError(f'status deve ser um de: {valid_statuses}')
    return v
```

---

## 📚 Schemas Response (Respostas)

Para enviar dados **PARA** o frontend, usamos tipos diferentes:

### `OrganizationContactResponse`
```python
class OrganizationContactResponse(BaseModel):
    id: int
    name: str
    phone: str
    cargo: str
    
    class Config:
        from_attributes = True  # ← SQLAlchemy ↔ Pydantic
```

### `OrganizationResponse`
```python
class OrganizationResponse(BaseModel):
    id: int
    name: str
    cnpj: str
    status: str
    contacts: list[OrganizationContactResponse] = []
    
    class Config:
        from_attributes = True  # ← SQLAlchemy ↔ Pydantic
```

**Por que `from_attributes = True`?**
Permite ao Pydantic ler dados de atributos de objetos ORM (como `organization.name`), não apenas dicts.

---

## 🚀 Fluxo Completo: Frontend → Backend → DB

```
1. FRONTEND ENVIA JSON
   POST /leads
   Content-Type: application/json
   {
     "name": "Tech Company",
     "cnpj": "12.345.678/0001-90",
     "contacts": [...]
   }

2. FASTAPI RECEBE E VALIDA COM PYDANTIC
   org_data: OrganizationCreate
   ✓ Valida nome (required, 1-100 chars)
   ✓ Valida CNPJ (remove formatação, valida números)
   ✓ Valida status (default "LEAD", apenas válidos)
   ✓ Valida cada contato recursivamente
   
   Se alguma validação falhar → 422 Unprocessable Entity

3. ROTA PROCESSA OS DADOS VALIDADOS
   # Dados já garantidos como corretos
   new_org = Organization(
       name=org_data.name,          # ← string já validada
       cnpj=org_data.cnpj,          # ← string já limpa
       status=statusEnum[org_data.status]  # ← valor enum válido
   )
   
   for contact_data in org_data.contacts:  # ← lista já validada
       new_contact = OrganizationContact(...)

4. SALVA NO BANCO
   db.add(new_org)
   await db.commit()

5. RETORNA DADOS AO FRONTEND
   response_model=OrganizationResponse
   {
     "id": 1,
     "name": "Tech Company",
     "cnpj": "12345678000190",
     "status": "LEAD",
     "contacts": [
       {
         "id": 101,
         "name": "João",
         ...
       }
     ]
   }
```

---

## 💡 Benefícios dessa Arquitetura

| Benefício | Descrição |
|-----------|-----------|
| **Type Safety** | Sistema de tipos forte com mypy/pylint |
| **Validação Automática** | Rejeita dados inválidos antes de chegar no banco |
| **Documentação Auto** | Swagger/OpenAPI gerado automaticamente |
| **Conversão** | JSON ↔ Python objects ↔ ORM models |
| **Serialização** | ORM models → JSON automaticamente |
| **Segurança** | Previne SQL injection, type confusion, etc |
| **DX** | Autocompletar no IDE, type hints |

---

## 🔍 Visualizando no Swagger

Acesse: `http://localhost:8000/docs`

A rota POST `/leads` vai mostrar:
- Exemplo completo do JSON esperado
- Todos os campos, tipos e validações
- "Try it out" para testar
- Respostas esperadas (201, 422, 500)

