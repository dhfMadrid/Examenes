"""Verificar estado real de BD y tabla Alumno."""
import pymssql

conn = pymssql.connect(
    server='127.0.0.1', port=1433, user='sa',
    password='TuPasswordSeguro123!', database='ExamenesULM'
)
curs = conn.cursor()

print("=== Tablas en dbo ===")
rows = curs.execute(
    "SELECT name FROM sys.tables WHERE schema_id = SCHEMA_ID('dbo')"
).fetchall()
for r in rows:
    print(f"  - {r[0]}")

print("\n=== Columnas de Alumno ===")
cols = curs.execute(
    "SELECT COLUMN_NAME, DATA_TYPE, MAX_LENGTH FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='Alumno' ORDER BY ORDINAL_POSITION"
).fetchall()
for c in cols:
    print(f"  {c[0]:25s} -> {c[1]:15s} (max:{c[2]})")

print("\n=== Datos en dbo.Alumno ===")
count = curs.execute("SELECT COUNT(*) FROM dbo.Alumno").fetchone()
print(f"Total filas: {count[0]}")

if count[0] > 0:
    rows = curs.execute(
        "SELECT Id, NifPasaporte, Nombre, Activo FROM dbo.Alumno"
    ).fetchall()
    for r in rows:
        print(f"  [{r[0]}] {r[1]:15s} | {r[2]:20s} | Activo:{r[3]}")

# Verificar si usuario demo existe
nif_demo = "12345678Z"
row = curs.execute(
    "SELECT Id, NifPasaporte FROM dbo.Alumno WHERE NifPasaporte = %s", (nif_demo,)
).fetchone()
print(f"\n=== Demo {nif_demo}: {'EXISTE' if row else 'NO EXISTE'} ===")

conn.close()
