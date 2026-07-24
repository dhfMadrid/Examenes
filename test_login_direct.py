"""Testear login paso a paso contra SQL Server real."""
import pymssql
import hashlib

conn = pymssql.connect(
    server='127.0.0.1',
    port=1433,
    user='sa',
    password='TuPa...NAME = "ExamenesULM"
curs = conn.cursor()

print("✅ Conexión DB OK")
print("\n--- Paso 1: Buscar alumno por NIF ---")
nif = "12345678Z".strip().upper()
try:
    curs.execute(
        "SELECT Id, Nombre, PasswordHash, Salt, Activo "
        "FROM dbo.Alumno WHERE NifPasaporte = %s AND Activo = 1",
        (nif,)
    )
    row = curs.fetchone()
    if not row:
        print("❌ Row is None - alumno no encontrado en DB")
        conn.close()
        
    id_, nombre, pw_hash, salt, activo = row[0], str(row[1]), row[2], bytes(row[3]), bool(row[4])
    print(f"✅ Alumno encontrado:")
    print(f"   Id={id_}, Nombre={nombre}")
    print(f"   Activo={activo}")
    print(f"   Salt type={type(salt).__name__}, salt={salt.hex()}")
    
except Exception as e:
    print(f"❌ Error al buscar alumno: {e}")

print("\n--- Paso 2: Verificar hash (como main.py) ---")
pw = "Demo1234"
if row:
    # Reproducir exactamente _hash_password de main.py
    pw_hash = hashlib.sha256((pw + salt.decode(errors="replace")).encode()).digest()
    
    # Comparar
    stored_bytes = bytes(pw_hash)
    
    print(f"   computed hash={pw_hash.hex()}")
    print(f"   stored hash ={stored_hex}")
    print(f"   {'✅ MATCH' if pw_hash == stored else '❌ NO MATCH'}")

print("\n--- Paso 3: Probar password correcto ---")
# Si no coincide, testear con "Demo1234" sin salt decode
try:
    curs.execute(
        "SELECT PasswordHash, Salt FROM dbo.Alumno WHERE NifPasaporte=%s",
        (nif,)
    )
    row2 = curs.fetchone()
    stored_hash = bytes(row2[0]) if row2 else None
    raw_salt = bytes(row2[1]) if row2 else b''
    
    # Método 1: decode salt como UTF-8 + concat
    print(f"\n   Salt raw hex: {raw_salt.hex()}")
    
    pw_hash_method1 = hashlib.sha256((pw + raw_salt.decode(errors="replace")).encode()).digest()
    print(f"   Method1 (decode utf-8): {pw_hash_method1.hex()}")
    print(f"   Stored:        : {stored_hash.hex()}")
    print(f"   Match: {pw_hash_method1 == stored_hash}")
    
conn.close()
print("\n✅ TEST COMPLETADO")
