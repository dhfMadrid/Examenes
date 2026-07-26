"""test_obtener_preguntas.py -- Tests para GET /api/v1/examenes/{exam_id}/preguntas.

Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_obtener_preguntas.py -v
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
# Helpers: mock del endpoint GET /examenes/{exam_id}/preguntas
#
# Flujo real del endpoint:
#   1) examen_int_id = _obtener_examen_int_id_por_session(exam_id)     ← patcheado
#   2) cur.execute("SELECT COUNT(*) FROM dbo.examen_preguntas WHERE examen_id=%s")
#      count = curs.fetchone()[0]   ← fetchone deve devolver tupla subscriptable
#   3) si count == 0 → HTTPException 404
#   4) cur.execute(JOIN query, (examen_int_id,))
#      rows = curs.fetchall()
# ---------------------------------------------------------------------------

def _mock_conn_with_questions(num_q=3):
    """Examen encontrado con N preguntas generadas."""
    conn = MagicMock()
    cur = MagicMock()

    # COUNT query -> fetchone devuelve (N,) -- tupla subscriptable
    cur.fetchone.return_value = (num_q,)

    # JOIN query -> fetchall devuelve filas simuladas
    rows = []
    for i in range(1, num_q + 1):
        respuestas_json = _json.dumps(["B"]) if i <= 2 else _json.dumps(["A"])
        fila = (
            i,                              # ep.orden
            i + 100,                        # pb.id AS banco_id
            f"Pregunta {i} de examen",      # texto_enunciado
            f"Opcion A{i}",                  # respuesta_a
            f"Opcion B{i}",                  # respuesta_b
            f"Opcion C{i}",                  # respuesta_c
            f"Opcion D{i}",                  # respuesta_d
            respuestas_json,                 # respuesta_correcta (string JSON)
            None,                            # url_fichero
        )
        rows.append(fila)
    cur.fetchall.return_value = rows

    conn.cursor.return_value = cur
    return conn


def _mock_conn_no_questions():
    """Examen existe pero 0 preguntas generadas -> debe dar 404."""
    conn = MagicMock()
    cur = MagicMock()
    # El endpoint hace: count = curs.fetchone()[0] -- necesita tupla subscriptable (0,)
    cur.fetchone.return_value = (0,)

    conn.cursor.return_value = cur
    return conn


# ---------------------------------------------------------------------------
# Tests exitosos de obtener preguntas
# ---------------------------------------------------------------------------

class TestObtenerPreguntasExitoso:

    def test_obtener_preguntas_retorna_listado(self):
        """GET /examenes/{id}/preguntas retorna {preguntas: [...]} con items."""
        conn = _mock_conn_with_questions(3)

        with patch("app.main._get_db", return_value=conn), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1):
            resp = TestClient(app).get("/api/v1/examenes/es_test/preguntas")

        assert resp.status_code == 200
        data = resp.json()
        assert "preguntas" in data
        preguntas = data["preguntas"]
        assert isinstance(preguntas, list)
        assert len(preguntas) == 3

    def test_cada_pregunta_tiene_id_banco(self):
        """Cada elemento tiene id_banco como int."""
        conn = _mock_conn_with_questions(3)

        with patch("app.main._get_db", return_value=conn), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1):
            resp = TestClient(app).get("/api/v1/examenes/es_test/preguntas")

        data = resp.json()
        for p in data["preguntas"]:
            assert "id_banco" in p
            assert isinstance(p["id_banco"], int)

    def test_cada_pregunta_tiene_texto_enunciado(self):
        """Cada objeto pregunta tiene texto_enunciado como string."""
        conn = _mock_conn_with_questions(2)

        with patch("app.main._get_db", return_value=conn), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1):
            resp = TestClient(app).get("/api/v1/examenes/es_test/preguntas")

        data = resp.json()
        for p in data["preguntas"]:
            assert "texto_enunciado" in p
            assert isinstance(p["texto_enunciado"], str)

    def test_respuesta_correcta_parseada_json(self):
        """La columna respuesta_correcta parseada es lista de strings."""
        conn = _mock_conn_with_questions(3)

        with patch("app.main._get_db", return_value=conn), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1):
            resp = TestClient(app).get("/api/v1/examenes/es_test/preguntas")

        assert resp.status_code == 200
        data = resp.json()
        for p in data["preguntas"]:
            rc = p.get("respuesta_correcta", [])
            assert isinstance(rc, list)
            assert len(rc) > 0

    def test_ordenes_seguidas(self):
        """Las preguntas tienen orden_en_examen creciente."""
        conn = _mock_conn_with_questions(5)

        with patch("app.main._get_db", return_value=conn), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1):
            resp = TestClient(app).get("/api/v1/examenes/es_test/preguntas")

        data = resp.json()
        ordenes = [p["orden_en_examen"] for p in data["preguntas"]]
        assert ordenes == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# Tests de errores
# ---------------------------------------------------------------------------

class TestObtenerPreguntasSinGenerar:

    def test_sin_preguntas_generadas_deve_return_404(self):
        """Si no se genero examen antes -> 404."""
        conn = _mock_conn_no_questions()

        with patch("app.main._get_db", return_value=conn), \
             patch("app.main._obtener_examen_int_id_por_session", return_value=1):
            resp = TestClient(app).get("/api/v1/examenes/es_sin_generar/preguntas")

        assert resp.status_code == 404

