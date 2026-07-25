"""FastAPI auth service for ExamenesULM - login + MFA against SQL Server."""

from __future__ import annotations



import hashlib

import json as _jsonlib

import logging
logging.basicConfig(level=logging.INFO)


import re as _re

import secrets

from datetime import datetime, timedelta, timezone

import pymssql

from fastapi import FastAPI, HTTPException, Request

from fastapi.exception_handlers import request_validation_exception_handler as _orig_val_exc_handler

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import JSONResponse

from fastapi.exceptions import RequestValidationError

from pydantic import BaseModel, ValidationError

# ============================================================

# Servicio de email (import lazy para no bloquear si hay errores SMTP)

# ============================================================

_email_svc = None

try:

    from . import email_service as _email_svc  # type: ignore[import]

except ImportError:

    print("[EMAIL IMPORT] relative import failed, trying absolute...")

    try:

        import email_service as _email_svc  # type: ignore[misc]

    except ImportError:

        print("[EMAIL IMPORT] email_service not found in current directory")

except Exception as _exc:

    print(f"[EMAIL IMPORT] ERROR no-cogido ({type(_exc).__name__}): {_exc}")



# ============================================================

# Lectura automática del .env para que nunca falten las variables de entorno (SMTP, etc.)

# ============================================================

def _cargar_env() -> None:
    import os as _os
    current_dir = _os.path.dirname(_os.path.abspath(__file__))  # backend/app/
    env_file = _os.path.join(current_dir, '.env')              # backend/app/.env
    if not _os.path.exists(env_file):
        return

    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                if not _os.getenv(k):
                    _os.environ[k] = v.strip('"').strip("'")


_cargar_env()





class LoginRequest(BaseModel):

    nifPasaporte: str

    password: str





class LoginResponse(BaseModel):

    exitoso: bool

    requiereMFA: bool = False

    mensaje: str | None = None

    tokenTemporal: str | None = None

    jwtToken: str | None = None





class VerifyMFARequest(BaseModel):

    nifPasaporte: str

    codigoMFA: str





# Credenciales desde variables de entorno (cargadas por _cargar_env())

import os

# Defaults para que el servidor arranque aunque no se cargue el .env
_DB = {
    "DB_SERVER": "localhost",
    "DB_PORT": "1433",
    "DB_USER": "sa",
    "DB_PASSWORD": "TuPasswordSeguro123!",
    "DB_NAME": "tfm_base_de_datos",
}

DB_SERVER  = os.getenv("DB_SERVER", _DB["DB_SERVER"])
DB_PORT    = int(os.getenv("DB_PORT", _DB["DB_PORT"]))
DB_USER    = os.getenv("DB_USER", _DB["DB_USER"])
DB_PASSWORD=os.getenv("DB_PASSWORD", _DB["DB_PASSWORD"])
DB_NAME    = os.getenv("DB_NAME", _DB["DB_NAME"])






def _get_db() -> pymssql.Connection:

    return pymssql.connect(

        server=DB_SERVER, port=DB_PORT, user=DB_USER,

        password=DB_PASSWORD, database=DB_NAME, autocommit=True,

    )





def _hash_password(pw: str) -> bytes:

    """SHA-256(password) — sin salt."""

    return hashlib.sha256(pw.encode()).digest()





def buscar_alumno(nif_pasaporte: str) -> dict | None:

    """Buscar alumno en BD. Returns id, nombre, password_hash (bytes), activo, correo_electronico."""

    conn = _get_db()

    try:

        curs = conn.cursor()

        curs.execute(

            "SELECT Id, Nombre, PasswordHash, Activo, email "

            "FROM dbo.Alumno WHERE NifPasaporte = %s AND Activo = 1",

            (nif_pasaporte,),

        )

        row = curs.fetchone()

        if not row:

            return None



        # Convert PasswordHash to bytes regardless of DB storage type

        raw_hash = row[2]

        if isinstance(raw_hash, str):

            password_hash_bytes = bytes.fromhex(raw_hash)

        else:

            password_hash_bytes = bytes(raw_hash)



        return {

            "id": int(row[0]),

            "nombre": str(row[1]) or "",

            "password_hash": password_hash_bytes,

            "activo": bool(row[3]),

            "correo_electronico": row[4],  # puede ser None si no configurado (columna 'email')

        }

    finally:

        conn.close()





# Mock exam list (sustituir por consulta real de dbo.examenes)

_EXAMS = [

    {

        "sessionId": "exam-001", "estado": 0, "codModulo": "010",

        "moduloDescricao": "Air Law",

        "titulo": "Examen de Ley Aerea (modulo 010)", "nTest": 80,

        "tTestSegundos": 5400, "fechaExamen": "2026-07-15T09:00:00Z",

    },

    {

        "sessionId": "exam-002", "estado": 1, "codModulo": "030",

        "moduloDescricao": "Perflight",

        "titulo": "Examen de Perflight (modulo 030)", "nTest": 45,

        "tTestSegundos": 3600, "fechaExamen": "2026-07-16T10:00:00Z",

    },

    {

        "sessionId": "exam-003", "estado": 2, "codModulo": "050",

        "moduloDescricao": "RACES",

        "titulo": "Examen de RACES (modulo 050)", "nTest": 90,

        "tTestSegundos": 7200, "fechaExamen": "2026-07-14T08:30:00Z",

    },

]





# In-memory MFA sessions (persistence real en prod con Redis)

_sessions: dict = {}  # mfa_key -> {nif, user_record, temp_token, expires_at}





def _b64url(data: bytes) -> str:

    import base64 as _b64

    return _b64.urlsafe_b64encode(data).rstrip(b"=").decode()





def _create_jwt(nif: str, nombre: str) -> str:

    hdr = _b64url(_jsonlib.dumps({"alg": "HS256", "typ": "JWT"}).encode())

    now = datetime.now(timezone.utc)

    payload = _jsonlib.dumps({

        "sub": nif, "nombre": nombre,

        "iat": int(now.timestamp()),

        "exp": int((now + timedelta(hours=2)).timestamp()),

    })

    sig_secret = "exam_salt_2026_static"

    sig_hash = hashlib.sha256(("sig=" + sig_secret).encode()).hexdigest()[:32]

    return f"{hdr}.{payload}.{sig_hash}"





app = FastAPI(title="ExamenesULM Auth Service", version="0.2.0")





@app.exception_handler(RequestValidationError)

