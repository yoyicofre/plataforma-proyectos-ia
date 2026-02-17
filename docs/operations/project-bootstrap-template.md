# Project Bootstrap Template (Reusable)

Usa este archivo como checklist base para crear un nuevo proyecto desde este template.

## 1) Naming estándar

- Repo: `<org>/<project-slug>`
- Lambda prod: `<project-slug>-api`
- API domain: `api.<root-domain>`
- Front domain: `app.<root-domain>`
- DB schema: `<projectSchema>`

## 2) Entornos

- Requerido: `prod`
- Opcional: `dev`
- En GitHub: `Settings > Environments`

## 3) Secrets GitHub (Environment)

Crear en `prod`:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `DB_HOST`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `JWT_SECRET`
- `DEV_BOOTSTRAP_KEY`
- `PORTAL_ACCESS_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

## 4) Variables GitHub (Environment)

Crear en `prod`:

- `AWS_REGION=us-east-1`
- `APP_NAME=<Project Name>`
- `ENVIRONMENT=prod`
- `LOG_LEVEL=INFO`
- `DB_PORT=3306`
- `JWT_ALGORITHM=HS256`
- `JWT_ISSUER=plataforma-ia`
- `JWT_AUDIENCE=plataforma-ia-api`
- `JWT_EXP_MINUTES=480`
- `OPENAI_MODEL_TEXT=gpt-5.2`
- `OPENAI_MODEL_IMAGE=gpt-image-1`
- `GEMINI_MODEL_TEXT=gemini-3-pro-preview`
- `GEMINI_MODEL_IMAGE=gemini-3-pro-image-preview`
- `OPENAI_TEXT_INPUT_COST_PER_1K=0`
- `OPENAI_TEXT_OUTPUT_COST_PER_1K=0`
- `GEMINI_TEXT_INPUT_COST_PER_1K=0`
- `GEMINI_TEXT_OUTPUT_COST_PER_1K=0`
- `OPENAI_IMAGE_COST_PER_IMAGE=0`
- `GEMINI_IMAGE_COST_PER_IMAGE=0`
- `LAMBDA_LAYER_VERSIONS_TO_KEEP=5`
- `FRONTEND_S3_BUCKET=<frontend-bucket-name>`
- `CLOUDFRONT_DISTRIBUTION_ID=<distribution-id>`
- `VITE_API_BASE_URL=https://api.<root-domain>`

## 5) Variables Lambda (runtime)

Asegurar que la Lambda tenga las mismas variables de negocio/infra usadas en el deploy.

Mínimo requerido:

- `ENVIRONMENT=prod`
- `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_ISSUER`, `JWT_AUDIENCE`, `JWT_EXP_MINUTES`
- `DEV_BOOTSTRAP_KEY`
- `OPENAI_API_KEY`, `OPENAI_MODEL_TEXT`, `OPENAI_MODEL_IMAGE`
- `GEMINI_API_KEY`, `GEMINI_MODEL_TEXT`, `GEMINI_MODEL_IMAGE`

Guardas activas en este template:

- `JWT_SECRET` no puede ser default en `prod`.
- `JWT_SECRET` debe tener al menos 32 chars.
- `DEV_BOOTSTRAP_KEY=dev-bootstrap-key` está bloqueado en `prod`.
- `POST /auth/token` deshabilitado en `prod`.

## 6) Deploy pipeline

- Workflow CI: `.github/workflows/ci.yml`
- Workflow deploy: `.github/workflows/deploy-lambda.yml`
- Build layer: `scripts/package_lambda_layer.ps1`
- Build function ZIP: `scripts/package_lambda.ps1`

Ejecución manual:

1. `Actions > Deploy Lambda > Run workflow`
2. `environment=prod`
3. `function_name=<project-slug>-api`

## 7) Dominios y DNS

Backend:

- API Gateway custom domain `api.<root-domain>`
- Route53 alias A al target de API Gateway

Frontend:

- S3 static hosting bucket
- CloudFront con cert ACM (`us-east-1`)
- Route53 alias A `app.<root-domain>` a CloudFront

## 8) Smoke tests post-deploy

- `GET https://api.<root-domain>/health` => `{"status":"ok"}`
- `POST /auth/token` en prod => `403`
- `https://app.<root-domain>` carga sin error y consume API

## 9) Seguridad operativa

- Rotar credenciales si alguna se compartió por chat/captura.
- No guardar secretos reales en repo.
- Usar `.env.local` solo para local.

## 10) Artefactos que deben quedar actualizados por proyecto

- `README.md` (dominios y endpoints reales)
- `docs/operations/aws-custom-domains.md`
- `docs/operations/cicd.md`
- `docs/operations/secrets.md`
- `database/mysql/*.sql` (DDL y migraciones del proyecto)
