# Project Template — FastAPI (modular) + AgentOps-ready

Este template es un punto de partida para proyectos con:

- **FastAPI** backend modular (por dominio)
- estructura de docs para **DoR/DoD**, ADRs, módulos
- lugar claro para permisos, contratos, QA, operación y reporting
- **scaffolder** por spec YAML (Idea → Esqueleto)

## Quick start

```bash
make install
make test
make run
```

## Scaffold por spec (Idea → Esqueleto)

1. Edita `specs/project.spec.yml` con tu proyecto y módulos.
2. Genera el esqueleto:

```bash
make scaffold
```

3. (Opcional) valida DoR mínimo:

```bash
make preflight
```

## Estructura

```
src/
  main.py
  core/
    config.py
    logging.py
    errors.py
    security.py
  modules/
    <module>/
      router.py
      schemas.py
      service.py
      dependencies.py
tests/
  test_health.py
scripts/
  scaffold_from_spec.py
  preflight_check.py
specs/
  project.spec.yml

docs/
  00_intake/           # DoR (brief, PRD, AC, NFR, riesgos, mapa de módulos)
  architecture/        # blueprint, estándares API, integraciones, data model
  frontend/            # rutas → APIs → permisos (FE-INTEGRATOR)
  design/              # design system + tokens (UX-DS)
  security/            # permisos, threat model, supply chain
  qa/                  # test strategy + planes
  operations/          # observabilidad, runbooks, release/rollback, costos
  platform/            # capabilities.yml
  modules/             # docs por módulo
  adr/                 # decisiones
```

## Convención de módulo

Cada módulo tiene (mínimo):

- `router.py` (API)
- `schemas.py` (Pydantic)
- `service.py` (negocio)
- `dependencies.py` (DI + AuthZ por módulo cuando corresponda)

## Dev con Docker

```bash
docker compose up --build
```

## Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Build produccion:

```bash
cd frontend
npm run build
```

Variable frontend:

- `VITE_API_BASE_URL` (ver `frontend/.env.example`)

## Siguiente paso recomendado

1. Publicar/instalar el pack de skills (tu repo interno):

```bash
npx skills add <tu-org>/agent-skills
```

2. Usar `project-factory-orchestrator` + `project-intake` para convertir la idea en `project.spec.yml` + DoR.
3. Usar `app-orchestrator` para ejecutar features end-to-end con gates.

### Nota importante (preflight)

- `project.slug` en `specs/project.spec.yml` debe ser **snake_case** (ej: `fleet_control`).
- El CI ejecuta `make preflight` por defecto (gate mecanico).

## MySQL config

Variables de entorno para backend:

```bash
DB_HOST=localhost
DB_PORT=3306
DB_USER=admin
DB_PASSWORD=your_password
DB_NAME=plataformaIa
JWT_SECRET=change-this-secret
JWT_ALGORITHM=HS256
JWT_ISSUER=plataforma-ia
JWT_AUDIENCE=plataforma-ia-api
JWT_EXP_MINUTES=480
DEV_BOOTSTRAP_KEY=dev-bootstrap-key
PORTAL_ACCESS_KEY=internal-portal-access-key
OPENAI_API_KEY=
OPENAI_MODEL_TEXT=gpt-5.2
OPENAI_MODEL_IMAGE=gpt-image-1
AI_HTTP_TIMEOUT_SECONDS=20
AI_TEXT_INPUT_CHAR_LIMIT=12000
AI_SYSTEM_PROMPT_CHAR_LIMIT=4000
AI_TEXT_DEFAULT_MAX_OUTPUT_TOKENS=700
AI_TEXT_HARD_MAX_OUTPUT_TOKENS=1200
GEMINI_API_KEY=
GEMINI_MODEL_TEXT=gemini-3-pro-preview
GEMINI_MODEL_IMAGE=gemini-3-pro-image-preview
OPENAI_TEXT_INPUT_COST_PER_1K=0
OPENAI_TEXT_OUTPUT_COST_PER_1K=0
GEMINI_TEXT_INPUT_COST_PER_1K=0
GEMINI_TEXT_OUTPUT_COST_PER_1K=0
OPENAI_IMAGE_COST_PER_IMAGE=0
GEMINI_IMAGE_COST_PER_IMAGE=0
```

DDL base:

- `database/mysql/001_init_plataformaIa.sql`
- `docs/data/mysql-ddl-runbook.md`

## API inicial (v0)

