# Module Map

## Modulos propuestos

<!-- [agentops:module-list:start] -->
- health
- users
<!-- [agentops:module-list:end] -->

## Entidades principales
- users
- projects
- project_members
- stage_catalog
- project_stage_status
- project_stage_events
- agent_catalog
- project_agent_assignments
- agent_runs
- project_artifacts

## Integraciones
- MySQL 8+ (`plataformaIa`)
- LLM providers (pendiente de definicion)
- Object storage para artifacts (pendiente de definicion)

## Eventos / workflows
- Creacion de proyecto -> inicializar etapas en `project_stage_status`.
- Cambio de estado de etapa -> registrar `project_stage_events`.
- Asignacion de agente por etapa -> `project_agent_assignments`.
- Ejecucion de agente -> `agent_runs` + event log + artifact opcional.
- Cierre de etapa -> validaciones de calidad y avance de pipeline.
