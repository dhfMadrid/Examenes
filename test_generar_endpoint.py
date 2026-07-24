"""Verificar que el endpoint Generar preguntas funciona tras el fix de bigint."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend/app"))

import json

# Import desde main.py del backend
from app.main import generate_exam_questions, _obtener_examen_int_id_por_session, obtener_exam_questions


def test_generar_exam_questions():
    """Simula la llamada completa del endpoint generar_sin_cambiar_datos."""
    from sqlalchemy import text
    from fastapi.testclient import TestClient

    # Importar el cliente de FastAPI
    from app.main import app as fastapi_app

    client = TestClient(fastapi_app)

    # Endpoint POST /api/v1/examenes/{examId}/generar
    exam_id = "es-A4C1049E"
    
    try:
        response = client.post(f"/api/v1/examenes/{exam_id}/generar")
    except Exception as e:
        print(f"ERROR al llamar endpoint: {e}")
        sys.exit(1)

    print(f"Status: {response.status_code}")
    
    if response.status_code == 404:
        # Quizas el examen no existe -- ver por qué
        data = response.json()
        print(f"Respuesta: {data}")
        if "Examen" in str(data) and "no encontrado" in str(data):
            print("⚠️ El examen con session_id es-A4C1049E no existe en BD.")
            # Verificar exámenes disponibles
            import pymssql
            conn = pymssql.connect(server="127.0.0.1", port=1433, user="sa", 
                                   password="TuPasswordSeguro123!", database="ExamenesULM")
            curs = conn.cursor()
            curs.execute("SELECT id, session_id FROM dbo.examenes ORDER BY id")
            ex = curs.fetchall()
            print(f"Exámenes en BD: {[(r[0], r[1]) for r in ex]}")
            print(f"Preguntas por módulo:")
            curs.execute("SELECT cod_modulo, COUNT(*) FROM dbo.preguntas_banco GROUP BY cod_modulo")
            for r in curs.fetchall():
                print(f"  modulo={r[0]}, count={r[1]}")
            conn.close()
        else:
            print(f"Respuesta inesperada: {data}")
    elif response.status_code == 200:
        data = response.json()
        print(f"Respuesta OK: {data}")
        if data.get("total_nuevo", 0) > 0:
            print("✅ Se generaron preguntas correctamente.")
            # Verificar que las preguntas se insertaron correctamente
            import pymssql
            conn = pymssql.connect(server="127.0.0.1", port=1433, user="sa", 
                                   password="TuPasswordSeguro123!", database="ExamenesULM")
            curs = conn.cursor()
            exam_int_id = _obtener_examen_int_id_por_session(exam_id)
            curs.execute(
                "SELECT TOP 5 ep.orden, ep.pregunta_banco_id, ep.resp_correcta FROM dbo.examen_preguntas ep WHERE ep.examen_id = %s ORDER BY ep.orden",
                (exam_int_id,)
            )
            rows = curs.fetchall()
            for r in rows:
                print(f"  fila: orden={r[0]}, banco_id={r[1]}, resp_correcta='{str(r[2])}'")
            conn.close()
        else:
            print("⚠️ Preguntas ya generadas previamente (ok, no cambiamos datos).")
    else:
        print(f"ERROR HTTP {response.status_code}")
        data = response.json()
        print(f"Respuesta: {data}")

    return response.status_code


def test_obtener_exam_questions():
    """Verificar endpoint obtener_preguntas del examen."""
    from fastapi.testclient import TestClient
    from app.main import app as fastapi_app
    
    client = TestClient(fastapi_app)
    
    exam_id = "es-A4C1049E"
    
    # Primero generar (para tener datos)
    response = client.post(f"/api/v1/examenes/{exam_id}/generar")
    
    if response.status_code != 200:
        print(f"⚠️ No pude generar preguntas: {response.status_code}")
        return
    
    # Ahora obtener
    response = client.get(f"/api/v1/examenes/{exam_id}/preguntas")
    print(f"\n=== Test obtener_preguntas ===")
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        preguntas = data.get("preguntas", [])
        print(f"Preguntas obtenidas: {len(preguntas)}")
        if preguntas:
            p = preguntas[0]
            print(f"  primera pregunta:")
            print(f"    id_banco={p['id_banco']}")
            print(f"    orden_en_examen={p['orden_en_examen']}")
            print(f"    texto='{p['texto_enunciado'][:60]}...'")
            print(f"    respuesta_correcta={p['respuesta_correcta']}")
            print("✅ Obtención de preguntas funciona correctamente.")
    else:
        print(f"ERROR: {response.json()}")


if __name__ == "__main__":
    status1 = test_generar_exam_questions()
    
    # Solo verificar obtener si generó
    if status1 == 200:
        test_obtener_exam_questions()
    
    print("\n=== RESUMEN ===")
    print("✅ Si no hubo errores de tipo nvarchar→bigint, el fix funciona.")
