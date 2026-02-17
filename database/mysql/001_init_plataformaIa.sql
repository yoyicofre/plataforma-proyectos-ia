-- MySQL 8+ bootstrap DDL
-- Schema: plataformaIa
-- Purpose: IA project platform with agent orchestration and stage tracking.

CREATE DATABASE IF NOT EXISTS `plataformaIa`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE `plataformaIa`;

CREATE TABLE IF NOT EXISTS users (
  user_id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  email              VARCHAR(320) NOT NULL,
  display_name       VARCHAR(150) NOT NULL,
  user_status        ENUM('active','inactive','blocked') NOT NULL DEFAULT 'active',
  created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS projects (
  project_id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  project_key         VARCHAR(40) NOT NULL,
  project_name        VARCHAR(180) NOT NULL,
  description         TEXT NULL,
  lifecycle_status    ENUM('draft','active','paused','completed','cancelled') NOT NULL DEFAULT 'draft',
  owner_user_id       BIGINT UNSIGNED NOT NULL,
  created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (project_id),
  UNIQUE KEY uq_projects_key (project_key),
  KEY idx_projects_owner (owner_user_id),
  CONSTRAINT fk_projects_owner
    FOREIGN KEY (owner_user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS project_members (
  project_member_id   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  project_id          BIGINT UNSIGNED NOT NULL,
  user_id             BIGINT UNSIGNED NOT NULL,
  member_role         ENUM('admin','operator','viewer') NOT NULL,
  created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (project_member_id),
  UNIQUE KEY uq_project_members_unique (project_id, user_id),
  KEY idx_project_members_user (user_id),
  CONSTRAINT fk_project_members_project
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
  CONSTRAINT fk_project_members_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS stage_catalog (
  stage_id            SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
  stage_code          VARCHAR(40) NOT NULL,
  stage_name          VARCHAR(80) NOT NULL,
  stage_order         SMALLINT UNSIGNED NOT NULL,
  is_terminal         BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (stage_id),
  UNIQUE KEY uq_stage_catalog_code (stage_code),
  UNIQUE KEY uq_stage_catalog_order (stage_order)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS project_stage_status (
  project_stage_status_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  project_id              BIGINT UNSIGNED NOT NULL,
  stage_id                SMALLINT UNSIGNED NOT NULL,
  stage_status            ENUM('not_started','in_progress','blocked','done','failed','skipped') NOT NULL DEFAULT 'not_started',
  started_at              TIMESTAMP NULL,
  completed_at            TIMESTAMP NULL,
  progress_percent        DECIMAL(5,2) NOT NULL DEFAULT 0.00,
  updated_by_user_id      BIGINT UNSIGNED NULL,
  updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (project_stage_status_id),
  UNIQUE KEY uq_project_stage_unique (project_id, stage_id),
  KEY idx_project_stage_status_project (project_id),
  KEY idx_project_stage_status_stage (stage_id),
  CONSTRAINT fk_project_stage_status_project
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
  CONSTRAINT fk_project_stage_status_stage
    FOREIGN KEY (stage_id) REFERENCES stage_catalog(stage_id),
  CONSTRAINT fk_project_stage_status_user
    FOREIGN KEY (updated_by_user_id) REFERENCES users(user_id),
  CONSTRAINT chk_project_stage_progress
    CHECK (progress_percent >= 0.00 AND progress_percent <= 100.00)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS project_stage_events (
  project_stage_event_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  project_id             BIGINT UNSIGNED NOT NULL,
  stage_id               SMALLINT UNSIGNED NOT NULL,
  event_type             ENUM('status_change','handoff','approval','agent_note','error') NOT NULL,
  event_payload          JSON NULL,
  event_note             VARCHAR(500) NULL,
  created_by_user_id     BIGINT UNSIGNED NULL,
  created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (project_stage_event_id),
  KEY idx_project_stage_events_project (project_id),
  KEY idx_project_stage_events_stage (stage_id),
  KEY idx_project_stage_events_type (event_type),
  CONSTRAINT fk_project_stage_events_project
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
  CONSTRAINT fk_project_stage_events_stage
    FOREIGN KEY (stage_id) REFERENCES stage_catalog(stage_id),
  CONSTRAINT fk_project_stage_events_user
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS agent_catalog (
  agent_id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  agent_code           VARCHAR(60) NOT NULL,
  agent_name           VARCHAR(120) NOT NULL,
  module_name          VARCHAR(80) NOT NULL,
  owner_team           VARCHAR(120) NOT NULL,
  default_model        VARCHAR(120) NULL,
  skill_ref            VARCHAR(255) NULL,
  is_active            BOOLEAN NOT NULL DEFAULT TRUE,
  metadata_json        JSON NULL,
  created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (agent_id),
  UNIQUE KEY uq_agent_catalog_code (agent_code),
  KEY idx_agent_catalog_module (module_name)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS project_agent_assignments (
  project_agent_assignment_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  project_id                  BIGINT UNSIGNED NOT NULL,
  agent_id                    BIGINT UNSIGNED NOT NULL,
  stage_id                    SMALLINT UNSIGNED NULL,
  assignment_status           ENUM('active','paused','disabled') NOT NULL DEFAULT 'active',
  assigned_at                 TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  assigned_by_user_id         BIGINT UNSIGNED NULL,
  PRIMARY KEY (project_agent_assignment_id),
  UNIQUE KEY uq_project_agent_stage (project_id, agent_id, stage_id),
  KEY idx_project_agent_assignments_project (project_id),
  KEY idx_project_agent_assignments_agent (agent_id),
  CONSTRAINT fk_project_agent_assignments_project
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
  CONSTRAINT fk_project_agent_assignments_agent
    FOREIGN KEY (agent_id) REFERENCES agent_catalog(agent_id),
  CONSTRAINT fk_project_agent_assignments_stage
    FOREIGN KEY (stage_id) REFERENCES stage_catalog(stage_id),
  CONSTRAINT fk_project_agent_assignments_user
    FOREIGN KEY (assigned_by_user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS agent_runs (
  agent_run_id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  project_id              BIGINT UNSIGNED NOT NULL,
  agent_id                BIGINT UNSIGNED NOT NULL,
  stage_id                SMALLINT UNSIGNED NULL,
  run_status              ENUM('queued','running','success','failed','cancelled','timeout') NOT NULL DEFAULT 'queued',
  trigger_source          ENUM('manual','schedule','event','api') NOT NULL DEFAULT 'manual',
  input_payload           JSON NULL,
  output_payload          JSON NULL,
  error_message           VARCHAR(1000) NULL,
  started_at              TIMESTAMP NULL,
  finished_at             TIMESTAMP NULL,
  duration_ms             BIGINT UNSIGNED NULL,
  token_input_count       INT UNSIGNED NULL,
  token_output_count      INT UNSIGNED NULL,
  cost_usd                DECIMAL(12,6) NULL,
  created_by_user_id      BIGINT UNSIGNED NULL,
  created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (agent_run_id),
  KEY idx_agent_runs_project (project_id),
  KEY idx_agent_runs_agent (agent_id),
  KEY idx_agent_runs_stage (stage_id),
  KEY idx_agent_runs_status (run_status),
  CONSTRAINT fk_agent_runs_project
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
  CONSTRAINT fk_agent_runs_agent
    FOREIGN KEY (agent_id) REFERENCES agent_catalog(agent_id),
  CONSTRAINT fk_agent_runs_stage
    FOREIGN KEY (stage_id) REFERENCES stage_catalog(stage_id),
  CONSTRAINT fk_agent_runs_user
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS project_artifacts (
  artifact_id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  project_id            BIGINT UNSIGNED NOT NULL,
  stage_id              SMALLINT UNSIGNED NULL,
  produced_by_agent_id  BIGINT UNSIGNED NULL,
  artifact_type         ENUM('brief','prd','nfr','adr','api_contract','test_report','release_note','other') NOT NULL,
  artifact_title        VARCHAR(180) NOT NULL,
  storage_url           VARCHAR(1000) NOT NULL,
  checksum_sha256       CHAR(64) NULL,
  artifact_status       ENUM('draft','published','deprecated') NOT NULL DEFAULT 'draft',
  created_by_user_id    BIGINT UNSIGNED NULL,
  created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (artifact_id),
  KEY idx_project_artifacts_project (project_id),
  KEY idx_project_artifacts_stage (stage_id),
  KEY idx_project_artifacts_agent (produced_by_agent_id),
  CONSTRAINT fk_project_artifacts_project
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
  CONSTRAINT fk_project_artifacts_stage
    FOREIGN KEY (stage_id) REFERENCES stage_catalog(stage_id),
  CONSTRAINT fk_project_artifacts_agent
    FOREIGN KEY (produced_by_agent_id) REFERENCES agent_catalog(agent_id),
  CONSTRAINT fk_project_artifacts_user
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
) ENGINE=InnoDB;

-- Base stage seeds for a standard IA project lifecycle.
INSERT INTO stage_catalog (stage_code, stage_name, stage_order, is_terminal) VALUES
  ('intake', 'Intake', 10, FALSE),
  ('discovery', 'Discovery', 20, FALSE),
  ('architecture', 'Architecture', 30, FALSE),
  ('backend', 'Backend Build', 40, FALSE),
  ('frontend', 'Frontend Build', 50, FALSE),
  ('data', 'Data & Integrations', 60, FALSE),
  ('qa', 'QA & Hardening', 70, FALSE),
  ('release', 'Release', 80, TRUE),
  ('operations', 'Operations', 90, TRUE)
ON DUPLICATE KEY UPDATE
  stage_name = VALUES(stage_name),
  stage_order = VALUES(stage_order),
  is_terminal = VALUES(is_terminal);
