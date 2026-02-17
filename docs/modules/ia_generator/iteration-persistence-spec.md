# IA Generator - Iteration Persistence Spec (Draft v1)

Fecha: 2026-02-17  
Objetivo: permitir que el usuario decida explicitamente que iteraciones de `Text IA` guardar en base de datos.

## 1) Regla de negocio

- No se guarda automaticamente toda la conversacion.
- El usuario marca una respuesta del asistente y ejecuta `Guardar iteracion`.
- Solo los mensajes/respuestas seleccionadas quedan persistidas como artefacto reutilizable.

## 2) Modelo de datos propuesto (MySQL 8+)

```sql
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
  KEY idx_ia_conv_user (created_by_user_id)
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
    FOREIGN KEY (message_id) REFERENCES ia_messages(message_id)
);
```

Notas:
- `run_id` conecta cada respuesta IA con `agent_runs`.
- `is_saved` permite marcar rapido en historial.
- `ia_saved_outputs` permite guardar varias respuestas de una misma conversacion con etiquetas distintas.

## 3) API propuesta (MVP)

### 3.1 Conversacion

- `POST /ia/conversations`
  - body: `project_id`, `agent_id`, `title?`
  - out: `conversation_id`

- `GET /ia/conversations?project_id=&agent_id=&limit=&offset=`
  - lista conversaciones del usuario con permisos de proyecto.

- `GET /ia/conversations/{conversation_id}`
  - detalle + mensajes.

### 3.2 Mensajes

- `POST /ia/conversations/{conversation_id}/messages`
  - body: `role`, `content`, `provider?`, `model_name?`, `run_id?`, `cost_usd?`
  - guarda mensaje user/assistant/system.

- `POST /ia/messages/{message_id}/save`
  - body: `label`, `notes?`
  - marca `is_saved=1` y crea fila en `ia_saved_outputs`.

### 3.3 Artefactos guardados

- `GET /ia/saved-outputs?project_id=&agent_id=&limit=&offset=`
  - devuelve iteraciones guardadas para reutilizacion.

## 4) UX propuesta (Generador IA > Text IA)

1. Crear/retomar conversacion:
- selector de proyecto y agente
- boton `Nueva conversacion`
- lista `Conversaciones recientes`

2. Iteracion:
- input prompt
- respuesta de asistente con metadatos (`run`, `provider`, `model`, `costo`)

3. Guardado explicito:
- boton por mensaje assistant: `Guardar iteracion`
- modal:
  - `label` obligatorio
  - `notes` opcional

4. Historial de valor:
- panel `Iteraciones guardadas` (derecha o abajo)
- acciones futuras: `Convertir a tarea`, `Usar como base`, `Exportar`.

## 5) Criterios de aceptacion (MVP)

- Usuario puede guardar una respuesta concreta sin persistir toda la conversacion.
- Cada salida guardada queda vinculada a `project_id`, `agent_id`, `run_id` y `usuario`.
- Listado de guardados filtra por proyecto y respeta permisos.
- Queda trazabilidad de costo por salida guardada.

## 6) Plan de implementacion (Sprint corto)

1. Migracion SQL `003_ia_generator_iterations.sql`.
2. Modulo backend `src/modules/ia_generator/`:
  - `router.py`, `schemas.py`, `service.py`, `dependencies.py`.
3. Integracion frontend:
  - crear conversacion
  - guardar mensajes user/assistant
  - accion `Guardar iteracion`
  - panel de guardados.
4. Smoke tests:
  - crear conversacion
  - persistir mensaje
  - guardar salida
  - listar guardados.
