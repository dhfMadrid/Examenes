# Test direct connection and login flow against real SQL Server
import pymssql
import hashlib
import secrets

print("=== Testing DB Connection ===")
conn = pymssql.connect(
    server='127.0.0.1',
    port=1433,
    user='sa',
    password="TuPasswordSeguro123!",
    database='ExamenesULM'
)
curs = conn.cursor()

# Check alumno table
curs.execute("SELECT COUNT(*) FROM dbo.Alumno")
count_alumnos = curs.fetchone()[0]
print(f"Alumnos in DB: {count_alumnos}")

if count_alumnos > 0:
    # Get demo user
    curs.execute("SELECT Id, NifPasaporte, Nombre, PasswordHash, Salt, Activo FROM dbo.Alumno")
    rows = curs.fetchall()
    for row in rows:
        print(f"  - {row[1]} | {row[2]} | Active={row[5]}")
        uid, nif, nombre, pw_hash, salt, activo = row
        
        # Test hash like main.py does
        pw = "Demo1234"
        salt_bytes = bytes(row[3])
        
        print(f"\n=== Password Verification ===")
        print(f"NIF: {row[1]}")
        print(f"PW: Demo1234")
        
        # Method 1: decode as-is (main.py does decode(errors='replace'))
        computed_1 = hashlib.sha256((pw + salt_bytes.decode(errors='replace')).encode()).digest()
        stored = bytes(row[2])
        match_1 = computed_1 == stored
        
        print(f"Method 1 (decode errors=replace): {computed_1.hex()}")
        print(f"Stored:                          {stored.hex()}")
        print(f"Match: {match_1}")
        
        if not match_1:
            # Method 2: try different salt formats
            raw_salt = row[3]
            for method_name, calc_func in [
                ("utf-8 decode", lambda s: hashlib.sha256((pw + s.decode('utf-8')).encode()).digest()),
                ("latin-1 decode", lambda s: hashlib.sha256((pw + s.decode('latin-1')).encode()).digest()),
                ("hex decode", lambda s: hashlib.sha256((pw + s.hex()).encode()).digest()),
            ]:
                try:
                    result = calc_func(raw_salt)
                    print(f"Method '{method_name}': {result.hex()} - Match={result==stored}")
                except Exception as e:
                    pass
        
        # Method 3: if Salt is uniqueidentifier, maybe we need to decode differently  
        salt_val = row[3]
        if hasattr(salt_val, 'hex'):
            print(f"Salt hex representation: {salt_val.hex()}")
        
# Check other tables
curs.execute("SELECT COUNT(*) FROM dbo.examenes")
count_examenes = curs.fetchone()[0]
print(f"\nExamenes in DB: {count_examenes}")

curs.execute("SELECT COUNT(*) FROM dbo.preguntas_banco")
count_questions = curs.fetchone()[0]
print(f"Preguntas in banco: {count_questions}")

conn.close()
