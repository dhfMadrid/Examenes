"""Verificar si existe usuario demo en la tabla Alumno."""
import pymssql

conn = pymssql.connect(
    server='127.0.0.1', port=1433, user='sa',
    password='TuPasswordSeguro123!', database='ExamenesULM'
)
curs = conn.cursor()

# Verificar usuario demo
row = curs.execute(
    "SELECT Id, NifPasaporte, Nombre, Activo FROM dbo.Alumno WHERE NifPasaporte = %s",
    ("12345678Z",)
).fetchone()

if row:
    print(f"✅ Usuario demo encontrado:")
    print(f"   Id={row[0]}, NIF={row[1]}, Nombre={row[2]}, Activo={row[3]}")
else:
    print("❌ Usuario demo NO existe. Ejecutar seed_db.py")

# Listar todos los alumnos
rows = curs.execute("SELECT Id, NifPasaporte, Nombre, Activo FROM dbo.Alumno").fetchall()
print(f"\n=== Total alumnos en BD: {len(rows)} ===")
for r in rows:
    print(f"  [{r[0]}] {r[1]:15s} | {r[2]:20s} | Activo:{r[3]}")

conn.close()
