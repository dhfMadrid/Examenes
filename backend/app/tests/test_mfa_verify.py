"""test_mfa_verify.py — Tests para POST /api/v1/auth/mfa-verify.

Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_mfa_verify.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

_tests_dir = Path(__file__).resolve().parent.parent.parent           # ...backend/
sys.path.insert(0, str(_tests_dir))

import hashlib
import pytest
from fastapi.testclient import TestClient
from app.main import app, _sessions


# ---------------------------------------------------------------------------
# Helper que garantiza password_hash consistente con SHA-256(password)
# ---------------------------------------------------------------------------

def _make_valid_user(password: str = "pass1234", correo=None):
    """Mock user cuyo hash COINCIDE con SHA-256(password)."""
    return {
        "id": 1,
        "nombre": "Juan Perez",
        "password_hash": hashlib.sha256(password.encode()).digest(),
        "activo": True,
        "correo_electronico": correo,
    }


@pytest.fixture
def clean_client():
    """TestClient con sesiones MFA limpias y usuario mockeado."""
    _sessions.clear()

    mu = _make_valid_user("pass1234", correo=None)

    with patch("app.main.buscar_alumno", return_value=mu):
        with patch("app.main._get_db"):
            client = TestClient(app)
            yield client, mu


# ---------------------------------------------------------------------------
# Tests MFA exitosos
# ---------------------------------------------------------------------------

class TestMFAVerifyExitoso:

    def test_mfa_con_codigo_correcto(self, clean_client):
        """OTP correcto → login completado con jwtToken."""
        client, mock_user = clean_client

        # Paso 1: login genera OTP y lo deja en la sesion
        login_resp = client.post("/api/v1/auth/login", json={
            "nifPasaporte": "ABC12345678",
            "password": "pass1234",
        })

        assert login_resp.status_code == 200
        login_data = login_resp.json()
        temp_token = login_data.get("tokenTemporal")

        # Leer el OTP de la sesion interna (simulamos que lo conocemos)
        mfa_key = "mfa_ABC12345678"
        stored_otp = _sessions[mfa_key]["otp"]         # 6 digitos

        # Paso 2: verificar MFA con el OTP real
        mfa_resp = client.post("/api/v1/auth/mfa-verify", json={
            "nifPasaporte": "ABC12345678",
            "codigoMFA": stored_otp,                     # codigo correcto
        })

        assert mfa_resp.status_code == 200
        data = mfa_resp.json()
        assert data["exitoso"] is True
        assert data["requiereMFA"] is False
        assert data["jwtToken"] is not None
        assert "Autenticacion completada" in data.get("mensaje", "")

    def test_mfa_no_permite_reutilizacion(self, clean_client):
        """Un OTP ya usado se elimina de la sesion — no se puede usar dos veces."""
        client, mock_user = clean_client

        # Login genera OTP
        login_resp = client.post("/api/v1/auth/login", json={
            "nifPasaporte": "USER123456789",
            "password": "pass1234",
        })

        assert login_resp.status_code == 200
        mfa_key = "mfa_USER123456789"
        stored_otp = _sessions[mfa_key]["otp"]

        # Primer uso → exitoso
        mfa_resp1 = client.post("/api/v1/auth/mfa-verify", json={
            "nifPasaporte": "USER123456789",
            "codigoMFA": stored_otp,
        })
        assert mfa_resp1.status_code == 200

        # Segundo uso del mismo OTP → fallo (se eliminó la sesion)
        assert mfa_key not in _sessions                # validacion


# ---------------------------------------------------------------------------
# Tests MFA fallidos
# ---------------------------------------------------------------------------

class TestMFAVerifyFallido:

    def test_mfa_codigo_incorrecto(self, clean_client):
        """OTP errado → 401."""
        client, mock_user = clean_client

        client.post("/api/v1/auth/login", json={
            "nifPasaporte": "ABC12345678",
            "password": "pass1234",
        })

        mfa_resp = client.post("/api/v1/auth/mfa-verify", json={
            "nifPasaporte": "ABC12345678",
            "codigoMFA": "000000",                         # codigo incorrecto
        })

        assert mfa_resp.status_code == 401

    def test_mfa_sesion_no_existe(self, clean_client):
        """Sesion MFA eliminada/expirada → 401."""
        client, mock_user = clean_client       # (sin hacer login, no hay sesion)

        mfa_resp = client.post("/api/v1/auth/mfa-verify", json={
            "nifPasaporte": "ABC12345678",
            "codigoMFA": "123456",
        })

        assert mfa_resp.status_code == 401
        data = mfa_resp.json()
        assert "Ninguna sesion MFA activa" in data.get("detail", "")


# ---------------------------------------------------------------------------
# Tests de validacion del codigo OTP
# ---------------------------------------------------------------------------

class TestMFAValidacionCodigo:

    def test_mfa_codigo_incorrecto_return_401(self, clean_client):
        """OTP incorrecto (pero numérico) → 401 (no 400)."""
        client, mock_user = clean_client

        client.post("/api/v1/auth/login", json={
            "nifPasaporte": "ABC12345678",
            "password": "pass1234",
        })

        mfa_resp = client.post("/api/v1/auth/mfa-verify", json={
            "nifPasaporte": "ABC12345678",
            "codigoMFA": "999999",                       # numeric pero incorrecto
        })

        assert mfa_resp.status_code == 401

        
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_otp_from_session(nif: str) -> str:
    """Utilidad para extraer el OTP de la sesion interna despues de un login."""
    mfa_key = f"mfa_{nif}"
    return _sessions[mfa_key]["otp"]