async def validation_exception_handler(request: Request, exc: RequestValidationError):

    """Catch FastAPI RequestValidationError and write EXACT failing fields to stdout so uvicorn displays them."""

    # 1) Leer el JSON crudo para ver qué envió el cliente

    raw_body = await request.body()

    client_payload = "<no body>"

    try:

        import json as _j

        import sys

        client_payload = _j.dumps(raw_body.decode(), ensure_ascii=False, default=str)

    except Exception:

        pass



    # 2) Extraer errores detallados

    error_msgs = []

    for e in exc.errors():

        loc = " -> ".join(str(l) for l in e.get("loc", ()))

        msg = e.get("msg", str(e))

        typ = e.get("type", "")

        inp_val = e.get("input")

        error_msgs.append(f"  [{typ}] {loc}: {msg}")

        if inp_val is not None:

            import traceback

            error_msgs.append(f"         input={inp_val!r}")



    # 3) Escribir traza completa a stdout — uvicorn muestra stdout en consola siempre

    sep = "=" * 70

    sys.stdout.write(f"\n{sep}\n")

    sys.stdout.write(f"[422] ⛔ UNPROCESSABLE ENTITY\n")

    for line in str(exc).splitlines():

        sys.stdout.write(f"  [val-error] {line}\n")

    for emsg in error_msgs:

        sys.stdout.write(f"{sep}\n[detail] {emsg}\n")

    sys.stdout.write(f"\n📦 Payload recibido del frontend (raw):\n{client_payload}\n{sep}\n\n")

    sys.stdout.flush()

    sys.stderr.write(f"[422-FATAL] Validation failed for {request.method} {request.url.path}\n")

    sys.stderr.write(f"[422-FATAL] Errors: {exc.errors()}\n")

    sys.stderr.write(f"{sep}\n\n")

    sys.stderr.flush()



    return JSONResponse(

        status_code=422,

        content={

            "detail": exc.errors(),

            "_validation_errors_full_trace": error_msgs,

            "_client_raw_body": client_payload,

        },

    )





@app.exception_handler(HTTPException)

async def http_exception_logger(request: Request, exc: HTTPException):

    """Log every HTTPException (incl. 400/401/404) so we see route-level errors in uvicorn."""

    logging.getLogger("APP.HTTP").error(

        "⚠️ HTTP %d | %s %s — %s",

        exc.status_code, request.method, request.url.path, exc.detail,

    )

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})





app.add_middleware(

    CORSMiddleware,

    allow_origins=[
        "https://tfm-frontend-z8zg.onrender.com",  # <--  frontend en Render
        "http://localhost:3000",  # desarrollo local (opcional)
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)





@app.get("/api/v1/auth/health")

async def health():

    return {"status": "ok"}





# ====================================================================

# POST /api/v1/auth/login (paso 1: credenciales)

# ====================================================================



@app.post("/api/v1/auth/login", response_model=LoginResponse)

async def login(payload: LoginRequest) -> LoginResponse:

    import traceback as _traceback  # noqa: F401

    nif = payload.nifPasaporte.strip().upper()

    pw = payload.password



    print(f"[TRACE LOGIN] >>> entró route — nif={nif} password={pw!r}")



    user_record = buscar_alumno(nif)

    if not user_record:

        print(f"[TRACE LOGIN] ✗ usuario NO encontrado en BD para NIF={nif}")

        raise HTTPException(status_code=401, detail="Credenciales incorrectas")



    print(f"[TRACE LOGIN] ✓ usuario encontrado: id={user_record['id']} nombre={user_record['nombre']} hash_db_len={len(user_record['password_hash'])}")



    expected_hash = _hash_password(pw)

    pw_match = expected_hash == user_record["password_hash"]

    print(f"[TRACE LOGIN] hash_check — pw={pw!r} expected_hex={expected_hash.hex()[:32]}... db_hex={user_record['password_hash'].hex()[:32]}... coincide={pw_match}")



    if not pw_match:

        print(f"[TRACE LOGIN] ✗ PASSWORD NO coincide para {nif} (pw={pw!r})")

        raise HTTPException(status_code=401, detail="Credenciales incorrectas")



    print(f"[TRACE LOGIN] ✓ password OK → generando OTP")



    # --- Generar OTP real de 6 digitos y enviarlo al email del alumno ---

    otp_code = secrets.randbelow(1000000)

    otp_str = str(otp_code).zfill(6)



    mfa_key = f"mfa_{nif}"

    _sessions[mfa_key] = {

        "nif": nif,

        "user_record": user_record,

        "otp": otp_str,                 # nuevo campo: codigo OTP valido

        "temp_token": secrets.token_urlsafe(24),

        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),

    }

    print(f"[TRACE LOGIN] ✓ OTP generado: {otp_str}")



    # Enviar email con el OTP

    correo = user_record.get("correo_electronico")

    print(f"[TRACE LOGIN] → correo_electronico={correo!r} type={type(correo).__name__} _email_svc={'None' if _email_svc is None else 'LOADED'}")



    if correo and _email_svc is not None:

        try:

            enviado = _email_svc.enviar_otp_a(correo, otp_str)

            print(f"[TRACE LOGIN] ✓ email_service.enviar_otp_a devolvió={enviado}")

            if not enviado:

                logging.warning("[login] No se pudo enviar email MFA a %s", correo)

        except Exception:

            tb = _traceback.format_exc()

            print(f"[TRACE LOGIN] ✗ EXCEPCION al enviar email:{tb}")

            logging.exception("[login] Error al enviar email MFA a %s", correo)

    else:

        if not correo:

            logging.info(

                "[login] OTP generado para %s pero no hay correo_electronico (%s). "

                "El usuario vera el codigo en la demo.", nif, repr(correo)

            )

            print(f"[TRACE LOGIN] → sin correo — skipping email (valor={correo!r})")

        if _email_svc is None:

            logging.info(

                "[login] OTP generado para %s pero _email_svc es None. "

                "servicio de email no disponible.", nif

            )

            print(f"[TRACE LOGIN] → _email_svc es None — skipping envio")



    if correo is None or correo.strip() == "":

        return LoginResponse(

            exitoso=True, requiereMFA=False,   # sin email → pasamos directo al examen

            jwtToken=_create_jwt(nif, user_record["nombre"]),

            tokenTemporal=None,

            mensaje="Usuario activado correctamente (email no configurado, se omite MFA).",

        )



    return LoginResponse(

        exitoso=True, requiereMFA=True,

        tokenTemporal=_sessions[mfa_key]["temp_token"],

        jwtToken=None,

        mensaje=f"Se ha enviado un codigo de verificacion a {correo}. Válido por 5 minutos.",

    )





