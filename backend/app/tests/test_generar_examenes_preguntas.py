"""test_generar_examenes_preguntas.py -- Tests para POST /api/v1/examenes/{exam_id}/generar.

Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_generar_examenes_preguntas.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

_tests_dir = Path(__file__).resolve().parent.parent.parent  # ...backend/
sys.path.insert(0, str(_tests_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app


# ---------------------------------------------------------------------------
# Helpers: fábrica de mock de cursor por número de preguntas del banco.
# El endpoint genera examenes/preguntas ejecuta en orden SQL sobre el MISMO cursor:
#   (1) SYS.COLUMNS  → fetchall()     ← siempre se ejecuta (bloqueo INFO), pero lo saltamos patcheando funciones auxiliares.
#   (2) _obtener_examen_int_id_por_session(session_id) → patcheado
#   (3) _obtener_examen_info_por_id(examen_int_id)     → patcheado
#   (4) cur.execute("SELECT COUNT(*) FROM dbo.examen_preguntas WHERE examen_id=%s")
#       count = curs.fetchone()[0]       ← fetchone deve devolver tupla subscriptable
#   (5) curs.executemany(insert_sql, params_list)    → ignorado en mock
# ---------------------------------------------------------------------------

def _mock_cursor_success(num_q=30):
    """COUNT=0 (no previas), fetchall de banco con num_q filas."""
    cur = MagicMock()
    # El endpoint hace: count = curs.fetchone()[0]  --  necesita una tupla subscriptable.
    cur.fetchone.return_value = (0,)

    banco_rows = []
    for i in range(1, num_q + 1):
        banco_rows.append((i, f"Pregunta {i}", "A", "B", "C", "D", "[\"A\"]", "moduloA"))
    cur.fetchall.return_value = banco_rows

    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


def _mock_cursor_has_questions(count=5):
    """COUNT=N>0 → ya generadas. fetchone debe devolver (N,)."""
    cur = MagicMock()
    cur.fetchone.return_value = (count,)
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


def _mock_cursor_empty_banco():
    """COUNT 0, pero fetchall vacío → el endpoint devuelve 400 no preguntas."""
    cur = MagicMock()
    cur.fetchone.return_value = (0,)
    cur.fetchall.return_value = []
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


def _mock_cursor_banco_insuficiente(n_banco=1, n_solicitado=30):
    """COUNT 0, fetchall con n_banco < n_solicitado → error 400."""
    cur = MagicMock()
    cur.fetchone.return_value = (0,)
    banco_rows = [(i, f"Pregunta {i}", "A", "B", "C", "D", "[\"A\"]", "moduloA") for i in range(1, n_banco + 1)]
    cur.fetchall.return_value = banco_rows
    conn = MagicMock()
    conn.cursor.return_value = cur
    return conn


# ---------------------------------------------------------------------------
# Tests exitosos
# ---------------------------------------------------------------------------

class TestGenerarExamenExitoso:

    def test_genera_examen_de_preguntas(self):
        """POST /examenes/{id}/generar con session valido -> {ok: True, total_nuevo: N > 0}."""
        n_test = 25
        mock_db = _mock_cursor_success(num_q=n_test)

        with patch("app.main._get_db", return_value=mock_db), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info:
            # info del examen debe tener cod_modulo y n_test
            mock_info.return_value = {
                "cod_modulo": "moduloA",
                "nombre": "Test Exam",
                "n_test": n_test,
            }

            resp = TestClient(app).post("/api/v1/examenes/es-valid-session/generar")

        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["total_nuevo"] > 0

    def test_respuesta_contiene_ok_true(self):
        """La respuesta debe tener ok=True."""
        n_test = 5
        mock_db = _mock_cursor_success(num_q=n_test)

        with patch("app.main._get_db", return_value=mock_db), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info:
            mock_info.return_value = {"cod_modulo": "moduloA", "nombre": "X", "n_test": n_test}

            resp = TestClient(app).post("/api/v1/examenes/es-valid-session/generar")

        data = resp.json()
        assert data["ok"] is True
        assert "total_nuevo" in data
        assert "msg" not in data  # no msg en caso de éxito

    def test_respuesta_contiene_total_nuevo(self):
        """Si se generan preguntas, total_nuevo debe == n_test."""
        n_test = 10
        mock_db = _mock_cursor_success(num_q=n_test)

        with patch("app.main._get_db", return_value=mock_db), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info:
            mock_info.return_value = {"cod_modulo": "moduloA", "nombre": "X", "n_test": n_test}

            resp = TestClient(app).post("/api/v1/examenes/es-valid-session/generar")

        data = resp.json()
        assert "total_nuevo" in data
        assert isinstance(data["total_nuevo"], int)
        # El endpoint retorna len(todas) → que es n_preguntas seleccionado del banco.
        # Como fetchall devuelve exactamente n_test filas: total_nuevo == n_test
        assert data["total_nuevo"] == 10


# ---------------------------------------------------------------------------
# Tests de escenarios fallidos
# ---------------------------------------------------------------------------

class TestGenerarExamenEscenariosFallidos:

    def test_examen_no_encontrado(self):
        """Exam session_id invalido -> 404."""
        with patch("app.main._obtener_examen_int_id_por_session", return_value=None):
            resp = TestClient(app).post("/api/v1/examenes/INVALID-session/generar")

        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data

    def test_preguntas_omitidas_si_previamente_generadas(self):
        """Si ya hay preguntas generadas -> devuelve total_nuevo=0."""
        mock_db = _mock_cursor_has_questions(count=5)

        with patch("app.main._get_db", return_value=mock_db), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info:
            mock_info.return_value = {"cod_modulo": "moduloA", "nombre": "X", "n_test": 30}

            resp = TestClient(app).post("/api/v1/examenes/es-valid2/generar")

        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["total_nuevo"] == 0
        # Verifica que el mensaje indique que ya estaban generadas.
        assert "ya" in data.get("msg", "").lower() or "previamente" in data.get("msg", "").lower()

    def test_no_preguntas_en_banco(self):
        """Si el banco carece de preguntas -> 400."""
        mock_db = _mock_cursor_empty_banco()

        with patch("app.main._get_db", return_value=mock_db), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info:
            mock_info.return_value = {"cod_modulo": "moduloA", "nombre": "X", "n_test": 30}

            resp = TestClient(app).post("/api/v1/examenes/es-valid3/generar")

        assert resp.status_code == 400

    def test_banco_insuficiente_preguntas(self):
        """Si el banco tiene menos preguntas de las necesarias -> 400."""
        mock_db = _mock_cursor_banco_insuficiente(n_banco=1, n_solicitado=30)

        with patch("app.main._get_db", return_value=mock_db), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info:
            mock_info.return_value = {"cod_modulo": "moduloA", "nombre": "X", "n_test": 30}

            resp = TestClient(app).post("/api/v1/examenes/es-valid4/generar")

        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Tests de multiples llamadas
# ---------------------------------------------------------------------------

class TestGenerarExamenMultiplesLlamadas:

    def test_generar_examen_multiples_veces(self):
        """Primera llamada genera, segunda devuelve total_nuevo=0."""
        mock_db_first = _mock_cursor_success(num_q=30)
        mock_db_second = _mock_cursor_has_questions(count=30)

        with patch("app.main._get_db", side_effect=[mock_db_first, mock_db_second]), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info:
            mock_info.return_value = {"cod_modulo": "moduloA", "nombre": "X", "n_test": 30}

            resp1 = TestClient(app).post("/api/v1/examenes/es-valid/generar")
            resp2 = TestClient(app).post("/api/v1/examenes/es-valid/generar")

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        data1 = resp1.json()
        data2 = resp2.json()
        assert data1["total_nuevo"] > 0, f"Se esperaban nuevas preguntas pero got {data1}"
        assert data2["total_nuevo"] == 0
