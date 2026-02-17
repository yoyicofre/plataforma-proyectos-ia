# Backlog

## Epics
- E1. Operacion de proyectos IA en produccion
- E2. Ejecucion y observabilidad de agentes
- E3. Gobierno de costo y seguridad
- E4. Experiencia de usuario y productividad operativa

## Stories
### E1 - Operacion de proyectos IA
- [ ] Como admin, quiero crear/editar proyectos y estados para gestionar cartera.
- [ ] Como operator, quiero actualizar stages del proyecto para reflejar avance real.
- [ ] Como viewer, quiero consultar KPIs y pipeline sin permisos de edicion.

### E2 - Ejecucion y observabilidad de agentes
- [ ] Como operator, quiero ejecutar agente de texto desde UI y ver salida + run_id.
- [ ] Como operator, quiero ejecutar agente de imagen y ver preview en la plataforma.
- [ ] Como admin, quiero ver historial de agent_runs filtrado por proyecto/agente.

### E3 - Gobierno de costo y seguridad
- [ ] Como admin, quiero ver costo por proveedor/modelo/proyecto en periodos configurables.
- [ ] Como admin, quiero alertas por umbral de costo diario/mensual.
- [ ] Como plataforma, quiero secretos centralizados (AWS Secrets Manager/SSM).

### E4 - UX y productividad
- [ ] Como usuario, quiero mensajes de error claros con accion recomendada.
- [ ] Como usuario, quiero vista detalle de proyecto (stages + runs + costos + agentes asignados).
- [ ] Como equipo, quiero smoke test automatico post deploy.

## Mapa modulo -> historias
- projects -> creacion/edicion/listado, detalle por proyecto
- project_stage_status -> progreso y bloqueos por etapa
- agent_catalog -> alta y mantenimiento de agentes
- project_agent_assignments -> asignacion de agentes por proyecto/etapa
- ai_providers -> ejecucion real texto/imagen
- agent_runs -> historial de ejecucion y trazabilidad
- costs -> resumen economico y futuros limites/alertas
- auth -> login/logout interno y permisos
