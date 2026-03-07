import pytest
import httpx
from main import app # Importa a sua própria API

@pytest.mark.asyncio
async def test_fluxo_completo_leads():
    # Inicia um cliente virtual que ataca a sua API diretamente na memória
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        
        # 1. ATAQUE DE AUTENTICAÇÃO
        login_payload = {"email": "diretor@ejunicap.com", "password": "senha_segura"}
        login_response = await client.post("/login", json=login_payload)
        
        # O que você deve verificar aqui para garantir que o login funcionou?
        assert login_response.status_code == 200
        
        # 2. ATAQUE DE NEGÓCIOS (O cliente virtual já está com o cookie injetado!)
        lead_payload = {
            "name": "Nova Empresa de Teste",
            "cnpj": "12.345.678/0001-90",
            "status": "LEAD",
            "contacts": [{"name": "Invasor", "phone": "000", "cargo": "Hacker"}]
        }
        
        lead_response = await client.post("/leads", json=lead_payload)
        
        # Se a nossa engenharia de RBAC falhou, ele vai retornar 201. 
        # Se funcionou e o usuário mockado não tiver permissão, qual código HTTP deve voltar?
        assert lead_response.status_code == 201 # Ou seria 403?