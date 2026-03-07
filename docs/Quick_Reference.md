# 🚀 Quick Reference: Pydantic Schemas para JSON Aninhado

## TL;DR - O que você criou

Você tem 3 camadas de modelos:

```python
# 1. ENTRADA (o que o frontend envia)
class OrganizationContactCreate(BaseModel):
    name: str
    phone: str = ""
    cargo: str = ""

class OrganizationCreate(BaseModel):
    name: str
    cnpj: str
    status: str = "LEAD"
    contacts: list[OrganizationContactCreate] = []

# 2. BANCO (ORM - como é salvo)
class Organization(Base):
    __tablename__ = "organization"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    cnpj: Mapped[str]
    status: Mapped[statusEnum]
    contacts: Mapped[list["OrganizationContact"]] = relationship(...)

class OrganizationContact(Base):
    __tablename__ = "organization_contact"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    phone: Mapped[str]
    cargo: Mapped[str]
    organization_id: Mapped[int] = mapped_column(ForeignKey("organization.id"))

# 3. SAÍDA (o que o frontend recebe)
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
```

---

## JSON Esperado pelo Frontend

```json
POST /leads
Content-Type: application/json

{
  "name": "Empresa XYZ LTDA",
  "cnpj": "12.345.678/0001-90",
  "status": "LEAD",
  "contacts": [
    {
      "name": "João Silva",
      "phone": "(11) 98888-8888",
      "cargo": "CEO"
    }
  ]
}
```

---

## Resposta do Backend (201 Created)

```json
{
  "id": 1,
  "name": "Empresa XYZ LTDA",
  "cnpj": "12345678000190",
  "status": "LEAD",
  "contacts": [
    {
      "id": 1,
      "name": "João Silva",
      "phone": "(11) 98888-8888",
      "cargo": "CEO"
    }
  ]
}
```

---

## Validações Automáticas

| Problema | Erro | HTTP |
|----------|------|------|
| Campo `name` faltando | `Field required` | 422 |
| Campo `cnpj` faltando | `Field required` | 422 |
| `name` vazio | `at least 1 character` | 422 |
| `cnpj` com letras | `CNPJ deve conter apenas números` | 422 |
| `status` = "INVALID" | `status deve ser um de: [...]` | 422 |
| Contato `name` vazio | `at least 1 character` | 422 |
| Qualquer erro no DB | `Erro ao criar o lead` | 500 |

---

## Como Pydantic Valida JSON Aninhado

```python
# Quando você recebe isso:
{
  "name": "...",
  "cnpj": "...",
  "contacts": [ ... ]
}

# Pydantic faz isso:
1. Cria OrganizationCreate com os dados
2. Para cada item em "contacts", cria OrganizationContactCreate
3. Valida CADA campo em CADA objeto
4. Se tudo OK, retorna objeto Python estruturado
5. Se algo falhar, retorna detalhes exatos dos erros
```

---

## Validators Customizados (o que você tem)

### Para CNPJ:
```python
@validator('cnpj')
def validate_cnpj(cls, v):
    cnpj_clean = v.replace('.', '').replace('/', '').replace('-', '')
    if not cnpj_clean.isdigit():
        raise ValueError('CNPJ deve conter apenas números')
    return cnpj_clean
```

**Aceita:** `"12.345.678/0001-90"` → Retorna: `"12345678000190"`

### Para Status:
```python
@validator('status')
def validate_status(cls, v):
    valid_statuses = ["LEAD", "CLIENT", "ARQUIVED"]
    if v not in valid_statuses:
        raise ValueError(f'status deve ser um de: {valid_statuses}')
    return v
```

**Aceita:** `"LEAD"`, `"CLIENT"`, `"ARQUIVED"`  
**Rejeita:** qualquer outra string

---

## Config Class - O que significa `from_attributes = True`?

```python
class Config:
    from_attributes = True
```

Permite Pydantic ler dados de objetos ORM, não só dicts:

```python
# SEM from_attributes = True:
organization = db.query(Organization).first()
response = OrganizationResponse(organization)  # ❌ Erro!

# COM from_attributes = True:
organization = db.query(Organization).first()
response = OrganizationResponse.from_orm(organization)  # ✅ OK!
# ou automaticamente na rota com response_model=OrganizationResponse
```

---

## A Rota POST (Implementação)

