# API Intern Platform

API para gerenciamento de leads e organizações, construída com FastAPI, SQLAlchemy e Redis. Este README foi reescrito para fornecer documentação prática e completa: instalação, configuração, execução, desenvolvimento, testes, deploy e exemplos de uso.

## Estrutura do repositório

Visão geral da árvore de diretórios:

```
api-intern-platform/
├── app/                    # Código principal da aplicação
│   ├── __init__.py
│   ├── main.py             # Ponto de entrada FastAPI (app.main:app)
│   ├── config.py           # Leitura de variáveis de ambiente / config
│   ├── database.py         # Sessões e engine SQLAlchemy
│   ├── models/             # Modelos SQLAlchemy (User, Lead, Organization, ...)
│   ├── schemas/            # Pydantic schemas (requests/responses)
│   ├── routes/             # Routers/Endpoints organizados por domínio
│   ├── services/           # Regras de negócio e interações com DB
│   ├── repositories/       # Acesso ao banco (opcional)
│   └── utils/              # Utilitários (auth, email, caching, helpers)
├── scripts/                # Scripts utilitários (ex: seed_user.py)
├── migrations/             # Migrations Alembic (se aplicável)
├── tests/                  # Testes unitários e de integração
├── docs/                   # Documentação adicional e exemplos
├── requirements.txt        # Dependências Python
├── Dockerfile              # Imagem da aplicação (opcional)
├── docker-compose.yml      # Compose para DB + Redis + app (opcional)
├── .env.example            # Variáveis de ambiente de exemplo
├── .gitignore
└── README.md
```

## Requisitos

- Python 3.10+
- PostgreSQL (ou outro RDBMS suportado)
- Redis (opcional, usado para cache/sessões)
- pip

Recomendado: Docker e docker-compose para ambientes reproduzíveis.

## Variáveis de ambiente

Crie um arquivo .env (ou exporte no ambiente) com as variáveis abaixo. Veja .env.example para referência.

- DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname
- REDIS_URL=redis://localhost:6379/0
- SECRET_KEY=uma_chave_secreta
- ALGORITHM=HS256
- ACCESS_TOKEN_EXPIRE_MINUTES=60
- ENV=development

Outras variáveis específicas podem estar em app/config.py.

## Instalação rápida (local)

1. Clone o repositório
2. Crie e ative um virtualenv:
   - python -m venv .venv
   - source .venv/bin/activate
3. Instale dependências:
   - pip install -r requirements.txt
4. Copie .env.example para .env e ajuste valores
5. Crie o banco e execute migrations (ver seção Migrations)

## Usando Docker (opcional)

1. Ajuste .env ou use variáveis no docker-compose.yml
2. docker-compose up --build

## Migrations

Se o projeto usa Alembic (padrão recomendado):

- Inicializar (se ainda não existir): alembic init migrations
- Gerar migration: alembic revision --autogenerate -m "mensagem"
- Aplicar migrations: alembic upgrade head

Se não houver Alembic, verifique scripts/ para rotinas de criação de esquema.

## Executando a aplicação

Desenvolvimento:

- uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Produção (exemplo com Uvicorn/Gunicorn):

- gunicorn -k uvicorn.workers.UvicornWorker app.main:app -w 4

## Scripts úteis

- scripts/seed_user.py --name "Admin" --email admin@example.com  # cria usuário inicial
- scripts/seed_data.py   # popular dados de exemplo (se existir)

## Testes

- Rode testes: pytest
- Para testes que envolvem DB/Redis, use fixtures que criem/derrubem bancos temporários ou use docker-compose para levantar dependências.

## Endpoints principais (resumo)

Autenticação
- POST /login  — Recebe credenciais (email/senha) e retorna access token JWT
- POST /logout — Invalida sessão / token (se suportado)

Leads
- POST /leads  — Criar lead (body: LeadCreate schema)
- GET /leads   — Listar leads (query params: page, size, filters)
- GET /leads/{id} — Recuperar lead por id
- PUT /leads/{id} — Atualizar lead
- DELETE /leads/{id} — Remover lead

Organizações
- POST /organizations — Criar organização
- GET /organizations  — Listar organizações

Usuários
- POST /users — Criar usuário
- GET /users  — Listar usuários (admin)

Observação: Endpoints exatos e schemas estão documentados automaticamente em tempo de execução no Swagger UI em /docs e no ReDoc em /redoc.

## Exemplos de uso (curl)

# Login
curl -X POST "http://localhost:8000/login" -H "Content-Type: application/json" -d '{"email":"admin@example.com","password":"secret"}'

# Criar lead (assumindo token JWT)
curl -X POST "http://localhost:8000/leads" -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d '{"name":"João","email":"joao@example.com","company":"ACME"}'

## Boas práticas de desenvolvimento

- Separe lógica em services/repositories para facilitar testes.
- Use Pydantic para validações e respostas consistentes.
- Trate erros com handlers globais (HTTPException) e logging apropriado.
- Proteja endpoints com dependências de segurança (OAuth2/JWT).
- Escreva testes unitários e de integração cobrindo as principais rotas.

## Deploy

- Configure variáveis de ambiente no servidor/CI
- Use gunicorn + uvicorn workers
- Utilize um sistema de migrations automatizado no deploy
- Configure proxys (Nginx) e TLS / HTTPS

## Observabilidade

- Ative logs estruturados (JSON) em produção
- Integrar Sentry ou similar para captura de erros
- Métricas: Prometheus + Grafana (expor /metrics)

## Contribuindo

- Abra issues para bugs/feature requests
- Faça branch a partir de main com prefixo feat/ ou fix/
- Envie PR com descrição clara e testes
- Siga o padrão de commit e CI do projeto

## Contato

Abra uma issue ou entre em contato com os mantenedores do repositório.

----

Se precisar, posso ajustar este README com detalhes específicos de config, exemplos de schemas, comandos exatos de migrations ou docker-compose já presentes no repositório.