# Current Status (2026-02-17)

Estado operativo real de la plataforma `plataforma-proyectos-ia`.

## 1) Infra y dominios

- Frontend activo en `https://app.mktautomations.com`
- API activa en `https://api.mktautomations.com`
- Health check OK: `GET /health -> {"status":"ok"}`
- Deploy backend y frontend funcionando por GitHub Actions.

## 2) Backend (FastAPI + Lambda)

### Autenticacion

- `POST /auth/login` (email + `PORTAL_ACCESS_KEY`)
- `POST /auth/logout`
- `GET /auth/permissions/me`
- `POST /auth/token` habilitado solo en `dev`

### Modulos conectados

- `GET /me/context`
- `GET /me/dashboard`
- `GET /projects/`, `POST /projects/`, `PATCH /projects/{project_id}`
- `GET /projects/{project_id}/stages`, `PUT /projects/{project_id}/stages/{stage_code}`
- `GET /agents/`, `POST /agents/`, `PATCH /agents/{agent_id}`
- `GET /project-agent-assignments/`, `POST /project-agent-assignments/`
- `GET /agent-runs/`, `POST /agent-runs/`
- `GET /costs/summary`
- `POST /ai/text/generate`
- `POST /ai/image/generate`
- `POST /ia/conversations`
- `GET /ia/conversations`
- `GET /ia/conversations/{conversation_id}`
- `POST /ia/conversations/{conversation_id}/messages`
- `POST /ia/messages/{message_id}/save`
- `GET /ia/saved-outputs`
- `GET /ia/text-specialties`

### CORS/preflight

- Se corrigio el bloqueo CORS con manejo global de `OPTIONS`.
- Estado actual: preflight validado con `curl` para `app.mktautomations.com`.

## 3) Frontend (React + Vite)

- Login moderno con marca `automationIA`.
- Dashboard ejecutivo (`Overview`) con KPIs, pipeline y costos por proveedor.
- Tab `Projects`: listado + creacion de proyecto.
- Tab `Costs`: resumen + ultimas ejecuciones (`agent-runs`).
- Tab `Ideas`: gestion de stages por proyecto (carga y actualizacion).
- Tab `Agents`:
  - catalogo + creacion de agente
  - asignacion agente-proyecto
  - ejecucion real de texto (`/ai/text/generate`)
  - ejecucion real de imagen (`/ai/image/generate`) con preview
- Tab `Generador IA`:
  - `Text IA` conversacional con seleccion de motor/modelo
  - selector de especialidad IA (prompt maestro y proveedor/modelo recomendado)
  - contexto de negocio estructurado para analisis experto
  - guardado explicito de iteraciones en DB (usuario decide que persistir)
- Logout real con limpieza de sesion.

## 4) CI/CD y configuracion

- Source of truth recomendado para prod:
  - Secrets/Variables en GitHub Environments
  - Deploy via workflows (`deploy-lambda.yml`, `deploy-frontend.yml`)
- Comando local de deploy backend disponible para soporte, pero no es el flujo principal de prod.

## 5) Base de datos

- Motor: MySQL 8+
- Schema: `plataformaIa`
- DDL base y migraciones:
  - `database/mysql/001_init_plataformaIa.sql`
  - `database/mysql/002_agent_runs_provider_model.sql`
  - `database/mysql/003_ia_generator_iterations.sql`

## 6) Riesgos abiertos

- Endurecer gestion de secretos (migrar a Secrets Manager/SSM para runtime).
- Completar observabilidad operativa (dashboards/alarms en CloudWatch).
- Mejorar trazabilidad de errores en UI (toasts y codigos amigables).

## 7) Proxima iteracion sugerida

1. Definir flujo operativo oficial por rol (`admin`, `operator`, `viewer`).
2. Agregar smoke tests E2E post deploy.
3. Crear vista detalle por proyecto (stages + runs + costos + agentes asignados).
4. Implementar alertas de costo y limites por proyecto/agente.
