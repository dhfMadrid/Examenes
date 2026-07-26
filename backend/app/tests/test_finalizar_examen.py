"""test_finalizar_examen.py -- Tests para POST /api/v1/examenes/finalizar.

Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_finalizar_examen.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import json as _json

_tests_dir = Path(__file__).resolve().parent.parent.parent  # ...backend/
sys.path.insert(0, str(_tests_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app


# ---------------------------------------------------------------------------
# Helpers: fábrica de mock para _calcular_y_guardar_resultado.
#
# El endpoint finalizar llama (en orden):
#   1) alumno = _buscar_alumno_por_nif(nifPasaporte)       → None si no hay
#   2) examen_int_id = _obtener_examen_int_id_por_session(examId) → None si no hay
#   3) exam_info = _obtener_examen_info_por_id(examen_int_id) → None si no hay
#   4) _calcular_y_guardar_resultado(...) → dict con correctas/fallos/etc.
#      dentro de _calcular_y_guardar:
#        curs.execute(JOIN examen_preguntas+preguntas_banco WHERE examen_id=%s)
#          fetchall() → [(orden, banco_id, respuesta_correcta), ...]
#        Compara con respuestas_alumno por orden.
# ---------------------------------------------------------------------------

def _mock_calculate_result(correctas=3, fallos=1, no_contestadas=0, porcen=87.50, es_apto=True):
    """Mock de la función interna que devuelve los cálculos."""
    def fn(*a, **kw):
        return {
            "correctas": correctas,
            "fallos": fallos,
            "no_contestadas": no_contestadas,
            "porcentaje_acierto": porcen,
            "es_apto": es_apto,
            "nota_final": porcen if porcen > 0 else 0.0,
        }
    return fn


def _mock_db_calc_with_rows(rows_data):
    """Mock que conecta a la BD y simula fetchall del JOIN en _calcular_y_guardar_resultado."""
    conn = MagicMock()
    cur = MagicMock()

    # Simular rows del SELECT: ep.orden, pb.id, CAST(pb.respuesta_correcta_modulos...)
    cur.fetchall.return_value = rows_data  # [(1, 101, '["A"]'), (2, 102, '["B"]'), ...]
    conn.cursor.return_value = cur

    return conn


# ---------------------------------------------------------------------------
# Tests de escenarios exitosos
# ---------------------------------------------------------------------------

class TestFinalizarExitoso:

    def test_respuesta_exitosa_basica(self):
        """POST /finalizar con datos válidos -> {exitoso: True, mensaje, resultados}."""
        mock_calc = _mock_calculate_result(correctas=3, fallos=2)

        with patch("app.main._buscar_alumno_por_nif", return_value={"id": 42, "nombre": "Juan", "activo": True}), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info, \
             patch("app.main._calcular_y_guardar_resultado", mock_calc):
            mock_info.return_value = {
                "cod_modulo": "moduloA",
                "n_test": 5,
                "t_test_segundos": 3600,
                "porc_apto_test": 80.0,
            }

            resp = TestClient(app).post(
                "/api/v1/examenes/finalizar",
                json={
                    "examId": "es-test-001",
                    "sessionID": "es-test-session",
                    "nifPasaporte": "12345678A",
                    "respuestas": [
                        {"numero": 1, "respuesta": "A"},
                        {"numero": 2, "respuesta": "B"},
                        {"numero": 3, "respuesta": "C"},
                        {"numero": 4, "respuesta": "D"},
                        {"numero": 5, "respuesta": "A"},
                    ],
                    "tiempoRestante": 1800,
                    "totalTiempo": 3600,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["exitoso"] is True
        assert "mensaje" in data
        assert "resultados" in data
        assert data["examId"] == 1  # examen intero db id

    def test_respuestas_contiene_resultados(self):
        """La respuesta contiene el campo 'resultados' con correctas, fallos, etc."""
        mock_calc = _mock_calculate_result(correctas=4, fallos=1, porcen=90.0, es_apto=True)

        with patch("app.main._buscar_alumno_por_nif", return_value={"id": 42, "nombre": "Ana", "activo": True}), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=5), \
             patch("app.main._obtener_examen_info_por_id") as mock_info, \
             patch("app.main._calcular_y_guardar_resultado", mock_calc):
            mock_info.return_value = {
                "cod_modulo": "moduloB",
                "n_test": 5,
                "t_test_segundos": 1800,
                "porc_apto_test": 80.0,
            }

            resp = TestClient(app).post(
                "/api/v1/examenes/finalizar",
                json={
                    "examId": "es-test-002",
                    "sessionID": "es-session-002",
                    "nifPasaporte": "87654321B",
                    "respuestas": [
                        {"numero": 1, "respuesta": "A"},
                        {"numero": 2, "respuesta": "B"},
                        {"numero": 3, "respuesta": "C"},
                        {"numero": 4, "respuesta": "D"},
                        {"numero": 5, "respuesta": "E"},
                    ],
                    "tiempoRestante": 900,
                    "totalTiempo": 1800,
                },
            )

        data = resp.json()
        res = data["resultados"]
        assert res["correctas"] == 4
        assert res["fallos"] == 1
        assert isinstance(res["porcentaje_acierto"], (int, float))
        assert res["es_apto"] is True
        assert "nota_final" in res

    def test_examen_no_apto(self):
        """Si porcentaje_acierto < porc_apto_test -> es_apto=False."""
        mock_calc = _mock_calculate_result(correctas=1, fallos=4, porcen=20.0, es_apto=False)

        with patch("app.main._buscar_alumno_por_nif", return_value={"id": 10, "nombre": "Pepe", "activo": True}), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=3), \
             patch("app.main._obtener_examen_info_por_id") as mock_info, \
             patch("app.main._calcular_y_guardar_resultado", mock_calc):
            mock_info.return_value = {
                "cod_modulo": "moduloA",
                "n_test": 5,
                "t_test_segundos": 3600,
                "porc_apto_test": 80.0,
            }

            resp = TestClient(app).post(
                "/api/v1/examenes/finalizar",
                json={
                    "examId": "es-test-noapto",
                    "sessionID": "es-session-noapto",
                    "nifPasaporte": "NOAPOSTEST",
                    "respuestas": [
                        {"numero": 1, "respuesta": "A"},
                        {"numero": 2, "respuesta": "a"},
                        {"numero": 3, "respuesta": "B"},
                        {"numero": 4, "respuesta": "C"},
                        {"numero": 5, "respuesta": "D"},
                    ],
                    "tiempoRestante": 30,
                    "totalTiempo": 3600,
                },
            )

        data = resp.json()
        assert data["resultados"]["es_apto"] is False


# ---------------------------------------------------------------------------
# Tests de errores
# ---------------------------------------------------------------------------

class TestFinalizarErrores:

    def test_alumno_no_encontrado(self):
        """NIF invalido -> 404 sin encontrar alumno."""
        with patch("app.main._buscar_alumno_por_nif", return_value=None):
            resp = TestClient(app).post(
                "/api/v1/examenes/finalizar",
                json={
                    "examId": "es-test-003",
                    "sessionID": "es-session-003",
                    "nifPasaporte": "INVALID-NIF",
                    "respuestas": [
                        {"numero": 1, "respuesta": "A"},
                    ],
                    "tiempoRestante": 1800,
                },
            )

        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
        assert "Alumno" in data["detail"] and "NIF" in data["detail"]

    def test_examen_no_encontrado(self):
        """ExamId invalido -> 404 sin encontrar examen."""
        with patch("app.main._buscar_alumno_por_nif", return_value={"id": 1, "nombre": "Test", "activo": True}), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=None):
            resp = TestClient(app).post(
                "/api/v1/examenes/finalizar",
                json={
                    "examId": "INVALID-EXAM-ID",
                    "sessionID": "es-session-inv",
                    "nifPasaporte": "VALID-NIF",
                    "respuestas": [],
                    "tiempoRestante": 0,
                },
            )

        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
        assert "examen" in data["detail"].lower()

    def test_info_examen_no_disponible(self):
        """Examen interno no tiene info -> 404."""
        with patch("app.main._buscar_alumno_por_nif", return_value={"id": 1, "nombre": "Test", "activo": True}), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=99), \
             patch("app.main._obtener_examen_info_por_id", return_value=None):
            resp = TestClient(app).post(
                "/api/v1/examenes/finalizar",
                json={
                    "examId": "es-test-99",
                    "sessionID": "es-session-99",
                    "nifPasaporte": "VALID-NIF-2",
                    "respuestas": [],
                    "tiempoRestante": 0,
                },
            )

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests de integridad de datos
# ---------------------------------------------------------------------------

class TestFinalizarIntegridad:

    def test_respuestas_vacias(self):
        """Sin respuestas -> correctas=0, fallos=0."""
        mock_calc = _mock_calculate_result(correctas=0, fallos=0, porcen=0.0, es_apto=False)

        with patch("app.main._buscar_alumno_por_nif", return_value={"id": 5, "nombre": "Vacio", "activo": True}), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1), \
             patch("app.main._obtener_examen_info_por_id") as mock_info, \
             patch("app.main._calcular_y_guardar_resultado", mock_calc):
            mock_info.return_value = {
                "cod_modulo": "moduloA",
                "n_test": 0,
                "t_test_segundos": 3600,
                "porc_apto_test": 80.0,
            }

            resp = TestClient(app).post(
                "/api/v1/examenes/finalizar",
                json={
                    "examId": "es-test-empty",
                    "sessionID": "es-session-empty",
                    "nifPasaporte": "EMPTY-RESP",
                    "respuestas": [],
                    "tiempoRestante": 3600,
                },
            )

        data = resp.json()
        assert data["exitoso"] is True
        res = data["resultados"]
        assert res["correctas"] == 0
        assert res["fallos"] == 0
        assert res["porcentaje_acierto"] == 0.0

