"""Debug: reproducible password hash check against actual DB data."""
import pymssql
import hashlib

DB_PASSWORD="TuPa...conn = pymssql.connect(
    server='127.0.0.1',
    port=1433,
    user='sa',
    password=DB_PASSWORD,
    database='ExamenesULM'
)
curs = conn.cursor()

# Get usuario demo from DB exactly as main.py does it
curs.execute(
    "SELECT Id, Nombre, PasswordHash, Salt, Activo "
    "FROM dbo.Alumno WHERE NifPasaporte = %s AND Activo = 1",
    ("12345678Z",),
)
row = curs.fetchone()

print(f"Found user: row = {row}")

if not row:
    print("NO USER in DB")
    conn.close()
    exit(1)

id_, nombre, pw_hash_bytes, salt_bytes_raw, activo = row
password_hash = bytes(pw_hash_bytes)
salt_bytes = bytes(salt_bytes_raw)  # convert to exact bytes like main.py

print(f"Id={id_}, Nombre={nombre}")
print(f"Activo={activo}")
print(f"PW Hash (stored) {password_hash.hex()}")
print(f"Salt (bytes) {salt_bytes.hex()} ({len(salt_bytes)} bytes)")

pw = "Demo1234"

# Exactly como main.py _hash_password:
# return hashlib.sha256((pw + salt.decode(errors="replace")).encode()).digest()
salt_str = salt_bytes.decode(errors="replace")
print(f"Salt as str (decode errors=replace) [{len(salt_str)} chars] = {repr(salt_str[:40])}{'...' if len(salt_str)>40 else ''}")

computed = hashlib.sha256((pw + salt_str).encode()).digest()

print(f"\nComputed hash:  {computed.hex()}")
print(f"Stored hash:    {password_hash.hex()}")
print(f"Match: {computed == password_hash}")

conn.close()
