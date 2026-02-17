# Lambda Deploy (FastAPI + ZIP)

## Resumen
Backend FastAPI se empaqueta como ZIP y se despliega a AWS Lambda con handler:
- `lambda_handler.handler`

Se usa `Mangum` para adaptar ASGI -> Lambda.

## Scripts
- Empaquetar:
  - `scripts/package_lambda.ps1`
- Desplegar:
  - `scripts/deploy_lambda.ps1`

## Requisitos
- AWS CLI instalado y autenticado (`aws configure`).
- Variables del proyecto cargadas (`.env.local` + `scripts/load_project_env.ps1`).

## Comandos
```powershell
./scripts/load_project_env.ps1
./scripts/package_lambda.ps1
./scripts/deploy_lambda.ps1 -FunctionName plataforma-ia-api -Region us-east-1
```

## Salida esperada
- Funcion Lambda creada/actualizada.
- Function URL publica para pruebas.

## Notas
- Para produccion, reemplazar Function URL publica por API Gateway + autenticacion.
- Si luego conectas Lambda a VPC privada para RDS, agrega subnets/security groups en configuracion Lambda.