# ====================================================================

# POST /api/v1/auth/mfa-verify (paso 2: codigo OTP)

# ====================================================================



@app.post("/api/v1/auth/mfa-verify", response_model=LoginResponse)

async def verify_mfa(payload: VerifyMFARequest) -> LoginResponse:

    nif = payload.nifPasaporte.strip().upper()

    codigo = payload.codigoMFA.strip()



    mfa_key = f"mfa_{nif}"

    session = _sessions.get(mfa_key)



    if not session:

        raise HTTPException(status_code=401, detail="Ninguna sesion MFA activa encontrada.")



    if datetime.now(timezone.utc) > session["expires_at"]:

        del _sessions[mfa_key]

        raise HTTPException(status_code=401, detail="Sesion MFA expirada (5 minutos). Vuelve a hacer login.")



    if not codigo.isdigit() or len(codigo) != 6:

        raise HTTPException(

            status_code=400,

            detail="El codigo MFA debe ser de 6 digitos numericos.",

        )



    # --- Validar OTP real almacenado en la sesión ---

    stored_otp = session.get("otp")

    if stored_otp and codigo != stored_otp:

        logging.warning("[mfa-verify] OTP incorrecto para %s", nif)

        raise HTTPException(status_code=401, detail="Codigo de verificacion incorrecto.")



    user_record = session.get("user_record")

    if not user_record:

        raise HTTPException(status_code=401, detail="Usuario no encontrado en sesion activa")



    del _sessions[mfa_key]



    return LoginResponse(

        exitoso=True, requiereMFA=False,

        jwtToken=_create_jwt(nif, user_record["nombre"]),

        tokenTemporal=None,

        mensaje="Autenticacion completada correctamente.",

    )





# ====================================================================

# GET /api/v1/examenes

# ====================================================================



# Mapa persistente session_id → id de BD (se llena al inicializar el app)

_session_id_to_dbid: dict[str, int] = {}





def _build_session_id(alumno_id: int, cod_modulo: str, examen_id: int) -> str:

    """Generar un session_id único y reproducible para cada examen."""

    import hashlib as _hashlib

    raw = f"exam-{alumno_id}-{cod_modulo}-{examen_id}"

    return "es-" + _hashlib.md5(raw.encode()).hexdigest()[:8].upper()





def _seed_session_ids():

    """Llenar session_id_to_dbid mirando los exámenes sin session_id en la BD."""

    conn = _get_db()

    try:

        curs = conn.cursor()

        # Verificar si ya existe la columna session_id

        curs.execute(

            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS "

            "WHERE TABLE_NAME='examenes' AND COLUMN_NAME='session_id'"

        )

        has_col = curs.fetchone()[0]

        if not has_col:

            # Crear columna

            try:

                curs.execute("ALTER TABLE dbo.examenes ADD session_id nvarchar(50) NULL")

                conn.commit()

            except Exception:

                pass

                has_col = True



        # Recorrer exámenes y generar session_id donde falta

        curs.execute("SELECT id, alumno_id, cod_modulo FROM dbo.examenes ORDER BY id")

        for row in curs.fetchall():

            eid = int(row[0])

            aid = int(row[1])

            cm = str(row[2]) or ""

            sid = _build_session_id(aid, cm, eid)

            if not has_col:

                try:

                    curs.execute("UPDATE dbo.examenes SET session_id = %s WHERE id = %s", (sid, eid))

                except Exception:

                    pass

            else:

                # Verificar si ya tienen session_id o actualizar a consistente

                curs.execute(

                    "SELECT TOP 1 session_id FROM dbo.examenes WHERE id = %s", (eid,)

                )

                existing = curs.fetchone()

                raw_sid = existing[0] if existing else None

                # '' (vacía) y None → ambos se reinterpretan como "sin session_id"

                has_sid = raw_sid.strip() if isinstance(raw_sid, str) and raw_sid != '' else None

                if not has_sid or has_sid != sid:

                    try:

                        curs.execute(

                            "UPDATE dbo.examenes SET session_id = %s WHERE id = %s", (sid, eid)

                        )

                    except Exception:

                        pass



            _session_id_to_dbid[sid] = eid

    finally:

        conn.close()





# Ejecutar seed al cargar el módulo

_seed_session_ids()





# Mapping cod_modulo → descripción legible (no hay tabla de módulos en BD)

_MODULO_MAP: dict[str, str] = {

    "010": "Air Law",

    "020": "Operaciones de Cabina",

    "030": "Perflight",

    "040": "Comunicaciones",

    "050": "RACES",

    "060": "Operacional FAA",

    "070": "Navegación",

    "080": "Regulación",

    "090": "Previsión meteorológica",

    "100": "Factores humanos",

}





def _mod_desc(cod: str) -> str:

    return _MODULO_MAP.get(cod.strip(), f"Módulo {cod}")





@app.get("/api/v1/examenes")

async def list_examenes(

    alumno_id: int | None = None,

    nif_pasaporte: str | None = None,

):

    """Devolver exámenes de la BD. Filtra por alumno_id o nif_pasaporte (se mutúan con Alumno)."""

    conn = _get_db()

    try:

        curs = conn.cursor()



        # Si viene nif → buscar alumno_id primero

        target_id: int | None = alumno_id

        if nif_pasaporte and not alumno_id:

            curs.execute(

                "SELECT Id FROM dbo.Alumno WHERE NifPasaporte = %s AND Activo = 1",

                (nif_pasaporte.strip().upper(),),

            )

            row = curs.fetchone()

            target_id = int(row[0]) if row else None



        if target_id is not None:

            sql = (

                "SELECT id, alumno_id, estado, cod_modulo, "

                "n_test, "

                "t_test_segundos, fecha_examen, porc_apto_test, session_id "

                "FROM dbo.examenes WHERE alumno_id = %s ORDER BY id"

            )

            curs.execute(sql, (target_id,))

        else:

            sql = (

                "SELECT id, alumno_id, estado, cod_modulo, "

                "n_test, "

                "t_test_segundos, fecha_examen, porc_apto_test, session_id "

                "FROM dbo.examenes ORDER BY id"

            )

            curs.execute(sql)



        rows = curs.fetchall()



        result = []

        for row in rows:

            examen_id = int(row[0])

            alumno_id_val = int(row[1])

            estado_val = int(row[2])

            cod_mod = str(row[3]) or ""

            # Guardias: None, '', ' ', 0 → todos se tratan como "sin session_id"

            raw_sid = row[8] if row[8] is not None else ""

            clean_sid = str(raw_sid).strip()

            if clean_sid:

                sid = clean_sid

            elif examen_id in _session_id_to_dbid:  # int keys → fallback

                sid = _session_id_to_dbid[examen_id]

            else:

                # Generar session_id en caliente si falta en DB y el seed ya pasó

                sid = _build_session_id(

                    alumno_id=alumno_id_val, cod_modulo=cod_mod, examen_id=examen_id

                )



            result.append({

                "sessionId": sid,

                "estado": estado_val,

                "codModulo": cod_mod,

                "moduloDescricao": f"{_mod_desc(cod_mod)} ({cod_mod})",

                "titulo": f"Examen {_mod_desc(cod_mod).title()} (módulo {cod_mod})",

                "nTest": row[4] if row[4] is not None else 30,

                "tTestSegundos": int(row[5]) if row[5] is not None else 3600,

                "fechaExamen": str(row[6]) if row[6] else None,

                "porcApto": float(row[7]) if row[7] is not None else 75.0,

            })



        return {"examenes": result}

    finally:

        conn.close()





