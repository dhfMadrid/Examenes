"""test_resultados_examen.py -- Tests para GET /api/v1/resultados/{examen_id}.

Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_resultados_examen.py -v
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

_tests_dir = Path(__file__).resolve().parent.parent.parent  # ...backend/
sys.path.insert(0, str(_tests_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app


# ---------------------------------------------------------------------------
# Helpers: factory de mock para resultados_de_examen.
#
# El endpoint GET /resultados/{examen_id} ejecuta:
#   1) examen_int = _obtener_examen_int_id_por_session(examen_id)
#      - si exam_id empieza por 'es-' → busca en BD (session_id)
#      - si no es numérico y no está en session_id_to_dbid → None
#      - fallback: int(examen_id)
#   2) _obtener_resultado_por_examen(examen_int):
#        curs.execute("SELECT id, examen_id, correctas, fallos, ...
#                      FROM dbo.resultados_examen WHERE examen_id=%s")
#        row = curs.fetchone()  <-- tupla con 14 columnas:
#          [0] id           (int)
#          [1] examen_id    (int)
#          [2] correctas    (int)
#          [3] fallos       (int)
#          [4] no_contestadas(int)
#          [5] porcentaje_acierto(float)
#          [6] es_apto      (bool)
#          [7] nota_final   (float/None)
#          [8] mensaje_resultado(str)
#          [9] fecha_calculo(datetime ← .isoformat()!)  <-- ¡IMPORTANTE!
#          [10] respuestas_json(str/None)
#          [11] tiempo_restante_segundos(int/None)
#          [12] tiempo_total_segundos(int/None)
#          [13] alumno_id   (int)
# ---------------------------------------------------------------------------

_DUMMY_DT = datetime(2026, 7, 27, 10, 30, 0, tzinfo=timezone.utc)


def _mock_conn_with_result():
    """DB retorna resultado en resultados_examen."""
    conn = MagicMock()
    cur = MagicMock()

    result_row = (
        101,                       # [0] id
        5,                         # [1] examen_id
        4,                         # [2] correctas
        1,                         # [3] fallos
        0,                         # [4] no_contestadas
        80.0,                      # [5] porcentaje_acierto
        True,                      # [6] es_apto
        80.0,                      # [7] nota_final
        "APTO",                    # [8] mensaje_resultado
        _DUMMY_DT,                 # [9] fecha_calculo (datetime! .isoformat())
        '[{"numero":1,"respuesta":"A"}]',  # [10] respuestas_json
        1800,                       # [11] tiempo_restante_segundos
        3600,                       # [12] tiempo_total_segundos
        42,                         # [13] alumno_id
    )
    cur.fetchone.return_value = result_row
    conn.cursor.return_value = cur
    return conn


def _mock_conn_no_result():
    """DB: resultados_examen no tiene fila para este examen."""
    conn = MagicMock()
    cur = MagicMock()
    cur.fetchone.return_value = None
    conn.cursor.return_value = cur
    return conn


# ---------------------------------------------------------------------------
# Tests de escenarios exitosos
# ---------------------------------------------------------------------------

class TestResultadoExitoso:

    def test_obtener_resultado_devuelve_datos_completos(self):
        """GET /resultados/{id} con examen finalizado -> 200 con todos los campos."""
        conn = _mock_conn_with_result()

        with patch("app.main._obtener_examen_int_id_por_session", return_value=5), \
             patch("app.main._get_db", return_value=conn):
            resp = TestClient(app).get("/api/v1/resultados/es-result-001")

        assert resp.status_code == 200
        data = resp.json()
        assert data["correctas"] == 4
        assert data["fallos"] == 1
        assert data["no_contestadas"] == 0
        assert data["porcentaje_acierto"] == 80.0
        assert data["es_apto"] is True
        assert data["nota_final"] == 80.0
        assert data["mensaje_resultado"] == "APTO"

    def test_obtener_resultado_include_campos_adicionales(self):
        """La respuesta incluye campos extra: tiempo, alumno_id, respuestas_json."""
        conn = _mock_conn_with_result()

        with patch("app.main._obtener_examen_int_id_por_session", return_value=5), \
             patch("app.main._get_db", return_value=conn):
            resp = TestClient(app).get("/api/v1/resultados/5")

        data = resp.json()
        assert "tiempo_restante_segundos" in data
        assert "tiempo_total_segundos" in data
        assert "alumno_id" in data
        assert "respuestas_json" in data
        assert "fecha_calculo" in data
        assert data["tiempo_restante_segundos"] == 1800
        assert data["tiempo_total_segundos"] == 3600
        assert data["alumno_id"] == 42

    def test_resultado_si_exam_id_es_numeric(self):
        """Si exam_id es numérico y funcion de session devuelve None → fallback int(exam_id)."""
        conn = _mock_conn_with_result()

        with patch("app.main._obtener_examen_int_id_por_session", return_value=None), \
             patch("app.main._get_db", return_value=conn):
            resp = TestClient(app).get("/api/v1/resultados/99")

        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests de errores
# ---------------------------------------------------------------------------

class TestResultadoErrores:

    def test_resultado_no_encontrado(self):
        """No hay resultados almacenados -> 404."""
        conn = _mock_conn_no_result()

        with patch("app.main._obtener_examen_int_id_por_session", return_value=5), \
             patch("app.main._get_db", return_value=conn):
            resp = TestClient(app).get("/api/v1/resultados/es-sin-result")

        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
        assert "No hay resultados" in data["detail"]

    def test_examen_no_encontrado(self):
        """Examen_id no existe en BD y no es numerico -> 404."""
        with patch("app.main._obtener_examen_int_id_por_session", return_value=None):
            resp = TestClient(app).get("/api/v1/resultados/garbage-id-xyz")

        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data
        assert "no encontrado" in data["detail"].lower()


# ---------------------------------------------------------------------------
# Tests de integridad
# ---------------------------------------------------------------------------

class TestResultadoIntegridad:

    def test_tipos_correctos(self):
        """Todos los campos numericos son int/float, no strings."""
        conn = _mock_conn_with_result()

        with patch("app.main._obtener_examen_int_id_por_session", return_value=5), \
             patch("app.main._get_db", return_value=conn):
            resp = TestClient(app).get("/api/v1/resultados/5")

        data = resp.json()
        assert isinstance(data["correctas"], (int, float))
        assert isinstance(data["fallos"], (int, float))
        assert isinstance(data["porcentaje_acierto"], (int, float))
        assert isinstance(data["es_apto"], bool)
        assert isinstance(data["nota_final"], (int, float))
        assert isinstance(data["mensaje_resultado"], str)


# ---------------------------------------------------------------------------
# Tests de flujo normal completo
# ---------------------------------------------------------------------------

class TestResultadoFlujoNormal:

    def test_respuesta_con_datos_completos_desde_db(self):
        """Simula un examen real finalizado con puntaje correcto."""
        result_row = (
            200,                 # id
            10,                  # examen_id
            8,                   # correctas
            2,                   # fallos
            0,                   # no_contestadas
            95.0,                # porcentaje_acierto
            True,                # es_apto
            95.0,                # nota_final
            "APTO",              # mensaje_resultado
            _DUMMY_DT,           # fecha_calculo (datetime!)
            '[{"numero":1,"respuesta":"A"},{"numero":2,"respuesta":"B"}]',
            300,                  # tiempo_restante_segundos
            1800,                 # tiempo_total_segundos
            15,                   # alumno_id
        )

        conn = MagicMock()
        cur = MagicMock()
        cur.fetchone.return_value = result_row
        conn.cursor.return_value = cur

        with patch("app.main._obtener_examen_int_id_por_session", return_value=10), \
             patch("app.main._get_db", return_value=conn):
            resp = TestClient(app).get("/api/v1/resultados/10")

        data = resp.json()
        assert data["correctas"] == 8
        assert data["fallos"] == 2
        assert data["no_contestadas"] == 0
        assert data["porcentaje_acierto"] == 95.0
        assert data["es_apto"] is True
        assert data["nota_final"] == 95.0
        assert data["mensaje_resultado"] == "APTO"

