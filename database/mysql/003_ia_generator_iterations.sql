CREATE TABLE IF NOT EXISTS ia_conversations (
  conversation_id       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  project_id            BIGINT UNSIGNED NOT NULL,
  agent_id              BIGINT UNSIGNED NOT NULL,
  title                 VARCHAR(180) NULL,
  status                ENUM('draft','saved','archived') NOT NULL DEFAULT 'draft',
  created_by_user_id    BIGINT UNSIGNED NOT NULL,
  created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (conversation_id),
  KEY idx_ia_conv_project (project_id),
  KEY idx_ia_conv_agent (agent_id),
  KEY idx_ia_conv_user (created_by_user_id),
  CONSTRAINT fk_ia_conv_project
    FOREIGN KEY (project_id) REFERENCES projects(project_id),
  CONSTRAINT fk_ia_conv_agent
    FOREIGN KEY (agent_id) REFERENCES agent_catalog(agent_id),
  CONSTRAINT fk_ia_conv_user
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS ia_messages (
  message_id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  conversation_id       BIGINT UNSIGNED NOT NULL,
  role                  ENUM('system','user','assistant') NOT NULL,
  content               MEDIUMTEXT NOT NULL,
  provider              VARCHAR(40) NULL,
  model_name            VARCHAR(120) NULL,
  run_id                BIGINT UNSIGNED NULL,
  cost_usd              DECIMAL(14,6) NULL,
  is_saved              TINYINT(1) NOT NULL DEFAULT 0,
  created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (message_id),
  KEY idx_ia_msg_conv (conversation_id),
  KEY idx_ia_msg_run (run_id),
  CONSTRAINT fk_ia_msg_conv
    FOREIGN KEY (conversation_id) REFERENCES ia_conversations(conversation_id),
  CONSTRAINT fk_ia_msg_run
    FOREIGN KEY (run_id) REFERENCES agent_runs(agent_run_id)
);

CREATE TABLE IF NOT EXISTS ia_saved_outputs (
  saved_output_id       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  conversation_id       BIGINT UNSIGNED NOT NULL,
  message_id            BIGINT UNSIGNED NOT NULL,
  label                 VARCHAR(180) NOT NULL,
  notes                 VARCHAR(1000) NULL,
  created_by_user_id    BIGINT UNSIGNED NOT NULL,
  created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (saved_output_id),
  KEY idx_ia_saved_conv (conversation_id),
  KEY idx_ia_saved_msg (message_id),
  KEY idx_ia_saved_user (created_by_user_id),
  CONSTRAINT fk_ia_saved_conv
    FOREIGN KEY (conversation_id) REFERENCES ia_conversations(conversation_id),
  CONSTRAINT fk_ia_saved_msg
    FOREIGN KEY (message_id) REFERENCES ia_messages(message_id),
  CONSTRAINT fk_ia_saved_user
    FOREIGN KEY (created_by_user_id) REFERENCES users(user_id)
);