# ====================================================================

# POST /api/v1/examenes/finalizar (B1 -- persistencia en BD)

# ====================================================================



from pydantic import BaseModel as ModelBase





class RespuestaPregunta(ModelBase):

    numero: int

    respuesta: str = ""

    impugnacion: str | None = None





class FinalizarRequest(ModelBase):

    """Schema que recibe el frontend al finalizar un examen."""

    examId: str

    sessionID: str

    nifPasaporte: str

    respuestas: list[RespuestaPregunta]

    tiempoRestante: int

    totalTiempo: int = 0





def _buscar_alumno_por_nif(nif_pasaporte: str) -> dict | None:

    """Buscar alumno por NIF y devolver {id, nombre, activo}."""

    conn = _get_db()

    try:

        curs = conn.cursor()

        curs.execute(

            "SELECT Id, Nombre, Activo "

            "FROM dbo.Alumno WHERE NifPasaporte = %s AND Activo = 1",

            (nif_pasaporte,),

        )

        row = curs.fetchone()

        if not row:

            return None

        return {

            "id": int(row[0]),

            "nombre": str(row[1]) or "",

            "activo": bool(row[2]),

        }

    finally:

        conn.close()





logger = logging.getLogger(__name__)

log = logger.info  # alias corto para llamadas rápidas





def _obtener_examen_int_id_por_session(session_id: str) -> int | None:

    """Buscar el id bigint en dbo.examenes dado un examId del frontend.



    El frontend envía session_id (ej. 'es-A4C1049E' o 'exam-001') que corresponde

    a la columna session_id de dbo.examenes, no al campo id (bigint).

    """

    log("[ex_id] Buscando examen por session_id=%s", session_id)

    conn = _get_db()

    try:

        curs = conn.cursor()



        # Metodo 1: mapeo in-memory (_session_id_to_dbid se llena en _seed_session_ids)

        if session_id in _session_id_to_dbid:

            found_id = _session_id_to_dbid[session_id]

            log("[ex_id] ✅ Encontrado via mapeo: id=%d", found_id)

            return found_id



        # Metodo 2: busqueda directa por columna session_id en BD

        sql = "SELECT TOP 1 id FROM dbo.examenes WHERE session_id = %s"

        curs.execute(sql, (session_id,))

        row = curs.fetchone()

        if row:

            found_id = int(row[0])

            log("[ex_id] ✅ Encontrado por columnas session_id: id=%d", found_id)

            # actualizar mapeo in-memory para futuras búsquedas mas rápidas

            _session_id_to_dbid[session_id] = found_id

            return found_id



        # Metodo 3: fallback — si el string tiene formato 'exam-N', usar N directamente id

        if session_id.startswith("exam-"):

            try:

                candidate = int(session_id.split("-")[-1])

                curs.execute("SELECT TOP 1 id FROM dbo.examenes WHERE id = %s", (candidate,))

                row2 = curs.fetchone()

                if row2:

                    found_id = int(row2[0])

                    log("[ex_id] ✅ Encontrado por fallback 'exam-N' → examen_N: id=%d", found_id)

                    _session_id_to_dbid[session_id] = found_id

                    return found_id

            except (ValueError, TypeError):

                pass



        log("[ex_id] ❌ NO encontrado para session_id=%s", session_id)

        return None

    finally:

        conn.close()





def _obtener_examen_info_por_id(examen_int_id: int) -> dict | None:

    """Devolver info del examen relevante para puntuación."""

    conn = _get_db()

    try:

        curs = conn.cursor()

        curs.execute(

            "SELECT alumno_id, cod_modulo, n_test, t_test_segundos, estado, idioma, porc_apto_test "

            "FROM dbo.examenes WHERE id = %s",

            (examen_int_id,),

        )

        row = curs.fetchone()

        if not row:

            return None

        return {

            "alumno_id": int(row[0]),

            "cod_modulo": str(row[1]) or "",

            "n_test": int(row[2]),

            "t_test_segundos": int(row[3]),

            "estado": int(row[4]),

            "idioma": int(row[5]),

            "porc_apto_test": float(row[6] if row[6] is not None else 75.0),

        }

    finally:

        conn.close()





