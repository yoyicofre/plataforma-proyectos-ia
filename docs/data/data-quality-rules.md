# Data Quality Rules

## Reglas
- completitud:
  - `projects.project_key`, `project_name`, `owner_user_id` son obligatorios.
  - Toda etapa activa de proyecto debe tener fila en `project_stage_status`.
  - Toda ejecucion de agente debe tener `project_id`, `agent_id` y `run_status`.
- validez:
  - `project_stage_status.progress_percent` debe estar entre 0 y 100.
  - `stage_catalog.stage_order` debe ser unico y positivo.
  - `agent_runs.cost_usd` no puede ser negativo.
- unicidad:
  - `users.email` unico.
  - `projects.project_key` unico.
  - `project_members(project_id, user_id)` unico.
  - `project_stage_status(project_id, stage_id)` unico.
- consistencia:
  - Si una etapa esta en `done`, `completed_at` debe estar informado.
  - Si una ejecucion esta en `running`, `started_at` debe estar informado.
  - Si una ejecucion esta en estado terminal (`success|failed|cancelled|timeout`), `finished_at` debe estar informado.
  - Todo `project_artifacts.produced_by_agent_id` debe existir en `agent_catalog`.

## Monitoreo
- KPI diario:
  - porcentaje de proyectos con todas las etapas inicializadas.
  - cantidad de ejecuciones de agente fallidas por etapa.
  - latencia p95 de `agent_runs.duration_ms` por agente.
  - costo diario en USD por proyecto y por agente.
- Alertas:
  - proyectos con etapa `blocked` por mas de X horas.
  - incremento anomalo de errores por agente.
  - artifacts sin checksum en estado `published`.
