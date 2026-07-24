"""Clean seed: delete old user and create correct one."""
import pymssql, hashlib, uuid as _uuid

SERV = "127.0.0.1"
PORT = 1433
USER = "sa"
PWO  = "TuPasswordSeguro123!"
DBN  = "ExamenesULM"

# 1) Delete old user if exists
conn = pymssql.connect(server=SERV, port=PORT, user=USER, password=PWO, autocommit=True)
curs = conn.cursor()
curs.execute(f"SELECT name FROM sys.databases WHERE name = N'{DBN}'")
if not curs.fetchone():
    print(f"Creating DB {DBN}...")
    curs.execute(f"CREATE DATABASE {DBN}")

conn.close()

# 2) Delete old demo user and seed fresh one
conn = pymssql.connect(server=SERV, port=PORT, user=USER, password=PWO, database=DBN)
curs = conn.cursor()

# Delete existing
curs.execute("SELECT Id FROM dbo.Alumno WHERE NifPasaporte = %s", ("12345678Z",))
old = curs.fetchone()
if old:
    curs.execute("DELETE FROM dbo.Alumno WHERE NifPasaporte = %s", ("12345678Z",))
    print(f"Deleted old demo user {old}")

# Seed fresh
nif_demo = "12345678Z"
demo_seed = hashlib.sha256(b"demo_salt_12345678Z").digest()[:16]
raw_salt_guid = _uuid.UUID(bytes=demo_seed)
salt_guid_str = str(raw_salt_guid)
pw_hash = hashlib.sha256(("Demo1234" + salt_guid_str).encode()).digest()

curs.execute(
    "INSERT INTO dbo.Alumno (NifPasaporte, Nombre, PasswordHash, Salt, Activo, FechaCreacion) VALUES (%s, %s, %s, %s, 1, GETUTCDATE())",
    (nif_demo, "Demo Usuer", pw_hash, raw_salt_guid),
)

# Verify it worked
conn.commit()
curs.execute("SELECT Id, NifPasaporte, Nombre, Activo FROM dbo.Alumno WHERE NifPasaporte = %s", (nif_demo,))
row = curs.fetchone()

print(f"\n=== New user verified ===")
print(f"  Id={row[0]}, NIF={row[1]}, Nombre=Demo Usuer, Activo=True")
print(f"  Salt (GUID): {str(raw_salt_guid)}")
print(f"  Salt used in hash: {salt_guid_str}")
print(f"  Password: Demo1234")

# Verify hash self-consistent  
verified = hashlib.sha256(("Demo1234" + salt_guid_str).encode()).digest()
print(f"  Hash verified (self): {verified.hex()[:32]}... == pw_hash? {verified.hex()[:8] == pw_hash.hex()[:8]}")

conn.close()