def _calcular_y_guardar_resultado(

    examen_int_id: int,

    exam_info: dict,

    respuestas: list[dict],

    tiempo_restante: int,

    total_tiempo: int,

    alumno_id: int,

    session_id: str,

) -> dict:

    """Calcular correctas/fallos/no-contestadas y guardar en resultados_examen.



    Compara las respuestas del alumno con las correctas almacenadas en

    dbo.preguntas_banco.respuesta_correcta_modulos (JSON array de letras 'A','B','C','D').

    """

    conn = _get_db()

    try:

        curs = conn.cursor()



        n_total = len(respuestas) if respuestas else 0



        # Dict por orden_pregunta (coincide con ep.orden): la respuesta del alumno se empareja por posición en el examen

        respuestas_alumno = {}

        for r in respuestas:

            # El frontend envía {"numero": X, "respuesta": Y}  —  NO tiene campo 'banco_id'

            orden_clave = r.get("numero") or r.get("orden") or r.get("banco_id")

            if orden_clave is not None:

                respuestas_alumno[int(orden_clave)] = str(r.get("respuesta", "")).strip().upper()



        # Obtener las preguntas SELECCIONADAS en examen_preguntas para este examen (con su correcta)

        curs.execute(

            "SELECT ep.orden, pb.id, CAST(pb.respuesta_correcta_modulos AS VARCHAR(200)) "

            "FROM dbo.examen_preguntas ep "

            "JOIN dbo.preguntas_banco pb ON ep.pregunta_banco_id = pb.id "

            "WHERE ep.examen_id = %s ORDER BY ep.orden",

            (examen_int_id,),

        )

        seleccionado = curs.fetchall()



        correcta_list = []

        fallo_list = []

        nocontestada_list = []



        for row in seleccionado:

            orden_pregunta = int(row[0])

            banco_id = int(row[1])

            respuesta_correcta_json = str(row[2]) if row[2] is not None else "[]"



            if not isinstance(respuesta_correcta_json, str):

                continue



            try:

                opciones_correctas = _jsonlib.loads(respuesta_correcta_json)

            except (_jsonlib.JSONDecodeError, TypeError):

                continue



            # Asegurar que es lista de letras mayúsculas

            if isinstance(opciones_correctas, list):

                opciones_correctas = [str(o).upper() for o in opciones_correctas]

            else:

                opciones_correctas = [str(opciones_correctas).upper()]



            # Buscar la respuesta del alumno por orden (posición en el examen), NO por banco_id

            resp_alumno = respuestas_alumno.get(orden_pregunta, "")



            if not resp_alumno:

                nocontestada_list.append(orden_pregunta)

                continue



            if resp_alumno in opciones_correctas:

                correcta_list.append(orden_pregunta)

            else:

                fallo_list.append(orden_pregunta)



        correctas = len(correcta_list)

        fallos = len(fallo_list)

        no_contestadas = len(nocontestada_list)



        porc_acierto = round((correctas / max(n_total, 1)) * 100, 2) if n_total > 0 else 0.0



        es_apto = porc_acierto >= exam_info["porc_apto_test"]

        nota_final = round(porc_acierto, 2) if porc_acierto > 0 else None



        mensaje = "APTO" if es_apto else "NO APTO"



        # ── Guardar respuestas JSON del alumno (para auditoría) ──

        resp_json_str = _jsonlib.dumps(respuestas, ensure_ascii=False)



        # ── UPSERT resultados_examen (INSERT ON CONFLICT o via OUTPUT) ──

        # Como SQL Server no tiene ON CONFLICT, usamos OUTPUT deleted.examen_id

        # para detectar si el MERGE insertó vs actualizó. Pero como pymssql exige autocommit=True

        # y el MERGE con USING (1) AS src no genera columnas reales, lo resolvemos aquí:

        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")



        try:

            # Intentar UPDATE primero

            curs.execute(

                "UPDATE dbo.resultados_examen SET "

                "correctas = %s, fallos = %s, no_contestadas = %s, "

                "porcentaje_acierto = %s, es_apto = %s, nota_final = %s, "

                "mensaje_resultado = %s, respuestas_json = %s, "

                "tiempo_restante_segundos = %s, tiempo_total_segundos = %s, "

                "alumno_id = %s "

                "WHERE examen_id = %s",

                (

                    int(correctas), int(fallos), int(no_contestadas), porc_acierto, int(es_apto),

                    nota_final, mensaje.replace("'", "''"), resp_json_str,

                    tiempo_restante, total_tiempo, alumno_id, examen_int_id,

                ),

            )



            if curs.rowcount == 0:

                # No existía → INSERT

                curs.execute(

                    "INSERT INTO dbo.resultados_examen (examen_id, alumno_id, correctas, fallos, "

                    "no_contestadas, porcentaje_acierto, es_apto, "

                    "nota_final, mensaje_resultado, fecha_calculo, respuestas_json, "

                    "tiempo_restante_segundos, tiempo_total_segundos) "

                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",

                    (

                        examen_int_id, alumno_id, int(correctas), int(fallos), int(no_contestadas),

                        porc_acierto, int(es_apto), nota_final,

                        mensaje.replace("'", "''"), now_ts, resp_json_str,

                        tiempo_restante, total_tiempo,

                    )

                )

        except Exception as upsert_err:

            # Si falla el UPDATE y luego el INSERT (conflict de PK etc.), lo reintentamos con SELECT+UPSERT

            curs.execute(

                "SELECT correctas, fallos, no_contestadas FROM dbo.resultados_examen WHERE examen_id = %s",

                (examen_int_id,),

            )

            existing_row = curs.fetchone()

            if existing_row:

                # Existe → UPDATE

                curs.execute(

                    "UPDATE dbo.resultados_examen SET "

                    "correctas = %s, fallos = %s, no_contestadas = %s, "

                    "porcentaje_acierto = %s, es_apto = %s, nota_final = %s, "

                    "mensaje_resultado = %s, respuestas_json = %s, "

                    "tiempo_restante_segundos = %s, tiempo_total_segundos = %s, "

                    "alumno_id = %s "

                    "WHERE examen_id = %s",

                    (

                        int(correctas), int(fallos), int(no_contestadas), porc_acierto, int(es_apto),

                        nota_final, mensaje.replace("'", "''"), resp_json_str,

                        tiempo_restante, total_tiempo, alumno_id, examen_int_id,

                    ),

                )

            else:

                # No existe → INSERT

                curs.execute(

                    "INSERT INTO dbo.resultados_examen (examen_id, alumno_id, correctas, fallos, "

                    "no_contestadas, porcentaje_acierto, es_apto, "

                    "nota_final, mensaje_resultado, fecha_calculo, respuestas_json, "

                    "tiempo_restante_segundos, tiempo_total_segundos) "

                    "VALUES (%s, %s, %s, %s, %s, %s, %s, 0, %s, %s, %s, %s, %s, %s)",

                    (

                        examen_int_id, alumno_id, int(correctas), int(fallos), int(no_contestadas),

                        porc_acierto, int(es_apto), nota_final,

                        mensaje.replace("'", "''"), now_ts, resp_json_str,

                        tiempo_restante, total_tiempo,

                    ),

                )



        # Actualizar examen: marcar como FINALIZADO y guardar respuestas JSON

        time_hora = None

        if exam_info["t_test_segundos"] and tiempo_restante > 0:

            h = max(0, int(tiempo_restante / 3600))

            m = max(0, int((tiempo_restante % 3600) / 60))

            s = max(0, int(tiempo_restante % 60))

            time_hora = f"{h:02d}:{m:02d}:{s:02d}"



        curs.execute(

            "UPDATE dbo.examenes SET estado = 3, fecha_finalizada = sysutcdatetime() "

            "WHERE id = %s",

            (examen_int_id,),

        )

        # Guardar respuestas como JSON en columna existente de examenes si está disponible

        try:

            curs.execute(

                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='examenes' AND COLUMN_NAME IN ('respuestas_test','tmp_respuestas') ORDER BY ORDINAL_POSITION",

            )

            cols = [r[0] for r in curs.fetchall()]

            if "respuestas_test" in cols:

                target_col = "respuestas_test"

            elif "tmp_respuestas" in cols:

                target_col = "tmp_respuestas"

            else:

                target_col = None



            if target_col:

                curs.execute(

                    f"UPDATE dbo.examenes SET {target_col} = %s WHERE id = %s",

                    (resp_json_str, examen_int_id),

                )

        except Exception:

            pass  # Ignorar si la columna no existe en esta variante de esquema



        return {

            "correctas": correctas,

            "fallos": fallos,

            "no_contestadas": no_contestadas,

            "porcentaje_acierto": porc_acierto,

            "es_apto": es_apto,

            "nota_final": nota_final if nota_final is not None else 0.0,

        }



    finally:

        conn.close()





