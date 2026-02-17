# Data Model

## Engine and schema
- Engine: MySQL 8+
- Schema: `plataformaIa`
- Source of truth DDL: `database/mysql/001_init_plataformaIa.sql`

## Core entities
- `users`: platform users.
- `projects`: IA projects with lifecycle status.
- `project_members`: user membership and role by project.
- `stage_catalog`: fixed stage catalog and order.
- `project_stage_status`: current status per stage for each project.
- `project_stage_events`: stage audit trail (handoff, status change, approval, errors).
- `agent_catalog`: catalog of available agents and module ownership.
- `project_agent_assignments`: which agents are assigned to each project/stage.
- `agent_runs`: agent execution log with status, payloads, cost and timing.
- `project_artifacts`: generated artifacts (PRD, ADR, contracts, reports).

## Relationship overview
- One `project` has many `project_members`.
- One `project` has many `project_stage_status` rows (one per stage).
- One `project_stage_status` is linked to one `stage_catalog` row.
- One `project` has many `project_stage_events` for traceability.
- One `project` has many `project_agent_assignments`.
- One `agent_catalog` row can be assigned to many projects.
- One `project` has many `agent_runs`; each run can be linked to a stage.
- One `project` has many `project_artifacts`; each artifact can be linked to stage and agent.

## Project stage model
Base lifecycle seeded in `stage_catalog`:
1. `intake`
2. `discovery`
3. `architecture`
4. `backend`
5. `frontend`
6. `data`
7. `qa`
8. `release`
9. `operations`

Allowed `project_stage_status.stage_status` values:
- `not_started`
- `in_progress`
- `blocked`
- `done`
- `failed`
- `skipped`

## Agent traceability model
- Every assignment is explicit in `project_agent_assignments`.
- Every execution is immutable in `agent_runs`.
- Stage and execution events are auditable in `project_stage_events`.
- Generated outputs are persisted as `project_artifacts` and linked to project/stage/agent.

## Data constraints and consistency
- Unique email in `users`.
- Unique business key in `projects.project_key`.
- Unique (project, user) membership.
- Unique (project, stage) current stage status.
- Unique stage code and order in catalog.
- Progress bounded by check constraint `0..100`.
- Foreign keys enforce integrity between projects, stages, agents, runs and artifacts.

## Migration strategy
- SQL-first migration files in `database/mysql/`.
- Naming convention: `NNN_<action>_<scope>.sql`.
- Rule: never edit applied files; append a new migration.
- Target execution order:
1. Create schema and base tables.
2. Seed static catalogs (`stage_catalog`).
3. Add incremental changes by new migration files.
