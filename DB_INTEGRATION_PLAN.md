# Plan de Integración con Base de Datos — ExamenesULM ReactSPA

## 📊 Estado Actual (Diagnóstico)

### Frontend (React SPA)
- ✅ Compila sin errores (`tsc --noEmit` → exit 0)
- ✅ Routing real con React Router DOM
- ✅ Vite proxy configurado (`/api/v1` → `http://127.0.0.1:8001`)
- ⚠️ **Todo el frontend consume datos mock/hardcoded en memoria** — ninguna llamada va a la BD

### Backend (FastAPI)
| Arch | Estado | Problemas críticos |
|------|--------|-------------------|
| `main.py` | ❌ No corre | `DB_PASSWORD` referenced on line 97 but **never defined** → NameError al inicio |
| `schemas.py` | ✅ OK | Solo define LoginRequest/LoginResponse/VerifyMfaRequest — incompleto, no hay schemas para examenes/resultados |
| `seed_db.py` | ⚠️ Incompleto | Crea usuario demo pero depende de `setup_db.py` que debe ejecutarse primero |
| `setup_db.py` | No revisado (asumido OK por seed_db) | — |

### Docker / SQL Server
- docker-compose.yml configura `mcr.microsoft.com/mssql/server:2022-latest` en puerto 1433
- Creds: `sa / TuPasswordSeguro123!`
- ⚠️ **Nadie ha verificado que el contenedor esté corriendo ni que la BD `ExamenesULM` existe**

### Arreglo con Arquitectura Propuesta (NEW_ARCHITECTURE.md)
La propuesta original indicaba .NET 9 + PostgreSQL — pero la implementación actual usa **Python/FastAPI + SQL Server**. El backend actual preserva el modelo de datos existente (`dbo.Alumno`, schema del legacy) como puente durante la migración.

---

## 🗺️ Roadmap de Integración (5 Fases)

### Fase 0: Corrección Crítica — Hacer que el servidor arranque
> **Depende de:** nada
> **Alcance:** Fix `DB_PASSWORD` + verificar contenedor SQL Server

| # | Tarea | Detalle | Estado |
|---|-------|---------|--------|
| 0.1 | Definir `DB_PASSWORD` en `main.py` | Variable referenced but never defined (line 97) | ⬜ |
| 0.2 | Verificar contenedor SQL Server | `docker ps` + conectar con `pymssql` | ⬜ |
| 0.3 | Ejecutar `setup_db.py` | Crear tabla `dbo.Alumno` si no existe | ⬜ |
| 0.4 | Ejecutar `seed_db.py` | Insertar usuario demo (12345678Z / Demo1234) | ⬜ |
| 0.5 | Correr backend y verificar healthcheck | `curl http://127.0.0.1:8001/api/v1/auth/health` | ⬜ |

---

### Fase 1: Consultar Alumnos desde DB (Login paso 1)
> **Depende de:** Fase 0 completada
> **Impacto:** El login real vs BD en lugar de datos mock

| # | Tarea | Detalle | Estado |
|---|-------|---------|--------|
| 1.1 | Verificar schema `dbo.Alumno` | Columns: Id, Nombre, PasswordHash, Salt, Activo, NifPasaporte, FechaCreacion | ⬜ |
| 1.2 | Confirmar que `buscar_alumno()` funciona | Ya existe en main.py (línea 106) pero necesita validar con datos reales | ⬜ |
| 1.3 | Agregar logs/debug al login | Registrar errores de conexión a BD para troubleshooting | ⬜ |

---

### Fase 2: Consultar Examenes desde DB (GET /examenes)
> **Depende de:** Fase 0 + Fase 1
> **Impacto:** Lista real de exámenes en lugar de `EXAMS` hardcodeado

| # | Tarea | Detalle | Estado |
|---|-------|---------|--------|
| 2.1 | Identificar/tablas de examenes en BD | Buscar tablas relacionadas: `Examen`, `Módulo`, estados | ⬜ |
| 2.2 | Crear función `_list_examenes_by_alumno(alumno_id)` | Query contra las tablas correspondientes | ⬜ |
| 2.3 | Reemplazar `EXAMS` mock en endpoint GET `/examenes` | Devolver datos reales con status NP/INI/COMP/FN | ⬜ |

