import pymssql

conn = pymssql.connect(
    server='127.0.0.1',
    port=1433,
    user='sa',
    password="TuPasswordSeguro123!",
    database='ExamenesULM'
)
curs = conn.cursor()

# 1) Verificar tabla Alumno
try:
    curs.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='Alumno'")
    r = curs.fetchone()
    print(f"Tabla Alumno existe: {r[0] > 0}")
    if r[0] > 0:
        curs.execute("SELECT Id, NifPasaporte, Nombre FROM dbo.Alumno")
        rows = curs.fetchall()
        print(f"Alumnos ({len(rows)}):")
        for row in rows:
            print(f"  {row}")
        
        # Verificar usuario demo
        curs.execute("SELECT * FROM dbo.Alumno WHERE NifPasaporte=%s", ("12345678Z",))
        demo = curs.fetchone()
        print(f"Demo user existe: {demo is not None}")
except Exception as e:
    print(f"Error Alumno: {e}")

# 2) Listar todas las tablas dbo
curs.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_SCHEMA='dbo' ORDER BY TABLE_NAME")
tables = [r[0] for r in curs.fetchall()]
print(f"\nTablas dbo ({len(tables)}):")
for t in tables:
    print(f"  - {t}")

# 3) Para cada tabla, ver columnas
for table_name in tables:
    curs.execute(f"SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table_name}' ORDER BY ORDINAL_POSITION")
    cols = curs.fetchall()
    print(f"\n📋 {table_name}:")
    for c in cols:
        print(f"  .{c[0]} ({c[1]})")

# 4) Contenido de cada tabla si tiene datos
for table_name in tables:
    curs.execute(f"SELECT COUNT(*) FROM [{table_name}]")
    cnt = curs.fetchone()[0]
    if cnt > 0:
        print(f"\n📊 {table_name}: {cnt} registros")
        curs.execute(f"SELECT TOP 1 * FROM [{table_name}]")
        row = curs.fetchone()
        if row:
            col_names = [desc[0] for desc in curs.description]
            for i, c in enumerate(col_names):
                val = row[i]
                # truncar strings largos
                if isinstance(val, str) and len(val) > 40:
                    val = str(val)[:37]+"..."
                print(f"   {c}={val}")

conn.close()
