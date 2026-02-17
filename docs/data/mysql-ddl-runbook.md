# MySQL DDL Runbook

## Scope
- Engine: MySQL 8+
- Schema: `plataformaIa`
- DDL file: `database/mysql/001_init_plataformaIa.sql`

## Apply in local/dev
```bash
mysql -u <user> -p < database/mysql/001_init_plataformaIa.sql
```

## Verify installation
```sql
SHOW DATABASES LIKE 'plataformaIa';
USE plataformaIa;
SHOW TABLES;
SELECT stage_code, stage_order FROM stage_catalog ORDER BY stage_order;
```

## Notes for parallel implementation
- Backend should start by mapping entities in this order:
  1. `users`, `projects`, `project_members`
  2. `stage_catalog`, `project_stage_status`, `project_stage_events`
  3. `agent_catalog`, `project_agent_assignments`, `agent_runs`, `project_artifacts`
- Frontend can consume stage status and agent run data as soon as read endpoints exist.
- Agent orchestration layer should write immutable execution records in `agent_runs`.