---

### Fase 3: Endpoint CRUD para Exámenes (Sesiones)
> **Depende de:** Fase 2 completada
> **Impacto:** Crear/iniciar/explorar sesiones de examen con datos persistentes

| # | Tarea | Detalle | Estado |
|---|-------|---------|--------|
| 3.1 | Identificar tabla de sesiones de examen en BD | Crear si no existe (estado, preguntas, tiempos) | ⬜ |
| 3.2 | Endpoint `POST /api/v1/exam/session` | Crear nueva sesión → estado=INI | ⬜ |
| 3.3 | Endpoint `GET /api/v1/exam/{sessionId}` | Obtener sesión con preguntas y timer | ⬜ |
| 3.4 | Endpoint `POST /api/v1/exam/{sessionId}/answer` | Registrar respuesta de pregunta individual | ⬜ |

---

### Fase 4: Finalización y Puntuación
> **Depende de:** Fase 3 completada
> **Impacto:** Cerrar examen y calcular resultados reales

| # | Tarea | Detalle | Estado |
|---|-------|---------|--------|
| 4.1 | Migrate finalizado examenes de JSONL a DB | Tabla/endpoint para resultados | ⬜ |
| 4.2 | Implementar scoring (RN-COR-01..04) | PorcAptoTest, excepciones HCo, discrepancias | ⬜ |
| 4.3 | Registrar timestamp de finalización en BD | Actualizar estado → FN | ⬜ |

---

### Fase 5: Healthcheck Real + Validaciones
> **Depende de:** Todas las fases
> **Impacto:** Operacionalidad completa

| # | Tarea | Detalle | Estado |
|---|-------|---------|--------|
| 5.1 | `/health` verifica conexión a BD real | Incluye check de conectividad SQL Server | ⬜ |
| 5.2 | Middleware de logging de requests | Registrar cada endpoint llamado con timestamps | ⬜ |
| 5.3 | Manejo de errores DB graceful | Mensajes amigables + fallback cuando hay problema de BD | ⬜ |

---

## 🐛 Bugs Detectados que Bloquean el Inicio

### CRÍTICO — `DB_PASSWORD` indefinido (main.py línea 97)
```python
# Linea 87-90: solo definimos credenciales pero no la contraseña... o si?
DB_SERVER = "127.0.0.1"
DB_PORT = 1433
DB_USER = "sa"
DB_NAME = "ExamenesULM"
# ❌ Falta: DB_PASSWORD = "TuPasswordSeguro123!"

# Linea 95-98: se referencia en _get_db() sin definir
return pymssql.connect(
    server=DB_SERVER, port=DB_PORT, user=DB_USER,
    password=DB_PASSWORD, database=DB_NAME, autocommit=True,  # <-- NameError!
)
```

### MOCK — `EXAMS` data (main.py líneas 140-152)
La lista de exámenes es un array hardcodeado dentro del archivo. Debe reemplazarse por una query a base de datos.

### INCOMPLETO — Schemas no reflejan DTOs de backend
`schemas.py` solo tiene LoginRequest/LoginResponse/VerifyMfaRequest, pero `main.py` define sus propios ExamenDto/RespuestaPregunta/FinalizarRequest en el mismo archivo (duplicación).

---

## ✅ Checklist Inmediato para Arrancar

```bash
# 1. Verificar contenedor SQL Server corriendo
docker ps --filter "name=tfm_sql_server"

# 2. Si no corre:
docker compose -f E:\TFM_IA\ExamenesULM_ReactSPA\docker-compose.yml up -d

# 3. Esperar a que MSSQL inicie (~15-30 segundos)
# 4. Fix DB_PASSWORD en main.py
# 5. python backend/app/seed_db.py
# 6. python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
# 7. curl http://127.0.0.1:8001/api/v1/auth/health
```
