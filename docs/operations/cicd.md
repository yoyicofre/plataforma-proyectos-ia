# CI/CD

## Pipeline mínimo (recomendado)
- Preflight (DoR): validar que el proyecto tiene artefactos base (brief/PRD/spec).
- Lint (ruff)
- Tests (pytest)
- (Opcional) Coverage gate (pytest-cov)

## Implementación
Este template incluye workflows en:
- `.github/workflows/ci.yml`
- `.github/workflows/deploy-lambda.yml` (deploy backend Lambda)
- `.github/workflows/deploy-frontend.yml` (deploy frontend S3/CloudFront)

Ajusta:
- versión de Python
- umbrales de cobertura
- jobs adicionales (security scan, SBOM, etc.)

## Deploy Lambda (GitHub Actions)

El workflow `deploy-lambda.yml` soporta:

- `push` a rama `main` (cambios backend)
- `workflow_dispatch` manual con:
  - `environment`: `dev` o `prod`
  - `function_name`: nombre de la Lambda

### Secrets requeridos (GitHub Environment)

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DB_HOST`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `JWT_SECRET`
- `DEV_BOOTSTRAP_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

### Variables recomendadas (GitHub Environment Variables)

- `AWS_REGION` (ej: `us-east-1`)
- `APP_NAME`
- `ENVIRONMENT` (`dev`/`prod`)
- `LOG_LEVEL`
- `DB_PORT`
- `JWT_ALGORITHM`
- `JWT_ISSUER`
- `JWT_AUDIENCE`
- `JWT_EXP_MINUTES`
- `OPENAI_MODEL_TEXT`
- `OPENAI_MODEL_IMAGE`
- `GEMINI_MODEL_TEXT`
- `GEMINI_MODEL_IMAGE`
- `LAMBDA_LAYER_VERSIONS_TO_KEEP` (ej: `5`)
- `FRONTEND_S3_BUCKET`
- `CLOUDFRONT_DISTRIBUTION_ID` (opcional pero recomendado)
- `VITE_API_BASE_URL` (ej: `https://api.mktautomations.com`)

## Reuso para nuevos proyectos

- Usar checklist base: `docs/operations/project-bootstrap-template.md`