@app.post("/api/v1/examenes/finalizar")

async def finalizar_examen(payload: FinalizarRequest):

    """Finalizar un examen y guardar los datos en la tabla resultados_examen (BD)."""

    log("[finalizar] ← POST recibido: examId=%s sessionID=%s nif=%s respuestas=%d tiempoRestante=%d",

        payload.examId, payload.sessionID, payload.nifPasaporte, len(payload.respuestas), payload.tiempoRestante)

    try:

        # Paso 1: Buscar al alumno por NIF

        alumno = _buscar_alumno_por_nif(payload.nifPasaporte)

        if not alumno:

            log("[finalizar] ❌ Alumno no encontrado para NIF=%s", payload.nifPasaporte)

            raise HTTPException(

                status_code=404,

                detail=f"Alumno con NIF '{payload.nifPasaporte}' no encontrado",

            )

        log("[finalizar] ✅ Alumno encontrado: id=%d nombre=%s", alumno["id"], alumno["nombre"])



        # Paso 2: Buscar el examen por examId en BD (directamente por id bigint)

        examen_int_id = _obtener_examen_int_id_por_session(payload.examId)

        if not examen_int_id:

            log("[finalizar] ❌ Examen NO encontrado para examId=%s", payload.examId)

            raise HTTPException(

                status_code=404,

                detail=f"No se encontró el examen en BD (examId={payload.examId})",

            )

        log("[finalizar] ✅ Examen interno id=%d", examen_int_id)



        # Paso 3: Obtener info del examen para scoring

        exam_info = _obtener_examen_info_por_id(examen_int_id)

        if not exam_info:

            log("[finalizar] ❌ Info del examen no disponible para id=%d", examen_int_id)

            raise HTTPException(

                status_code=404,

                detail=f"Examen id={examen_int_id} no encontrado en BD",

            )

        log("[finalizar] ✅ Info: modulo=%s n_test=%d porc_apto=%f%%",

            exam_info["cod_modulo"], exam_info["n_test"], exam_info["porc_apto_test"])



        # Paso 4: Convertir respuestas al formato dict

        respuestas_dict = [r.model_dump() for r in payload.respuestas]



        # Paso 5: Calcular y guardar el resultado en la BD

        log("[finalizar] → Calculando scoring...")

        resultados = _calcular_y_guardar_resultado(

            examen_int_id=examen_int_id,

            exam_info=exam_info,

            respuestas=respuestas_dict,

            tiempo_restante=payload.tiempoRestante,

            total_tiempo=payload.totalTiempo or exam_info["t_test_segundos"],

            alumno_id=alumno["id"],  # FK ← alumnos.Activo = int(id) del alumno

            session_id=payload.sessionID,  # session string para consultar examen_preguntas

        )

        log("[finalizar] ✅ Scoring OK: correctas=%d fallos=%d no_contestadas=%d porc=%f%% apto=%s nota=%.2f",

            resultados["correctas"], resultados["fallos"], resultados["no_contestadas"],

            resultados["porcentaje_acierto"], resultados["es_apto"], resultados["nota_final"])



        return {

            "exitoso": True,

            "mensaje": "Examen finalizado y almacenado correctamente en BD.",

            "resultados": resultados,

            "examId": examen_int_id,  # DB integer para fetch de resultados

        }



    except HTTPException:

        raise

    except Exception as exc:

        import traceback

        traceback.print_exc()

        raise HTTPException(

            status_code=500,

            detail=f"Error al procesar el examen: {str(exc)}",

        )





# ====================================================================

# GET /api/v1/resultados/{examen_id} -- Fase 1: obtener resultados de BD

# ====================================================================





def _obtener_resultado_por_examen(examen_id: int) -> dict | None:

    """Leer una fila de dbo.resultados_examen por examen_id.



    Devuelve un dict con la forma compatible con ResultadoResponse, o None si no existe.

    """

    conn = _get_db()

    try:

        curs = conn.cursor()

        curs.execute(

            "SELECT id, examen_id, correctas, fallos, no_contestadas,"

            " porcentaje_acierto, es_apto,"

            " nota_final, mensaje_resultado, fecha_calculo, respuestas_json,"

            " tiempo_restante_segundos, tiempo_total_segundos,"

            " alumno_id"

            " FROM dbo.resultados_examen WHERE examen_id = %s",

            (examen_id,),

        )

        row = curs.fetchone()

        if not row:

            return None



        # Convertir tipos de SQL Server a Python seguros

        valores = {

            "id": int(row[0]),       # id (PK)

            "examen_id": int(row[1]),   # exam_id (FK)

            "correctas": int(row[2]),

            "fallos": int(row[3]),

            "no_contestadas": int(row[4]),

        }



        raw_pct = row[5]

        valores["porcentaje_acierto"] = float(raw_pct) if raw_pct is not None else 0.0



        es_apto_raw = row[6]

        valores["es_apto"] = bool(es_apto_raw) if es_apto_raw is not None else False



        raw_nota = row[7]

        valores["nota_final"] = float(raw_nota) if raw_nota is not None else None



        valores["mensaje_resultado"] = (str(row[8]) or "Sin resultado").strip()

        valores["fecha_calculo"] = row[9].isoformat() if row[9] else ""



        raw_respuestas = row[10]

        valores["respuestas_json"] = str(raw_respuestas) if raw_respuestas is not None else None



        raw_tiempo_rest = row[11]

        valores["tiempo_restante_segundos"] = int(raw_tiempo_rest) if raw_tiempo_rest is not None else None



        raw_total_tiempo = row[12]

        valores["tiempo_total_segundos"] = int(raw_total_tiempo) if raw_total_tiempo is not None else None



        raw_alumno = row[13]

        valores["alumno_id"] = int(raw_alumno) if raw_alumno is not None else None



        # Corregir nombres de campos al snake_case que espera frontend

        return {

            "id": valores["id"],

            "examen_id": valores["examen_id"],

            "correctas": valores["correctas"],

            "fallos": valores["fallos"],

            "no_contestadas": valores["no_contestadas"],

            "porcentaje_acierto": valores["porcentaje_acierto"],

            "es_apto": valores["es_apto"],

            "nota_final": valores["nota_final"],

            "mensaje_resultado": valores["mensaje_resultado"],

            "fecha_calculo": valores["fecha_calculo"],

            "tiempo_restante_segundos": valores["tiempo_restante_segundos"],

            "tiempo_total_segundos": valores["tiempo_total_segundos"],

            "alumno_id": valores["alumno_id"],

        }



    finally:

        conn.close()







