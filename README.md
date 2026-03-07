# API Intern Platform

Uma plataforma de API para gerenciamento de leads e organizações, construída com FastAPI, SQLAlchemy e Redis.

## Estrutura do Projeto

```
api-intern-platform/
├── app/                    # Código principal da aplicação
│   ├── __init__.py
│   ├── main.py            # Ponto de entrada FastAPI
│   ├── config.py          # Configurações (DB, Redis, etc.)
│   ├── database.py        # Conexão com banco de dados
│   ├── models/            # Modelos SQLAlchemy
│   │   ├── user.py
│   │   └── organization.py
│   ├── routes/            # Rotas FastAPI
│   │   ├── auth.py
│   │   └── leads.py
│   ├── services/          # Lógica de negócio
│   │   ├── auth_service.py
│   │   └── lead_service.py
│   └── utils/             # Utilitários
│       ├── redis_client.py
│       └── security.py
├── scripts/               # Scripts utilitários
│   ├── seed_user.py       # Script para criar usuário inicial
│   └── __init__.py
├── tests/                 # Testes
│   ├── test_api.py
│   ├── conftest.py
│   └── __init__.py
├── docs/                  # Documentação
├── requirements.txt       # Dependências Python
├── .gitignore
└── README.md
```

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual: `python -m venv .venv`
3. Ative o ambiente: `source .venv/bin/activate`
4. Instale as dependências: `pip install -r requirements.txt`

## Configuração

Certifique-se de ter PostgreSQL e Redis rodando. Configure as variáveis em `app/config.py` se necessário.

## Executando

### Criar usuário inicial
```bash
python scripts/seed_user.py --name "Admin" --email admin@example.com
```

### Rodar a aplicação
```bash
uvicorn main:app --reload
```

### Rodar testes
```bash
pytest
```

## API Endpoints

- `POST /login` - Autenticação
- `POST /logout` - Logout
- `POST /leads` - Criar lead
- `GET /leads` - Listar leads

## Desenvolvimento

A aplicação segue uma arquitetura modular com separação clara entre:
- **Models**: Definições de banco de dados
- **Routes**: Endpoints da API
- **Services**: Lógica de negócio
- **Utils**: Funções auxiliares

Para adicionar novas funcionalidades, siga este padrão.