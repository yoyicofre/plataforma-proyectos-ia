# Lambda Deploy (FastAPI + ZIP)

## Resumen
Backend FastAPI se empaqueta como ZIP y se despliega a AWS Lambda con handler:
- `lambda_handler.handler`

Se usa `Mangum` para adaptar ASGI -> Lambda.
Estrategia recomendada:
- ZIP de función solo con código (`lambda_handler.py` + `app/src`)
- Dependencias Python en Lambda Layer

## Scripts
- Empaquetar:
  - `scripts/package_lambda.ps1`
  - `scripts/package_lambda_layer.ps1`
- Desplegar:
  - `scripts/deploy_lambda.ps1`

## Requisitos
- AWS CLI instalado y autenticado (`aws configure`).
- Variables del proyecto cargadas (`.env.local` + `scripts/load_project_env.ps1`).

## Comandos
```powershell
./scripts/load_project_env.ps1
./scripts/package_lambda_layer.ps1
./scripts/package_lambda.ps1
./scripts/deploy_lambda.ps1 -FunctionName plataforma-ia-api -Region us-east-1
```

## Salida esperada
- Funcion Lambda creada/actualizada.
- Function URL publica para pruebas.

## Notas
- En consola Lambda, la vista de código queda ordenada (código propio en `app/`).
- El deploy publica una nueva versión de layer y la adjunta a la función.
- El deploy elimina versiones antiguas del layer según retención (`LayerVersionsToKeep`, default `5`).
- Para produccion, reemplazar Function URL publica por API Gateway + autenticacion.
- Si luego conectas Lambda a VPC privada para RDS, agrega subnets/security groups en configuracion Lambda.

## Presupuesto de latencia IA (GPT-5.2)

Para reducir errores `503` por timeout en prompts largos, configurar:

- `AI_HTTP_TIMEOUT_SECONDS`
- `AI_TEXT_INPUT_CHAR_LIMIT`
- `AI_SYSTEM_PROMPT_CHAR_LIMIT`
- `AI_TEXT_DEFAULT_MAX_OUTPUT_TOKENS`
- `AI_TEXT_HARD_MAX_OUTPUT_TOKENS`
