# Secrets Management

- No guardar claves reales en archivos versionados.
- Usar `.env.local` (ignorado por git) basado en `.env.example`.
- Rotar credenciales filtradas.
- Separar por ambiente (`dev`, `stg`, `prod`) con secretos distintos.

## Setup local

1. Crear `.env.local` desde `.env.example`.
2. Completar valores reales (DB, JWT, OpenAI, Gemini, AWS profile).
3. Cargar variables en la sesión de PowerShell:

```powershell
./scripts/load_project_env.ps1
```

## Recomendación AWS

- Guardar claves AWS en `~/.aws/credentials` vía `aws configure`.
- En proyecto usar `AWS_PROFILE` en `.env.local`.

## Rotación obligatoria

Si una clave fue compartida por chat/captura, asumir compromiso y rotar inmediatamente:

1. Revocar/Eliminar la clave anterior en el proveedor.
2. Crear clave nueva.
3. Actualizar secretos en:
   - Local (`.env.local`)
   - GitHub Actions (`Settings > Environments > Secrets`)
   - AWS (Parameter Store/Secrets Manager si aplica)
4. Redeploy backend/frontend.
5. Verificar logs por uso inesperado de la clave vieja.

## Guardas de seguridad en producción

- `ENVIRONMENT=prod` o `ENVIRONMENT=production`.
- `JWT_SECRET` debe ser no-default y de al menos 32 caracteres.
- `DEV_BOOTSTRAP_KEY=dev-bootstrap-key` está bloqueado en `prod`.
- `PORTAL_ACCESS_KEY` debe existir y tener al menos 12 caracteres.
- Endpoint `POST /auth/token` deshabilitado en `prod`.

## Variables recomendadas anti-timeout (Text IA)

- `AI_HTTP_TIMEOUT_SECONDS=20`
- `AI_TEXT_INPUT_CHAR_LIMIT=12000`
- `AI_SYSTEM_PROMPT_CHAR_LIMIT=4000`
- `AI_TEXT_DEFAULT_MAX_OUTPUT_TOKENS=700`
- `AI_TEXT_HARD_MAX_OUTPUT_TOKENS=1200`

Objetivo:
- mantener llamadas IA dentro de ventana segura para API Gateway/Lambda
- reducir 503 por respuestas muy extensas o prompts sobredimensionados

## Reuso para nuevos proyectos

- Usar checklist base: `docs/operations/project-bootstrap-template.md`
