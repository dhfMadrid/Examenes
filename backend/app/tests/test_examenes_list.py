"""test_examenes_list.py -- Tests para GET /api/v1/examenes.

Ejecutar desde root del proyecto:
    python -m pytest backend/app/tests/test_examenes_list.py -v
"""
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

_tests_dir = Path(__file__).resolve().parent.parent.parent  # ...backend/
sys.path.insert(0, str(_tests_dir))

import pytest
from fastapi.testclient import TestClient
from app.main import app


def _mock_conn_list_examenes():
    """Mock de DB con filas reales de examenes."""
    conn = MagicMock()
    cursor = MagicMock()
    
    # SQL: SELECT id, alumno_id, estado, cod_modulo, n_test, t_test_segundos, 
    #      fecha_examen, porc_apto_test, session_id FROM dbo.examenes ORDER BY id
    
    rows = [
        (1, 10, 0, "010", 30, 5400, "2026-07-15T09:00:00Z", 75.0, ""),
        (2, 10, 1, "030", 45, 3600, "2026-07-16T10:00:00Z", 80.0, None),
        (3, 10, 2, "050", 90, 7200, None, 90.0, ""),
    ]
    
    cursor.fetchall.return_value = rows
    cursor.rowcount = len(rows)
    conn.cursor.return_value = cursor
    return conn


def _mock_conn_list_empty():
    """Mock de DB sin examenes (lista vacia)."""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.fetchall.return_value = []
    conn.cursor.return_value = cursor
    return conn


class TestExamenesList:

    def test_devuelve_lista_de_examenes(self):
        """GET /api/v1/examenes retorna {examenes: [...]} con datos."""
        mock_db = _mock_conn_list_examenes()
        
        with patch("app.main._get_db", return_value=mock_db):
            resp = TestClient(app).get("/api/v1/examenes")

        assert resp.status_code == 200
        data = resp.json()
        assert "examenes" in data
        assert isinstance(data["examenes"], list)
        assert len(data["examenes"]) == 3
    
    def test_cada_examen_tiempo_en_segundos(self):
        """Cada examen tiene tTestSegundos como int > 0."""
        mock_db = _mock_conn_list_examenes()
        
        with patch("app.main._get_db", return_value=mock_db):
            resp = TestClient(app).get("/api/v1/examenes")

        data = resp.json()
        for exam in data["examenes"]:
            assert "tTestSegundos" in exam
            assert isinstance(exam["tTestSegundos"], int)
            assert exam["tTestSegundos"] > 0
    
    def test_cada_examen_tiene_modulo(self):
        """Cada examen tiene codModulo y moduloDescricao validos."""
        mock_db = _mock_conn_list_examenes()
        
        with patch("app.main._get_db", return_value=mock_db):
            resp = TestClient(app).get("/api/v1/examenes")

        data = resp.json()
        assert len(data["examenes"]) == 3
        
        first = data["examenes"][0]
        assert first["codModulo"] == "010"
        assert "Air Law" in first["moduloDescricao"]
        
        second = data["examenes"][1]
        assert second["codModulo"] == "030"
        assert "Perflight" in second["moduloDescricao"]
    
    def test_nTest_si_es_none_usa_default_30(self):
        """Si n_test es None en BD -> 30 de default."""
        mock_db = MagicMock()
        cursor = MagicMock()
        # Cambiar fila[4] (n_test) a None
        empty_rows = [(99, 20, 1, "070", None, None, None, None, "")]
        cursor.fetchall.return_value = empty_rows
        mock_db.cursor.return_value = cursor
        
        with patch("app.main._get_db", return_value=mock_db):
            resp = TestClient(app).get("/api/v1/examenes")

        data = resp.json()
        exam = data["examenes"][0]
        assert exam["nTest"] == 30
    
    def test_nTest_si_tiene_valor_usa_ese_val(self):
        """Si n_test tiene valor en BD, usar ese valor."""
        mock_db = MagicMock()
        cursor = MagicMock()
        rows_with_value = [(99, 20, 1, "070", 15, 3600, None, None, "")]
        cursor.fetchall.return_value = rows_with_value
        mock_db.cursor.return_value = cursor
        
        with patch("app.main._get_db", return_value=mock_db):
            resp = TestClient(app).get("/api/v1/examenes")

        data = resp.json()
        exam = data["examenes"][0]
        assert exam["nTest"] == 15


class TestExamenesListFilters:

    def test_con_nif_pasaporte_filtro(self):
        """Con nif_pasaporte -> filtra por alumno."""
        mock_db = MagicMock()
        cursor = MagicMock()
        
        # Primera llamada: SELECT Id from dbo.Alumno WHERE NifPasaporte...
        cursor.fetchone.side_effect = [(42,)]
        
        # Segunda llamada (dentro de list_examenes): SELECT examenes WHERE alumno_id = 42
        exam_rows = [(1, 42, 0, "060", 25, 5400, None, 80.0, "")]
        cursor.fetchall.side_effect = [exam_rows]
        
        mock_db.cursor.return_value = cursor
        
        with patch("app.main._get_db", return_value=mock_db):
            resp = TestClient(app).get("/api/v1/examenes?nif_pasaporte=TESTUSER999")

        assert resp.status_code == 200


class TestExamenesListSinData:

    def test_sin_examenes_en_bd(self):
        """Si no hay examenes en BD -> lista vacia."""
        mock_db = _mock_conn_list_empty()
        
        with patch("app.main._get_db", return_value=mock_db):
            resp = TestClient(app).get("/api/v1/examenes")

        assert resp.status_code == 200
        data = resp.json()
        assert data["examenes"] == []