try:

    from .schemas import ResultadoResponse

except ImportError:

    from schemas import ResultadoResponse





# ====================================================================

# POST /api/v1/examenes/{examId}/generar  — Selecciona preguntas al azar + INSERT en examen_preguntas

# GET  /api/v1/examenes/{examId}/preguntas — Devuelve las preguntas ya generadas del examen

# ====================================================================





@app.post("/api/v1/examenes/{exam_id}/generar")

async def generar_examen_preguntas(exam_id: str):

    """Seleccionar preguntas aleatorias de preguntas_banco para un examen

    e insertarlas en examen_preguntas (una fila por número en el examen generado).



    La tabla examen_preguntas tiene columnas: id, examen_id, pregunta_banco_id,

    cod_modulo, orden, resp_correcta, resp_alumno, acerto.

    """

    log("generar ← exam_id=%r (tipo=%s)", exam_id, type(exam_id).__name__)

    conn = _get_db()

    try:

        curs = conn.cursor()



        # ── LOG TRACING: estructura de la tabla de destino ──

        curs.execute("""

            SELECT c.name, t.name as type_name, c.is_nullable

            FROM sys.columns c

            JOIN sys.types t ON c.user_type_id = t.user_type_id

            WHERE c.object_id = (SELECT object_id FROM sys.tables WHERE name='examen_preguntas')

            ORDER BY c.column_id

        """)

        schema_cols = curs.fetchall()

        log("generar ── SCHEMA examen_preguntas:")

        for sc in schema_cols:

            nullable = "NULL" if sc[2] else "NOT NULL"

            log("generar    col=%s type=%s %s", str(sc[0]), str(sc[1]), nullable)



        # 1) Buscar el examen interno por session_id (mismo patrón que finalizar)

        ex_id_int = _obtener_examen_int_id_por_session(exam_id)

        if not ex_id_int:

            log("generar ❌ No se encontró examen para session_id=%r (tipo=%s)", exam_id, type(exam_id).__name__)

            raise HTTPException(status_code=404, detail=f"Examen '{exam_id}' no encontrado en BD.")

        log("generar ✅ examen interno id=%d  (tipo=%s, nvarchar-ok?%s)",

            ex_id_int, type(ex_id_int).__name__, isinstance(ex_id_int, int))



        # 2) Info del examen (módulo, nº de preguntas...)

        exam_info = _obtener_examen_info_por_id(ex_id_int)

        if not exam_info:

            raise HTTPException(status_code=404, detail=f"Info del examen id={ex_id_int} no encontrada.")



        log("generar    info.examen → cod_modulo=%r  n_test=%d",

            exam_info["cod_modulo"], exam_info["n_test"])



        # 3) ¿Ya existen preguntas para este examen? Si ya están generadas, omitir.

        log("generar   checking COUNT(examen_id=%r tipo=%s)", ex_id_int, type(ex_id_int).__name__)

        curs.execute(

            "SELECT COUNT(*) FROM dbo.examen_preguntas WHERE examen_id = %s",

            (ex_id_int,),

        )

        existente = curs.fetchone()[0]

        if existente and existente > 0:

            log("generar ⏩ Ya existen %d preguntas para examen %s, omitiendo.", existente, exam_id)

            return {"ok": True, "total_nuevo": 0, "msg": "preguntas ya generadas previamente"}



        # 4) Obtener TODAS las preguntas del banco de este módulo (ORDER BY NEWID() = random)

        num_preguntas = exam_info["n_test"] or 30



        curs.execute(

            "SELECT TOP %d id, texto_enunciado, respuesta_a, respuesta_b, respuesta_c, respuesta_d, "

            "CAST(respuesta_correcta_modulos AS VARCHAR(200)) AS respuesta_correcta, cod_modulo "

            "FROM dbo.preguntas_banco WHERE cod_modulo = %s ORDER BY NEWID()",

            (num_preguntas, exam_info["cod_modulo"]),

        )

        todas = curs.fetchall()



        if not todas:

            raise HTTPException(

                status_code=400,

                detail=f"No hay preguntas disponibles en el banco para el módulo {exam_info['cod_modulo']}.",

            )



        total_en_banco = len(todas)

        if num_preguntas > total_en_banco:

            raise HTTPException(

                status_code=400,

                detail=f"Se necesitan {num_preguntas} preguntas pero el banco solo tiene {total_en_banco} para este módulo.",

            )



        # 5) Insertar en examen_preguntas (examen_id bigint, pregunta_banco_id int, ...)

        #    Columnas de la tabla:

        #      id          bigint   AUTO_INCREMENT PK

        #      examen_id   bigint   NOT NULL

        #      pregunta_banco_id int    NOT NULL

        #      cod_modulo  nvarchar(20) NOT NULL

        #      orden       int        NOT NULL

        #      resp_correcta  nchar(2)   NOT NULL

        #      resp_alumno     nchar(2)   NULL (vacío al generar)

        #      acerto          bit        NOT NULL  → 0 = sin contestar todavía

        insert_sql = (

            "INSERT INTO dbo.examen_preguntas "

            "(examen_id, pregunta_banco_id, cod_modulo, orden, resp_correcta, resp_alumno, acerto) "

            "VALUES (%s, %s, %s, %s, %s, N'', 0)"

        )



        params_list = []

        for idx, row in enumerate(todas, start=1):

            banco_id = int(row[0])

            texto_enunciado = str(row[1]) if row[1] is not None else ""

            rc_raw = str(row[6]) if row[6] is not None else "[]"



            # Extraer primera letra de cada opción correcta (ej. ['A','C'] -> 'AC')

            try:

                opciones = _jsonlib.loads(rc_raw)

                if isinstance(opciones, list):

                    letras = ''.join(str(o).upper().strip()[:1] for o in opciones if str(o).upper().strip())[:2]

                else:

                    letras = str(opciones).upper().strip()[:2]

            except Exception:

                letters = _re.findall(r'[A-D]', rc_raw.upper())

                letras = ''.join(letters)[:2]



            if not letras:

                log("generar ⚠️  pregunta banco_id=%d sin respuesta correcta parseable, rc_raw=%r — uso 'N'",

                    banco_id, rc_raw)

                letras = "N"



            params_list.append((ex_id_int, banco_id, exam_info["cod_modulo"], idx, letras))



        log("generar    preparadas %d filas para INSERT", len(params_list))

        if params_list:

            log("generar    ▶ primera fila: examen_id=%r tipo=%r  banco_id=%d  modulo=%r orden=%d resp=%r",

                params_list[0][0], type(params_list[0][0]), params_list[1], params_list[2], params_list[3], params_list[4])

            log("generar    ▶ SQL INSERT columnas = examen_id(bigint)+pregunta_banco_id(int)+cod_modulo(nvarchar)+orden(int)+resp_correcta(nchar)+resp_alumno(nchar)+acerto(bit))")



        curs.executemany(insert_sql, params_list)

        conn.commit()



        log("generar ✅ generadas %d preguntas para examen=%s", len(todas), exam_id)

        return {"ok": True, "total_nuevo": len(todas)}



    except HTTPException:

        raise

    except Exception as exc:

        import traceback

        traceback.print_exc()

        raise HTTPException(status_code=500, detail=f"Error al generar el examen: {str(exc)}")

    finally:

        conn.close()





