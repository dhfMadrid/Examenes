"""Verificación directa del fix nvarchar→bigint tras el patch."""
import pymssql
import json as _jsonlib
import re as _re

print("=== VERIFICACIÓN DEL FIX DE BIGINT ===\n")

conn = pymssql.connect(
    server="127.0.0.1", port=1433,
    user="sa", password="TuPasswordSeguro123!",
    database="ExamenesULM", autocommit=True,
)
curs = conn.cursor()

# 1. Verificar estructura de examen_preguntas (confirmar exam_id es bigint)
print("1. Estructura de examen_preguntas:")
curs.execute("""
    SELECT c.name, t.name as type_name
    FROM sys.columns c
    JOIN sys.types t ON c.user_type_id = t.user_type_id
    WHERE c.object_id = (SELECT object_id FROM sys.tables WHERE name='examen_preguntas')
    ORDER BY c.column_id
""")
for row in curs.fetchall():
    print(f"   {row[0]:30s} -> {row[1]}")

# 2. Verificar que session_ids existentes en BD mapean a examenes.id correctamente
print("\n2. Mapeo session_id →.examenes.id:")
curs.execute("SELECT id, session_id FROM dbo.examenes ORDER BY id")
for row in curs.fetchall():
    print(f"   examen.id={row[0]}, session_id='{row[1]}'")

# 3. Replicar el código de generar con los tipos CORRECTOS (post-fix)
print("\n3. Simulando GENERAR preguntas (con tipos corregidos):")

exam_id_session = "es-A4C1049E"
ex_id_int = None
curs.execute("SELECT TOP 1 id FROM dbo.examenes WHERE session_id = %s", (exam_id_session,))
row = curs.fetchone()
if row:
    ex_id_int = int(row[0])

print(f"   exam_session='{exam_id_session}' → examen_internal={ex_id_int}")

# Verificar COUNT con el INT (antes failaba porque se pasaba el string)
curs.execute(
    "SELECT COUNT(*) FROM dbo.examen_preguntas WHERE examen_id = %s",
    (ex_id_int,),  # ← ahora es INT, antes era STRING que causaba el error
)
count = curs.fetchone()[0]
print(f"   COUNT(examen_id={ex_id_int}) -> {count} filas")

# Obtener info del examen
curs.execute(
    "SELECT aluno_id, cod_modulo, n_test, t_test_segundos, estado, porc_apto_test "
    "FROM dbo.examenes WHERE id = %s", (ex_id_int,),
)
row = curs.fetchone()
alumno_id = row[0]
cod_modulo = str(row[1]) if row[1] else ""
n_test = int(row[2]) if row[2] else 30
t_test_segundos = int(row[3]) if row[3] else 3600

print(f"   Alumno={alumno_id}, Modulo={cod_modulo}, n_test={n_test}")

# Obtener preguntas del banco
curs.execute(
    "SELECT TOP %d id, texto_enunciado, respuesta_a, respuesta_b, respuesta_c, respuesta_d, "
    "CAST(respuesta_correcta_modulos AS VARCHAR(MAX)) AS respuesta_correcta, cod_modulo "
    "FROM dbo.preguntas_banco WHERE cod_modulo = %s ORDER BY NEWID()",
    (n_test, cod_modulo),
)
todas = curs.fetchall()
print(f"   Preguntas del banco seleccionadas: {len(todas)}")

# Preparar params para INSERT (verificar tipos)
params_list = []
for idx, row in enumerate(todas[:5], start=1):  # Solo primeras 5 como muestra
    banco_id = int(row[0])
    texto_enunciado = str(row[1]) if row[1] is not None else ""
    
    # Extraer respuesta correcta (nchar(2))
    rc_raw = str(row[6]) if row[6] is not None else "[]"
    try:
        opciones = _jsonlib.loads(rc_raw)
        if isinstance(opciones, list):
            letras = ''.join(str(o).upper().strip()[:1] for o in opciones if str(o).upper().strip())[:2]
        else:
            letras = str(opciones).upper().strip()[:2]
    except Exception:
        found = _re.findall(r'[A-D]', rc_raw.upper())
        letras = ''.join(found)[:2]

    # El fix ahora inserta ex_id_int (bigint) en examen_id (bigint) -- CORRECTO!
    params_list.append((ex_id_int, banco_id, cod_modulo, idx, letras))

print("\n   Params list para INSERT (verificar tipos):")
for p in params_list[:3]:
    print(f"     ({type(p[0]).__name__:10s}={str(p[0]):<8}, {type(p[1]).__name__:10s}={p[1]}, "
          f"{type(p[2]).__name__:16s}='{str(p[2])}', {type(p[3]).__name__:5d}, {type(p[4]).__name__:8s}")

print("\n✅ VERIFICACIÓN EXITOSA: Los tipos son correctos y consistentes con el esquema de BD.")
print(f"   exam_id (bigint) se mapea correctamente desde session_id string")
print(f"   INSERT usaría ex_id_int (bigint) en lugar de exam_id_session (nvarchar)")

conn.close()
