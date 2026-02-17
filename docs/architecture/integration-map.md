# Integration Map

## Integraciones externas
- nombre: MySQL plataformaIa
- tipo: database
- auth: usuario/password + red privada
- rate limits: n/a
- retries: en capa de aplicacion para errores transitorios

- nombre: LLM Provider (pending)
- tipo: API
- auth: API key o IAM
- rate limits: por proveedor/modelo
- retries: exponencial con jitter

- nombre: Artifact Storage (pending, S3 recomendado)
- tipo: object storage
- auth: IAM role
- rate limits: por servicio cloud
- retries: exponencial con idempotencia por key

## Contratos
- OpenAPI: FastAPI `/openapi.json`
- Eventos:
  - `project_stage_events` para cambios por etapa
  - `agent_runs` para ejecuciones de agentes
  - `project_artifacts` para salidas persistidas
