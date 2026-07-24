"""Verificar si existe usuario demo en la tabla Alumno."""
import pymssql

conn = pymssql.connect(
    server='127.0.0.1', port=1433, user='sa',
    password='TuPasswordSeguro123!', database='ExamenesULM'
)
curs = conn.cursor()

# Conteo total
curs.execute("SELECT COUNT(*) FROM dbo.Alumno")
count = curs.fetchone()
print(f"Total alumnos en BD: {count[0]}")

if count[0] > 0:
    curs.execute("SELECT Id, NifPasaporte, Nombre, Activo FROM dbo.Alumno")
    rows = curs.fetchall()
    for r in rows:
        print(f"  [{r[0]}] {r[1]:15s} | {r[2]:20s} | Activo:{r[3]}")

# Verificar usuario demo especifico
curs.execute("SELECT Id, NifPasaporte FROM dbo.Alumno WHERE NifPasaporte = %s", ("12345678Z",))
row = curs.fetchone()
print(f"\nDemo 12345678Z: {'EXISTE' if row else 'NO EXISTE'}")

conn.close()
