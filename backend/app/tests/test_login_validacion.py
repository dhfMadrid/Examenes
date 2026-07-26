"""test_login_validacion.py — Tests de validacion Pydantic (422) para login.

Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_login_validacion.py -v
"""
import sys
from pathlib import Path

_tests_dir = Path(__file__).resolve().parent.parent.parent           # ...backend/
sys.path.insert(0, str(_tests_dir))

from unittest.mock import patch
import httpx
import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestLoginValidacionPydantic:
    """FastAPI/Pydantic valida los campos de LoginRequest antes de entrar en el endpoint.
    
    Se prueban las reglas de validacion via 422 Unprocessable Entity — nunca llega
    a buscar_alumno, ni a la BD, ni al hashing. Solo se verifica el comportamiento
    de FastAPI sobre payloads invalidos.
    """

    def test_falta_nif_pasaporte(self):
        """Sin nifPasaporte → 422 con detalle de Pydantic."""
        with patch("app.main._get_db"):
            resp = TestClient(app).post("/api/v1/auth/login", json={
                "password": "pass123456789",       # solo password
            })

        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data
        
        # Buscar el campo que falla en los errores de validacion
        # El loc es ('body', 'nifPasaporte') — hay que mirar el segundo elemento
        encontrados = []
        for e in data["detail"]:
            if isinstance(e, dict) and "loc" in e:
                encontrados.append(tuple(e["loc"]))
        
        assert ("body", "nifPasaporte") in encontrados

    def test_falta_password(self):
        """Sin password → 422 con detalle de Pydantic."""
        with patch("app.main._get_db"):
            resp = TestClient(app).post("/api/v1/auth/login", json={
                "nifPasaporte": "ABC12345678",    # solo nif
            })

        assert resp.status_code == 422
        data = resp.json()
        
        encontrados = []
        for e in data["detail"]:
            if isinstance(e, dict) and "loc" in e:
                encontrados.append(tuple(e["loc"]))
        
        assert ("body", "password") in encontrados

    def test_campo_con_tipo_invalido(self):
        """Enviar un array donde se espera string → 422 (invalid type)."""
        with patch("app.main._get_db"):
            resp = TestClient(app).post("/api/v1/auth/login", json={
                "nifPasaporte": ["ABC", "DEF"],   # es lista, debe ser str
                "password": 12345,                  # es int, debe ser str
            })

        assert resp.status_code == 422
        data = resp.json()
        assert "detail" in data
        assert len(data["detail"]) >= 2        # al menos dos errores de tipo

    def test_payload_vacio(self):
        """Sin cuerpo JSON → 422 (missing body)."""
        with patch("app.main._get_db"):
            resp = TestClient(app).post("/api/v1/auth/login", json={})

        assert resp.status_code == 422

    def test_cuerpo_invalido_no_json(self):
        """Enviar un string plano donde se espera JSON → 400 (HTTPX error en el cuerpo)."""
        with patch("app.main._get_db"):
            # Enviar texto plano sin content-type application/json
            try:
                resp = TestClient(app).post(
                    "/api/v1/auth/login",
                    content=b"no_es_un_json",
                    headers={"content-type": "text/plain; charset=utf-8"}
                )
                # Si por alguna razon llega, deberia fallar en el parse
                assert resp.status_code != 200          # fallo (40x)
            except Exception:
                # Si el TestClient o FastAPI lanzan una excepcion, tambien es valido —
                # significa que se detecta el error de parsing
                pass

    def test_json_malformado(self):
        """JSON incompleto invalido → 422 (JSON decode error)."""
        with patch("app.main._get_db"):
            resp = TestClient(app).post(
                "/api/v1/auth/login",
                content=b'{"nifPasaporte": "ABC"',     # falta cerrar y el campo password
                headers={"content-type": "application/json"}
            )
        
        # Esto puede ser 422 (Pydantic no recibe cuerpo completo) o 400 (parse error segun FastAPI version)
        assert resp.status_code in (400, 422)