- `GET /projects/`
- `GET /projects/{project_id}`
- `POST /projects/`
- `PATCH /projects/{project_id}`
- `GET /projects/{project_id}/stages`
- `PUT /projects/{project_id}/stages/{stage_code}`
- `GET /agents/`
- `GET /agents/{agent_id}`
- `POST /agents/`
- `PATCH /agents/{agent_id}`
- `GET /agent-runs/`
- `POST /agent-runs/`
- `GET /project-agent-assignments/`
- `GET /project-agent-assignments/{assignment_id}`
- `POST /project-agent-assignments/`
- `PATCH /project-agent-assignments/{assignment_id}`
- `GET /projects/{project_id}/members`
- `POST /projects/{project_id}/members`
- `PATCH /projects/{project_id}/members/{member_user_id}`
- `DELETE /projects/{project_id}/members/{member_user_id}`
- `GET /projects/{project_id}/permissions/me`
- `POST /auth/token` (solo dev, emite JWT para pruebas)
- `POST /auth/login` (email + `PORTAL_ACCESS_KEY`, recomendado para frontend interno)
- `GET /auth/permissions/me`
- `GET /me/context`
- `GET /me/dashboard`
- `POST /ai/text/generate`
- `POST /ai/image/generate`
- `POST /ia/conversations`
- `GET /ia/conversations`
- `GET /ia/conversations/{conversation_id}`
- `POST /ia/conversations/{conversation_id}/messages`
- `POST /ia/messages/{message_id}/save`
- `GET /ia/saved-outputs`
- `GET /ia/text-specialties`
- `GET /costs/summary`

Migraciones DB:

- `database/mysql/001_init_plataformaIa.sql`
- `database/mysql/002_agent_runs_provider_model.sql`
- `database/mysql/003_ia_generator_iterations.sql`

Deploy frontend en S3:

- script: `scripts/deploy_frontend_s3.ps1`
- runbook: `docs/operations/frontend-s3.md`
- dominio actual: `https://app.mktautomations.com`

Deploy backend en Lambda (ZIP):

- handler: `lambda_handler.handler`
- scripts: `scripts/package_lambda_layer.ps1`, `scripts/package_lambda.ps1`, `scripts/deploy_lambda.ps1`
- runbook: `docs/operations/lambda-deploy.md`
- dominio actual: `https://api.mktautomations.com`

Runbook de dominios AWS (Route53 + ACM + API Gateway + CloudFront):

- `docs/operations/aws-custom-domains.md`

CI/CD backend (GitHub Actions):

- quality gate: `.github/workflows/ci.yml`
- deploy Lambda: `.github/workflows/deploy-lambda.yml`
- deploy frontend: `.github/workflows/deploy-frontend.yml`
- guia: `docs/operations/cicd.md`
- plantilla reusable (nuevos proyectos): `docs/operations/project-bootstrap-template.md`
- estado operativo actual: `docs/operations/current-status.md`

Secrets locales:

- copiar `.env.example` a `.env.local` (ignorado por git)
- cargar variables en PowerShell con `./scripts/load_project_env.ps1`
- guia: `docs/operations/secrets.md`

Flujo QA/frontend rapido:

- `docs/qa/api-smoke.http`

Notas de seguridad JWT:

- usa `JWT_SECRET` de al menos 32 caracteres.
- `/auth/token` esta deshabilitado cuando `ENVIRONMENT=prod`.
- en `prod`, `JWT_SECRET` default y `DEV_BOOTSTRAP_KEY=dev-bootstrap-key` son rechazados al iniciar la app.

## Autorizacion por proyecto

Fuente de verdad:

- `project_members.member_role` (`admin`, `operator`, `viewer`)

Reglas:

- `GET /projects/*`, `GET /projects/{id}/stages`, `GET /project-agent-assignments/*`, `GET /agent-runs/*`:
  requiere membresia al proyecto (`viewer` o superior).
- `PATCH /projects/{id}`, `PUT /projects/{id}/stages/*`, `POST/PATCH /project-agent-assignments/*`, `POST /agent-runs/`:
  requiere rol de proyecto `admin` o `operator`.
- `POST /projects/`, `POST/PATCH /agents/*`:
  requiere rol global JWT `admin` o `operator`.
- `POST/PATCH/DELETE /projects/{id}/members*`:
  requiere rol de proyecto `admin`.

## Proximo modulo en diseno

- `Generador IA > Text IA` (persistencia bajo decision del usuario):
  - `docs/modules/ia_generator/iteration-persistence-spec.md`
  - `docs/modules/ia_generator/agent-specializations-roadmap.md`
