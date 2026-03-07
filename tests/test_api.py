import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/login", json={"email": "test@example.com", "password": "password"})
        assert response.status_code == 200
        assert "Login successful" in response.json()["message"]