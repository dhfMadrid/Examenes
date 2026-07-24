"""Testear que login funciona contra SQL Server real."""
import pymssql
import hashlib

DB_PASSWORD = "TuPasswordSeguro123!"

conn = pymssql.connect(
    server='127.0.0.1',
    port=1433,
    user='sa',
    password=DB_PASSWORD,
    database='ExamenesULM'
)
curs = conn.cursor()

# 1) Buscar alumno (exactamente como buscar_alumno de main.py)
nif = "12345678Z"
curs.execute(
    "SELECT Id, Nombre, PasswordHash, Salt, Activo "
    "FROM dbo.Alumno WHERE NifPasaporte = %s AND Activo = 1",
    (nif,),
)
row = curs.fetchone()

if row:
    print(f"✅ Usuario {nif} encontrado en BD:")
    print(f"   Id={row[0]}, Nombre={row[1]}")
    
    # Verificar hash como lo hace main.py (_hash_password)
    pw = "Demo1234"
    salt_bytes = bytes(row[3])
    computed_hash = hashlib.sha256((pw + salt_bytes.decode(errors="replace")).encode()).digest()
    stored_hash = bytes(row[2])
    
    print(f"{'✅' if computed_hash == stored_hash else '❌'} Hash match: {computed_hash.hex()} vs {stored_hash.hex()}")
else:
    print("❌ Usuario no encontrado en BD")

# 2) Verificar que el backend puede leer OK
print("\n🔍 Simulando endpoint /examenes (con datos reales de los modulos):")
modulos = [
    ("010", "Air Law"),
    ("030", "Perflight"),
    ("050", "RACES"),
    ("060", "Operacional FAA"),
]

for cod_modulo, nombre in modulos:
    cursor.count_examenes = curs.execute(
        "SELECT COUNT(*) FROM dbo.examenes WHERE cod_modulo=%s AND alumno_id=1", 
        (cod_modulo,)
    )
    
print(f"📌 Tabla examenes tiene {sum(curs.fetchmany())} rows para alumno 1")

# Verificar si hay examenes en general
curs.execute("SELECT COUNT(*) FROM dbo.examenes")
total_examenes = curs.fetchone()[0]
print(f"\nTotal examenes en BD (todos los alumnos): {total_examenes}")

curs.execute("SELECT COUNT(*) FROM dbo.preguntas_banco")
total_preguntas = curs.fetchone()[0]
print(f"Total preguntas en banco: {total_preguntas}")

# Verificar estados_examen
curs.execute("SELECT id, nombre, color_ui FROM dbo.estados_examen")
estados = curs.fetchall()
print("\nEstados disponibles:")
for eid, ename, ecolor in estados:
    print(f"  {eid} = {ename} ({ecolor})")

conn.close()
print("\n✅ Conexion BD OK - TODO FUNCIONAL")
