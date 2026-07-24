"""Testing end-to-end: login contra BD real + MFA."""
import subprocess, json

def curl(cmd):
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return {
        'rc': result.returncode,
        'out': result.stdout.strip(),
        'err': result.stderr.strip()
    }

print("=" * 60)
print("1. HEALTHCHECK")
print("=" * 60)
r = curl(r'curl -s http://127.0.0.1:8001/api/v1/auth/health')
print(f"Health: {r['out']}\n")

# 2. Login con credenciales CORRECTAS (BD)
print("=" * 60)
print("2. LOGIN CON CREDENCIALES CORRECTAS (BD)")
print("=" * 60)
payload = json.dumps({"nifPasaporte": "12345678Z", "password": "Demo1234"})
r = curl(f'curl -s -X POST http://127.0.0.1:8001/api/v1/auth/login -H "Content-Type: application/json" -d "{payload}"')
if r['rc'] == 0:
    data = json.loads(r['out'])
    print(json.dumps(data, indent=2))
else:
    print(f"ERROR: {r['err']}")

print()

# 3. Login con CONTRASEÑA INCORRECTA
print("=" * 60)
print("3. LOGIN CON CONTRASENA INCORRECTA")
print("=" * 60)
payload_wrong = json.dumps({"nifPasaporte": "12345678Z", "password": "wrongpass"})
r = curl(f'curl -s --max-time 5 -X POST http://127.0.0.1:8001/api/v1/auth/login -H "Content-Type: application/json" -d "{payload_wrong}"')
if r['rc'] == 0:
    print(f"Response: {r['out']}")
else:
    print(f"Error: {r['err']}")

print()

# 4. Login con usuario NO existente
print("=" * 60)
print("4. LOGIN CON USUARIO NO EXISTENTE")
print("=" * 60)
payload_nouser = json.dumps({"nifPasaporte": "99999999Z", "password": "AnyPass123"})
r = curl(f'curl -s --max-time 5 -X POST http://127.0.0.1:8001/api/v1/auth/login -H "Content-Type: application/json" -d "{payload_nouser}"')
if r['rc'] == 0:
    print(f"Response: {r['out']}")

print()

# 5. MFA (sin session previa, debera dar error)
print("=" * 60)
print("5. MFA VERIFICATION (Sin sessi\u00f3n previa)")
print("=" * 60)
mfa_payload = json.dumps({"nifPasaporte": "12345678Z", "codigoMFA": "654321"})
r = curl(f'curl -s --max-time 5 -X POST http://127.0.0.1:8001/api/v1/auth/mfa-verify -H "Content-Type: application/json" -d "{mfa_payload}"')
if r['rc'] == 0:
    print(f"Response: {r['out']}")

print()
print("Done.")
