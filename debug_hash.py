"""Debug completo del login contra BD real."""
import hashlib
import traceback
import sys

HERMES_PY = r"C:\Users\USUARIO\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
import subprocess

script = '''
import pymssql, hashlib

print("=" * 50)
print("CONN -> BD")
print("=" * 50)

conn = pymssql.connect(
    server='127.0.0.1', port=1433, user='sa', password='TuPasswordSeguro123!', 
    database='ExamenesULM'
)
curs = conn.cursor()

# 1. Obtener todos los campos del alumno demo con tipos
print("\\n--- SELECT TOP 1 * ---")
curs.execute("SELECT TOP 1 Id, NifPasaporte, Nombre, PasswordHash, Salt, Activo FROM dbo.Alumno")
row = curs.fetchone()
for i, col in enumerate(row):
    print(f"  [{i}] {type(col).__name__:20s} = {repr(col)[:80]}")

# 2. Usar column_names del cursor (SQL Server driver)
print("\\n--- Column names ---")
curs.execute(
    "SELECT Id, Nombre, PasswordHash, Salt, Activo FROM dbo.Alumno WHERE NifPasaporte = %s AND Activo = 1",
    ('12345678Z',)
)
row2 = curs.fetchone()
print(f"Column names: {[c[0] for c in [None]*10]}")
for i, col in enumerate(row2):
    print(f"  [{i}] {type(col).__name__:20s} = {repr(col)[:80]}")

# 3. Recalcular hash de forma idéntica al backend
print("\\n--- Hash check ---")
NIF_PAS = '12345678Z'

curs.execute(
    "SELECT Id, Nombre, PasswordHash, Salt, Activo FROM dbo.Alumno WHERE NifPasaporte = %s AND Activo = 1",
    (NIF_PAS,)
)
row3 = curs.fetchone()

print(f"  Raw row types: {[type(v).__name__ for v in row3]}")
nid, nombre, pw_hash_raw, salt_bytes_raw, activo = [v for v in row3]

# Salt handling
raw_salt = salt_bytes_raw  
if hasattr(raw_salt, 'int'):  # Python UUID mapped by pymssql
    decoded_salt = raw_salt.bytes
elif isinstance(raw_salt, (bytes, bytearray)):
    decoded_salt = bytes(raw_salt)
else:
    hex_stripped = str(salt_row[3]).replace("-", "").encode() if hasattr(str(row3),"decode") else ""
    # Try as GUID string
    decoded_salt = bytes.fromhex(str(raw_salt).replace("-",""))

print(f"  Salt type after decode: {type(decoded_salt).__name__} len={len(decoded_salt)} hex={decoded_salt.hex()}")

# Password hash is already bytes or needs conversion
if isinstance(pw_hash_raw, str):
    # In case pymssql returns as string (unlikely)
    computed = hashlib.sha256(("Demo1234" + decoded_salt.decode(errors="replace")).encode()).digest()
else:
    pw_bytes = bytes(pw_hash_raw) if hasattr(pw_hash_raw, '__iter__') else pw_hash_raw
    
print(f"  PasswordHash type in db: {type(pw_hash_raw).__name__} len={len(bytes(pw_hash_raw))}")

# Method A: hashlib.sha256(("Demo1234" + salt_str).encode())  -- like seed_db.py
salt_str = decoded_salt.decode(errors="replace")
computed_a = hashlib.sha256(("Demo1234" + salt_str).encode()).digest()
print(f"  Hash A (seed_db-style concat): {computed_a.hex()}")

# Method B: hashlib.sha256(b"D..." + salt_bytes) -- like main.py line 238
computed_b = hashlib.sha256(("Demo1234".encode() + decoded_salt)).digest()
print(f"  Hash B (backend-style bytes):   {computed_b.hex()}")

# Real hash from DB
db_hash = bytes(pw_hash_raw) if not isinstance(pw_hash_raw, bytes) else pw_hash_raw
print(f"  DB hash:                       {db_hash.hex()}")

print(f"\\n  Match A==DB? {computed_a.hex()[:32]}... == {db_hash.hex()[:32]}... ? {computed_a == db_hash}")
print(f"  Match B==DB? {computed_b.hex()[:32]}... == {db_hash.hex()[:32]}... ? {computed_b == db_hash}")

# Also check exact comparison with raw bytes
computed_raw = hashlib.sha256(("Demo1234".encode() + decoded_salt)).digest()
print(f"  Match B==DB? {computed_b == db_hash} (B={len(computed_b)} DB={len(db_hash)})")

conn.close()
'''

result = subprocess.run(
    [HERMES_PY, '-c', script],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