@app.get("/api/v1/examenes/{exam_id}/preguntas")

async def obtener_examen_preguntas(exam_id: str):

    """Devolver las preguntas generadas para un examen (desde examen_preguntas).



    Join con preguntas_banco para obtener el contenido completo.

    exam_id puede ser session_id o DB id; se normaliza via BD.

    """

    log("preguntas ← exam_id=%s", exam_id)

    conn = _get_db()

    try:

        curs = conn.cursor()



        # Normalizar: convertir session_id (string es-*) a examen interno bigint

        examen_int_id = _obtener_examen_int_id_por_session(exam_id)

        if not examen_int_id:

            raise HTTPException(

                status_code=404,

                detail=f"No se encontró el examen '{exam_id}' en BD.",

            )



        # Verificar que existen preguntas generadas para este examen (bigint id)

        curs.execute(

            "SELECT COUNT(*) FROM dbo.examen_preguntas WHERE examen_id = %s",

            (examen_int_id,),

        )

        count = curs.fetchone()[0]

        

        if count == 0:

            raise HTTPException(

                status_code=404,

                detail=f"No hay preguntas generadas para el examen {exam_id}. Usa POST /generar primero.",

            )



        # Join con preguntas_banco para obtener texto y opciones reales

        query = (

            "SELECT ep.orden, pb.id AS banco_id, pb.texto_enunciado, "

            "pb.respuesta_a, CAST(pb.respuesta_b AS VARCHAR(500)) AS respuesta_b, "

            "CAST(pb.respuesta_c AS VARCHAR(500)) AS respuesta_c, "

            "CAST(pb.respuesta_d AS VARCHAR(500)) AS respuesta_d, "

            "CAST(pb.respuesta_correcta_modulos AS VARCHAR(200)) AS respuesta_correcta, "

            "pb.url_fichero "

            "FROM dbo.examen_preguntas ep "

            "JOIN dbo.preguntas_banco pb ON ep.pregunta_banco_id = pb.id "

            "WHERE ep.examen_id = %s ORDER BY ep.orden"

        )



        curs.execute(query, (examen_int_id,))

        rows = curs.fetchall()



        preguntas = []

        for row in rows:

            orden = int(row[0])

            banco_id = int(row[1])

            texto_enunciado = str(row[2]) if row[2] is not None else ""



            resp_raw = str(row[7]) if row[7] is not None else "[]"

            try:

                respuestas_list = _jsonlib.loads(resp_raw)

                if isinstance(respuestas_list, str):

                    respuestas_list = [respuestas_list]

            except (_jsonlib.JSONDecodeError, TypeError):

                respuestas_list = []



            # --- nueva columna: url_fichero en row[8] ---

            url_imagen = str(row[8]) if row[8] is not None and str(row[8]).strip() != '' else None



            preguntas.append({

                "id_banco": banco_id,

                "orden_en_examen": orden,

                "texto_enunciado": texto_enunciado,

                "url_fichero": url_imagen,

                "opciones_a": str(row[3]) if row[3] is not None else "None",

                "opciones_b": str(row[4]) if row[4] is not None else "None",

                "opciones_c": str(row[5]) if row[5] is not None else "None",

                "opciones_d": str(row[6]) if row[6] is not None else "None",

                "respuesta_correcta": respuestas_list,

            })



        log("preguntas → %d preguntas para examen=%s", len(preguntas), exam_id)

        return {"preguntas": preguntas}



    except HTTPException:

        raise

    except Exception as exc:

        import traceback

        traceback.print_exc()

        raise HTTPException(status_code=500, detail=f"Error al obtener preguntas: {str(exc)}")

    finally:

        conn.close()





@app.get("/api/v1/resultados/{examen_id}", response_model=ResultadoResponse | None)

async def obtener_resultado(examen_id: str):

    """Devolver la puntuación final de un examen ya evaluado."""

    # Normalizar session_id (es-...) → id entero; si es numeric, convertir directamente

    examen_int = _obtener_examen_int_id_por_session(examen_id)

    if not examen_int:

        try:

            examen_int = int(examen_id)

        except ValueError:

            raise HTTPException(status_code=404, detail=f"Examen '{examen_id}' no encontrado en BD.")

    resultado = _obtener_resultado_por_examen(examen_int)

    if not resultado:

        raise HTTPException(

            status_code=404,

            detail=f"No hay resultados para el examen con id={examen_id}. El examen aún no ha sido finalizado.",

        )

    return ResultadoResponse(**resultado)







