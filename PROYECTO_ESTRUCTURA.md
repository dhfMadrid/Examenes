# Estructura del Proyecto — ExamenesULM_ReactSPA

```
ExamenesULM_ReactSPA/
│
├── 📱 FRONTEND (React 19 + TypeScript + Vite)
│   ├── index.html                   # HTML plantilla SPA (div root)
│   ├── package.json                 # Dependencias y scripts (dev/build/test/ui)
│   ├── tsconfig.json                # TS: path aliases (@core/@domain/@features)
│   ├── tsconfig.node.json           # TS config para tooling (Vite, etc.)
│   ├── vite.config.ts               # Vite dev server + proxy API + Sentry sourcemaps
│   ├── .gitignore                   # node_modules/, dist/, *.env*, coverage…
│   │
│   ├── src/                         # Código fuente TypeScript
│   │   ├── index.tsx                  # Entrada principal: ReactDOM.createRoot()
│   │   ├── App.tsx                    # Componente raíz + React Router setup
│   │   ├── sentry.ts                  # @sentry/react (error tracking manual)
│   │   └── vite-env.d.ts              # Tipos Vite para modules/import.meta.env
│   │
│   ├── core/                          # Utilidades de propósito general
│   │
│   ├── features/                      # Módulos funcionales (Feature-Sliced Design)
│   │   ├── auth-flow/                 # Autenticación (Login + MFA por email OTP)
│   │   │   ├── components/
│   │   │   │   ├── LoginForm.tsx      # Input usuario + contraseña + botón submit
│   │   │   │   ├── LoginPage.css      # Variables CSS: colores, tipografías del login
│   │   │   │   └── LoginPage.tsx      # Layout contenedor del formulario de login
│   │   │   ├── context/
│   │   │   │   ├── AuthContext.tsx    # createContext<{usuario?, jwtToken?}>()
│   │   │   │   ├── AuthGuard.tsx      # <ProtectedRoute> = redirige si no auth
│   │   │   │   └── AuthProvider.tsx   # Provee login/logout y estado de sesión
│   │   │   ├── domain/
│   │   │   │   ├── auth.api.ts        # POST /api/v1/login, /api/v1/mfa/verify
│   │   │   │   └── auth.domain.ts     # Definiciones de tipos (Interfaz Usuario…)
│   │   │   ├── MFAScreen.tsx          # Input código OTP recibido por email
│   │   │   └── __tests__/
│   │   │       └── auth.domain.test.ts  # Unit tests del dominio/auth
│   │   │
│   │   ├── calculator/                # Herramienta calculadora integrada al examen
│   │   │   └── components/
│   │   │       └── Calculadora.tsx     # Pantalla calculadora (páginas 3-5)
│   │   │
│   │   ├── exam/                      # Sesión de examen (pregunta → respuesta iterativa)
│   │   │   ├── pages/
│   │   │   │   └── ExamSessionPage.tsx  # Interfaz principal del examen interactivo
│   │   │   └── domain/
│   │   │       └── question.domain.test.ts  # Tests entidad PreguntaDTO
│   │   │
│   │   ├── exam-selection/            # Listado y selección de exámenes disponibles
│   │   │   ├── pages/
│   │   │   │   └── ExamSelectionPage.tsx  # Grid con <ExamCard> por cada examen
│   │   │   ├── components/
│   │   │   │   └── ExamCard.tsx           # Extracto de examen (título, dificultad)
│   │   │   │       └── __tests__/
│   │   │   │           └── ExamCard.test.tsx  # Snapshot + click del card
│   │   │   ├── services/
│   │   │   │   └── exam.api.ts            # GET /api/v1/examenes/listar
│   │   │   └── __tests__/
│   │   │       └── mockData.ts              # Mocks datos exámenes para tests
│   │   │
│   │   ├── results/                   # Resultados post-examen
│   │   │   └── pages/
│   │   │       └── ResultsPage.tsx      # Resumen correctas/fallos/nota final
│   │   │
│   │   └── timer/                     # Temporizador cuenta atrás del examen
│   │       ├── domain/
│   │       │   └── useTimerCountdown.ts  # Hook React con countdown logic
│   │       └── __tests__/
│   │           ├── timerCleanup.test.tsx         # Verifica limpieza intervalos
│   │           └── useTimerCountdown.test.tsx    # Tests hook countdown
│   │
│   ├── shared/                          # Código compartido (dominio común)
│   │   ├── domain/
│   │   │   ├── scoringRules.ts         # Reglas puntuación (correctas/fallos/nota)
│   │   │   ├── scoringRules.test.ts    # Verificación reglas antes de enviar al backend
│   │   │   ├── timer.domain.ts         # Tipos y constantes temporizador del examen
│   │   │   ├── examSession.ts          # Entidad central: PreguntaDTO, ResultadoExamen…
│   │   │   └── timer.*.test.ts         # Verifica limpieza intervalos del timer
│   │   └── styles/
│   │       └── shared.css              # Variables CSS globales y reset base
│   │
│   └── test/                            # Configuración global de pruebas (Vitest)
│       └── setupVitest.ts               # Importa @testing-library/jest-dom + globals
│
  ════════════════════════

🔙 BACKEND (FastAPI + SQL Server)

backend/                                # Python package root
   ├── requirements.txt                 # FastAPI, uvicorn, pydantic, pymssql
   ├── __init__.py                      # Empty init for python
   └── app/                             # Aplicación FastAPI
       ├── __init__.py                  # Init de módulo
       ├── main.py                      # API principal (1200+ líneas)
                                         #    - Login + MFA contra SQL Server
                                         #    - CRUD exámenes, preguntas, resultados
                                         #    - CORS, middleware Sentry integration
       ├── schemas.py                   # Modelos Pydantic (request/response)
       ├── new_endpoints.py             # Endpoint adicional: examenes finalizados JSONL
       ├── check_bd.py                  # Verificación conectividad BD y consulta datos
       ├── create_db_and_seed.py        # Crea BD + semillas si no existen
       ├── seed_fresh.py                # Limpia + resiembrada completa base de prueba
       ├── setup_db.py                  # Inicialización: crea BD/tables si faltan
       ├── setup_seed.py                # Setup completo (BD + semilla)
       ├── update_user_hash.py          # Actualiza hash contraseña usuario
       └── verify_db.py                 # Verifica estructura/tablas de la base de datos

  ════════════════════════

🗄️ BASE DE DATOS & INFRAESTRUCTURA

docker-compose.yml   Docker Compose — servicio "db"
                      mcr.microsoft.com/mssql/server:2022-latest
                      Puerto 1433:1433 | sa / TuPasswordSeguro123!
                      Volumen persistente: sql_server_data

DB_INTEGRATION_PLAN.md   Diseño de integración BD frontend ↔ backend


  ════════════════════════

☁️ SENTRY (Error Tracking & Monitoring)

sentry.ts                 Configuración @sentry/react en frontend (instrumentación)
vite.config.ts            @sentry/bundler-plugins — subida de sourcemaps a Sentry.io
.env.production.sentry    Credenciales: org (senasa-mx), project, auth token


  ════════════════════════

🧪 SCRIPTS AUXILIARES (desarrollo / demo)

check_db.py                Verificación base de datos local
check_db_real.py           Verificación conexión BD real
check_demo.py              Chequeo demo usuario/contraseña
check_demo_user.py         Validación cuenta demo
check_tiempo.py            Prueba tiempos sincronización backend-frontend
debug_hash.py              Depuración hashes contraseñas
debug_login.py             Debug completo flujo inicio sesión
e2e_test_login.py          Prueba end-to-end del login (Python)


  ════════════════════════

📄 ARCHIVOS DE CONFIGURACIÓN Y ENTORNO

    .env                 Variables locales genéricas (secretos, no en git)
    .env.local           Variables dev overrides (secretos, no en git)
    .env.production      Variables prod (secretos, no en git)
    .env.production.sentry  Config Sentry.io (org/proj/token)


  ════════════════════════

📋 ARCHIVOS DOCUMENTACIÓN

DB_INTEGRATION_PLAN.md   Diseño de integración BD frontend ↔ backend


  ════════════════════════

REPO GIT (exclusiones)

.gitignore               node_modules/, dist/, .env*, coverage, logs…
package-lock.json        Dependencias lock (lockfile para npm install)
```
