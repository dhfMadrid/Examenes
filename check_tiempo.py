"""Trace completo de valores de tiempo."""
import pymssql

conn = pymssql.connect(server="127.0.0.1", port=1433, user="sa", password="TuPasswordSeguro123!", database="ExamenesULM")
curs = conn.cursor()

# Valores reales en BD
curs.execute("""
    SELECT id, n_test, t_test_segundos, estado, fecha_examen 
    FROM dbo.examenes WHERE session_id = 'es-A4C1049E'
""")
row = curs.fetchone()

if row:
    eid, n_test_val, t_test_seg, estado, fecha = row
    print(f"BD examen es-A4C1049E:")
    print(f"  n_test           = {n_test_val}")       # columna real de BD
    print(f"  t_test_segundos   = {t_test_seg}")      # columna real
    print(f"  estado           = {estado}")
    print(f"  fecha_examen     = {fecha}")

conn.close()
