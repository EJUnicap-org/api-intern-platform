# 📖 API Reference - EJ Unicap Platform

## 🔐 Autenticação (JWT Stateless)
A API utiliza o padrão OAuth2 com tokens JWT. O token deve ser enviado no cabeçalho HTTP de todas as rotas protegidas: `Authorization: Bearer <seu_token_aqui>`.

### 1. Login
* **POST** `/auth/login`
* **Segurança:** Rota Pública
* **Content-Type:** `application/x-www-form-urlencoded` (Padrão OAuth2)
* **Body (Form):**
    * `username` (string, required): E-mail do usuário.
    * `password` (string, required): Senha.
* **Response (200 OK):**
    ```json
    {
      "access_token": "eyJhbGciOi...",
      "token_type": "bearer"
    }
    ```
* **Erros:** `401 Unauthorized` (Credenciais inválidas).

### 2. Dados do Usuário Atual
* **GET** `/auth/me`
* **Segurança:** Requer Autenticação (Qualquer Role)
* **Response (200 OK):** Retorna o objeto do usuário logado (id, name, email, role, is_active).

---

## 🏢 Organizações e Leads (RBAC Ativo)

### 1. Criar Lead
* **POST** `/organizations/leads`
* **Segurança:** Apenas `ADMIN` ou `MANAGER` (Consultores recebem 403)
* **Body (JSON):**
    ```json
    {
      "name": "Empresa Teste",
      "cnpj": "12.345.678/0001-90",
      "status": "LEAD", 
      "contacts": []
    }
    ```
    *Nota: CNPJ aceita formatação ou apenas números. O Backend limpa automaticamente.*
* **Response (201 Created):** Retorna a Organização com ID gerado.

### 2. Listar Leads
* **GET** `/organizations/leads`
* **Segurança:** Apenas `ADMIN` ou `MANAGER`
* **Query Params:**
    * `limit` (int, default=10): Itens por página (1-100).
    * `offset` (int, default=0): Pular itens.
    * `cnpj_filter` (string, opcional): Busca parcial por CNPJ.
* **Response (200 OK):** Array de Organizações.

### 3. Atualizar Status do Lead
* **PATCH** `/organizations/leads/{lead_id}/status`
* **Segurança:** Apenas `ADMIN` ou `MANAGER`
* **Body (JSON):**
    ```json
    {
      "status": "CLIENTE" 
    }
    ```
    *Status válidos: "LEAD", "CLIENTE", "ARQUIVADO".*
* **Response (200 OK):** Organização atualizada.

---

## 🚀 Projetos

### 1. Criar Projeto
* **POST** `/projects/`
* **Segurança:** Apenas `ADMIN` ou `MANAGER`
* **Body (JSON):**
    ```json
    {
      "title": "Sistema de Gestão",
      "description": "Desenvolvimento de plataforma",
      "organization_id": 1,
      "deadline": "2026-12-31T23:59:59Z",
      "member_ids": [2, 5, 8]
    }
    ```
* **Response (201 Created):** Dados do projeto com os membros aninhados.
* **Erros:** `400 Bad Request` (Se IDs de membros ou organização não existirem).

### 2. Listar Projetos
* **GET** `/projects/`
* **Segurança:** Requer Autenticação
* **Comportamento de Negócio:**
    * `ADMIN`/`MANAGER`: Recebem a lista de TODOS os projetos da base.
    * `CONSULTANT`: Recebem APENAS os projetos onde seu ID consta na lista de membros (Prevenção de IDOR).
* **Response (200 OK):** Array de Projetos.

### 3. Detalhes do Projeto
* **GET** `/projects/{project_id}`
* **Segurança:** Requer Autenticação
* **Erros:** * `404 Not Found` (Projeto inexistente).
*`403 Forbidden` (Se um Consultor tentar acessar um projeto do qual não faz parte).

## 📊 Diagnóstico (Motor PERT/CCPM)

### 1. Calcular Diagnóstico Híbrido
* **PATCH** `/projects/{project_id}/diagnostic`
* **Segurança:** Requer Autenticação (`ADMIN` ou `MANAGER`).
* **Body (JSON):**
    ```json
    {
      "tasks": {
        "A": { "desc": "Levantamento de Requisitos", "pred": [], "O": 2, "M": 4, "P": 6 },
        "B": { "desc": "Design da Interface (Paralelo)", "pred": ["A"], "O": 1, "M": 2, "P": 3 },
        "C": { "desc": "Arquitetura do BD (Gargalo)", "pred": ["A"], "O": 4, "M": 6, "P": 14 },
        "D": { "desc": "Integracao e Testes Finais", "pred": ["B", "C"], "O": 2, "M": 3, "P": 4 }
      }
    }
    ```
* **Response (200 OK):** Retorna o dicionário completo com as raízes `pert_classico` e `corrente_critica`.
* **Erros:**
    * `400 Bad Request`: Se o dicionário de tarefas estiver vazio.
    * `404 Not Found`: Projeto não encontrado.
    * `422 Unprocessable Entity`: Erro de topologia (ex: dependência circular ou nó solto).

### 2. Visualizar Diagnóstico Salvo
* **GET** `/projects/{project_id}/diagnostic`
* **Segurança:** Requer Autenticação (`ADMIN` ou `MANAGER`).
* **Response (200 OK):** Retorna o JSON do cálculo salvo no banco.
* **Erros:** * `404 Not Found`: Projeto inexistente OU o cálculo ainda não foi rodado (necessário rodar o PATCH primeiro).

### 3. Baixar Relatório (PDF)
* **GET** `/projects/{project_id}/diagnostic/pdf`
* **Segurança:** Requer Autenticação (`ADMIN` ou `MANAGER`).
* **Response (200 OK):** Arquivo binário (`application/pdf`). O front-end deve forçar o download.
* **Erros:** * `404 Not Found`: Diagnóstico não foi gerado para este projeto ainda.

---

## 📂 Arquivos (Cloudflare R2)

### 1. Solicitar URL de Upload
* **POST** `/files/upload-url`
* **Segurança:** Requer Autenticação.
* **Comportamento UI:** A API retorna uma URL pré-assinada. O Front-end deve fazer um `PUT` binário para essa URL logo em seguida.
* **Erros:** * `500 Internal Server Error`: Falha de comunicação do backend com a Cloudflare. O Front-end deve exibir mensagem de indisponibilidade temporária do serviço de arquivos.