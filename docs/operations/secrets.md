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
- Endpoint `POST /auth/token` deshabilitado en `prod`.