```python
@app.post("/leads", response_model=OrganizationResponse, status_code=201)
async def create_lead(
    org_data: OrganizationCreate,  # ← Pydantic valida aqui
    db: AsyncSession = Depends(get_db_session)
):
    """
    org_data já está validado. Você SABE que:
    - org_data.name é string, 1-100 chars
    - org_data.cnpj é string limpa, só números
    - org_data.status é "LEAD", "CLIENT" ou "ARQUIVED"
    - org_data.contacts é lista de contatos válidos
    """
    
    # Criar ORM models
    new_org = Organization(
        name=org_data.name,
        cnpj=org_data.cnpj,
        status=statusEnum[org_data.status]
    )
    
    for contact_data in org_data.contacts:
        new_contact = OrganizationContact(
            name=contact_data.name,
            phone=contact_data.phone,
            cargo=contact_data.cargo,
            organization=new_org
        )
        new_org.contacts.append(new_contact)
    
    # Salvar
    db.add(new_org)
    await db.commit()
    await db.refresh(new_org)  # Recarrega do DB
    
    # FastAPI converte automaticamente:
    # Organization (ORM) → OrganizationResponse (Pydantic) → JSON
    return new_org
```

---

## Testando no Swagger

1. Acesse: `http://localhost:8000/docs`
2. Procure por `POST /leads`
3. Clique em "Try it out"
4. Cole este JSON:

```json
{
  "name": "Empresa Teste",
  "cnpj": "12.345.678/0001-90",
  "status": "LEAD",
  "contacts": [
    {
      "name": "João",
      "phone": "(11) 99999-9999",
      "cargo": "CEO"
    }
  ]
}
```

5. Clique "Execute"
6. Veja a resposta 201 com os dados salvos

---

## Por que 3 schemas diferentes?

| Schema | Quando Usar | Por quê |
|--------|-----------|--------|
| `OrganizationCreate` | Receber dados do frontend | Valida entrada, sem IDs |
| `Organization` | Salvar no DB com SQLAlchemy | Mapeia a tabela do DB |
| `OrganizationResponse` | Enviar dados ao frontend | Inclui IDs, serializa ORM |

**Separação = Segurança + Flexibilidade**

```python
# Você RECEBE
{
  "name": "...",
  "cnpj": "...",
  "contacts": [...]
  # Sem "id" (o DB cria)
}

# Você SALVA com ORM
Organization(
  name="...",
  cnpj="...",
  # id é auto-incrementado
)

# Você RESPONDE
{
  "id": 1,
  "name": "...",
  "cnpj": "...",
  "contacts": [...]
  # Incluindo "id" que veio do DB
}
```

---

## Erros Comuns

### ❌ `AttributeError: type object 'Organization' has no attribute 'from_orm'`

**Motivo:** Você tentou usar uma classe ORM como Pydantic.

**Solução:** Use `response_model=OrganizationResponse` na rota para conversão automática.

### ❌ Pydantic não valida contatos aninhadosDe

**Motivo:** Você não definiu `contacts: list[OrganizationContactCreate]`

**Solução:** Use type hints corretos com lista tipada.

### ❌ `ValueError: could not interpret object as an integer` ao salvar

**Motivo:** Status string não foi convertido para enum.

**Solução:** Use `status=statusEnum[org_data.status]` na rota.

### ❌ Contatos não aparecem na resposta

**Motivo:** `cascade="all, delete-orphan"` no relacionamento, mas contatos não foram setados.

**Solução:** Use `new_org.contacts.append(new_contact)` antes de salvar.

---

## ⚡ Resumão: JSON Aninhado em 3 Passos

```
1. Frontend envia
   POST /leads
   { "name": "...", "cnpj": "...", "contacts": [...] }

2. Pydantic valida automatically
   ✓ Estrutura correta
   ✓ Tipos corretos
   ✓ Valores permitidos
   ✓ Comprimentos OK
   → Retorna OrganizationCreate validado

3. Rota cria ORM, salva, retorna Response
   new_org = Organization(...)
   db.add(), db.commit(), db.refresh()
   return new_org  ← Convertido para OrganizationResponse automaticamente
```

---

## 📚 Files Criados/Modificados

- **main2.py** - Adicionado schemas Pydantic + rota POST /leads
- **SCHEMAS_EXAMPLE.md** - Documentação detalhada com exemplos
- **test_schemas_examples.py** - Exemplos práticos de teste
- **Quick_Reference.md** - Este arquivo

Pronto para usar! 🚀

