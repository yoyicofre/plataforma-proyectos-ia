USE `plataformaIa`;

ALTER TABLE agent_runs
  ADD COLUMN provider VARCHAR(20) NULL AFTER stage_id,
  ADD COLUMN model_name VARCHAR(120) NULL AFTER provider,
  ADD KEY idx_agent_runs_provider (provider),
  ADD KEY idx_agent_runs_model_name (model_name);
