"""test_health.py — Health check endpoint.
    
Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_health.py -v
"""
import sys
from pathlib import Path

# backend/app/tests/ → añadir backend/ al path
_tests_dir = Path(__file__).resolve().parent               # ...backend/app/tests
sys.path.insert(0, str(_tests_dir.parent.parent))          # ...backend/

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="session")
def client():
    """Crea un cliente de pruebas sin levantar servidor."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests para GET /api/v1/auth/health."""

    def test_health_returns_ok(self, client):
        """El endpoint health debe devolver {status: 'ok'} con codigo 200."""
        response = client.get("/api/v1/auth/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_responde_json(self, client):
        """La respuesta debe ser siempre formato JSON correcto."""
        response = client.get("/api/v1/auth/health")
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "ok"
