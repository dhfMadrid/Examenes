"""test_login.py — Tests para POST /api/v1/auth/login.

Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_login.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import hashlib

# ...backend/app/tests/ → añadir backend/ al path para que `app.main` sea importable
_tests_dir = Path(__file__).resolve().parent.parent.parent           # ...backend/
sys.path.insert(0, str(_tests_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app


def _make_mock_user(password: str, correo=None):
    """Construye un mock de usuario con el hash correcto para `password`."""
    expected_hash = hashlib.sha256(password.encode()).digest()
    return {
        "id": 1,
        "nombre": "Juan Perez",
        "password_hash": expected_hash,
        "activo": True,
        "correo_electronico": correo,
    }


# ---------------------------------------------------------------------------
# Tests de credenciales VALIDAS
# ---------------------------------------------------------------------------

class TestLoginExitoso:

    def test_login_exitoso_sin_email(self):
        """Usuario con credenciales correctas y sin email → jwtToken directo."""
        password = "pass1234"
        mu = _make_mock_user(password, correo=None)

        with patch("app.main.buscar_alumno", return_value=mu):
            with patch("app.main._get_db"):
                resp = TestClient(app).post("/api/v1/auth/login", json={
                    "nifPasaporte": "ABC12345678",
                    "password": password,
                })

        assert resp.status_code == 200
        data = resp.json()
        assert data["exitoso"] is True
        assert data["requiereMFA"] is False
        assert data["jwtToken"] is not None
        assert "email no configurado" in (data.get("mensaje") or "")


# ---------------------------------------------------------------------------
# Tests de credenciales INVALIDAS
# ---------------------------------------------------------------------------

class TestLoginFallido:

    def test_usuario_no_encontrado(self):
        """NIF no existe → 401."""
        with patch("app.main.buscar_alumno", return_value=None):
            with patch("app.main._get_db"):
                resp = TestClient(app).post("/api/v1/auth/login", json={
                    "nifPasaporte": "NOEXISTE",
                    "password": "qualquier Cosa",
                })

        assert resp.status_code == 401
        data = resp.json()
        assert data["detail"] == "Credenciales incorrectas"

    def test_password_incorrecto(self):
        """NIF existe pero password no coincide → 401."""
        wrong_hash = b"DIFERENTE_HASH_32_BYTES_PARA_COMP-"
        mu = _make_mock_user("pass1234", correo=None)
        mu["password_hash"] = wrong_hash

        with patch("app.main.buscar_alumno", return_value=mu):
            with patch("app.main._get_db"):
                resp = TestClient(app).post("/api/v1/auth/login", json={
                    "nifPasaporte": "ABC12345678",
                    "password": "wrong_password",
                })

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Tests de normalizacion
# ---------------------------------------------------------------------------

class TestLoginNormalizacion:

    def test_nif_normalizado_mayusculas(self):
        """El backend convierte el NIF a mayúsculas antes de buscarlo."""
        password = "pass1234"
        mu = _make_mock_user(password, correo=None)

        with patch("app.main.buscar_alumno", return_value=mu):
            with patch("app.main._get_db"):
                resp = TestClient(app).post("/api/v1/auth/login", json={
                    "nifPasaporte": "abc12345678",   # minusculas
                    "password": password,
                })

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests de email + MFA
# ---------------------------------------------------------------------------

class TestLoginConEmail:

    def test_login_con_email_requiere_mfa(self):
        """Usuario con email → requiereMFA + tokenTemporal."""
        mu = _make_mock_user("pass1234", correo="maria@gmail.com")

        counter = [0]  # para controlar side_effect llamadas

        def buscar_llamada(nif: str):
            nif_norm = nif.strip().upper()
            if counter[0] == 0:
                counter[0] += 1
                return mu
            else:
                # segunda llamada (quizas de _seed_session_ids o similar)
                return None

        with patch("app.main.buscar_alumno", side_effect=buscar_llamada):
            with patch("app.main._get_db"):
                resp = TestClient(app).post("/api/v1/auth/login", json={
                    "nifPasaporte": "XYZ98765432",
                    "password": "pass1234",
                })

        assert resp.status_code == 200
        data = resp.json()
        assert data["exitoso"] is True
        assert data["requiereMFA"] is True
        assert data["tokenTemporal"] is not None
        assert "Se ha enviado" in (data.get("mensaje") or "")
