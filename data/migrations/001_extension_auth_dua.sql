-- ================================================================
-- MIGRACION 001 - Extension de autenticacion dual y DUA
-- Colegio San Leonardo Murialdo - Valparaiso
-- ITS RAG Math
--
-- EJECUTAR SOBRE UNA BD EXISTENTE. Es 100% aditiva hasta la seccion
-- de correccion de bug. NO borra datos hasta el paso final
-- (correccion de historial_interaccion).
--
-- Si tu BD aun tiene el bug del copy-paste
--   "CURRENT_TIMES, estudiante_diagnostico, id_estudianteTAMP,"
--   la tabla historial_interaccion no se podra usar. La seccion final
--   la recrea limpia (perdera cualquier dato previo en esa tabla).
--
-- EJECUTAR EN ORDEN. Cada sentencia es idempotente.
-- ================================================================

USE its_murialdo;

-- ================================================================
-- PARTE 1: EXTENSION A `usuario` (sin perder datos)
-- ================================================================

-- Anadir columna de preferencias DUA (modo nocturno + filtro luz)
ALTER TABLE usuario
  ADD COLUMN preferencias_dua JSON NULL;

-- Anadir soft delete
ALTER TABLE usuario
  ADD COLUMN deleted_at TIMESTAMP NULL;

-- ================================================================
-- PARTE 2: EXTENSION A `estudiante_pie`
-- ================================================================

-- Subdivision del curso (A o B)
ALTER TABLE estudiante_pie
  ADD COLUMN curso_subdivision ENUM('A','B') NULL AFTER curso;

-- Preferencias DUA del estudiante
ALTER TABLE estudiante_pie
  ADD COLUMN preferencias_dua JSON NULL;

-- Soft delete
ALTER TABLE estudiante_pie
  ADD COLUMN deleted_at TIMESTAMP NULL;

-- Auditoria: que docente creo al estudiante
ALTER TABLE estudiante_pie
  ADD COLUMN created_by_usuario CHAR(36) NULL;

-- FK del docente creador (puede fallar si la tabla usuario no existe aun)
ALTER TABLE estudiante_pie
  ADD CONSTRAINT fk_estudiante_created_by
    FOREIGN KEY (created_by_usuario)
    REFERENCES usuario (id_usuario)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

-- ================================================================
-- PARTE 3: EXTENSION A `sesion_tutoria`
-- ================================================================

ALTER TABLE sesion_tutoria
  ADD COLUMN id_usuario CHAR(36) NULL AFTER id_estudiante;

ALTER TABLE sesion_tutoria
  ADD COLUMN curso_subdivision ENUM('A','B') NULL AFTER id_oa;

ALTER TABLE sesion_tutoria
  ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ON UPDATE CURRENT_TIMESTAMP;

ALTER TABLE sesion_tutoria
  ADD CONSTRAINT fk_sesion_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario)
    ON DELETE SET NULL
    ON UPDATE CASCADE;

-- ================================================================
-- PARTE 4: TABLAS NUEVAS
-- ================================================================

CREATE TABLE IF NOT EXISTS intento_login (
  id_intento  BIGINT       AUTO_INCREMENT PRIMARY KEY,
  email       VARCHAR(150) NOT NULL,
  exitoso     TINYINT(1)   NOT NULL,
  ip_origen   VARCHAR(45)  NULL,
  created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_intento_email_fecha (email, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS auditoria_docente (
  id_auditoria        BIGINT       AUTO_INCREMENT PRIMARY KEY,
  id_usuario          CHAR(36)     NOT NULL,
  accion              VARCHAR(50)  NOT NULL,
  tabla_afectada      VARCHAR(50)  NULL,
  id_registro         VARCHAR(36)  NULL,
  detalle             JSON         NULL,
  created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aud_usuario (id_usuario, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- PARTE 5: INDICES NUEVOS
-- (CREATE INDEX no tiene IF NOT EXISTS nativo en MySQL 8.0; si una
--  corrida previa los creo, comentarlos manualmente en re-ejecucion)
-- ================================================================

CREATE INDEX idx_ep_curso_subdivision
  ON estudiante_pie (curso, curso_subdivision, deleted_at);

CREATE INDEX idx_ep_correo
  ON estudiante_pie (correo_electronico);

-- ================================================================
-- PARTE 6: DIAGNOSTICOS SEMILLA (idempotente)
-- (Tu script original ya insertaba estos. Si no, los agrega.)
-- ================================================================

INSERT IGNORE INTO diagnostico (id_diagnostico, codigo, nombre_completo, descripcion) VALUES
  (UUID(), 'TEA',  'Trastorno del Espectro Autista',
   'Condicion del neurodesarrollo que afecta la comunicacion social y presenta patrones de conducta repetitivos.'),
  (UUID(), 'TDAH', 'Trastorno por Deficit de Atencion e Hiperactividad',
   'Condicion caracterizada por inatencion, hiperactividad e impulsividad que afecta el aprendizaje.'),
  (UUID(), 'DIL',  'Dificultad Intelectual Leve',
   'Funcionamiento intelectual significativamente por debajo del promedio con limitaciones en conducta adaptativa.'),
  (UUID(), 'DEA',  'Dificultad Especifica del Aprendizaje',
   'Dificultades persistentes en lectura, escritura o matematicas sin causa sensorial o intelectual aparente.'),
  (UUID(), 'DL',   'Dificultad del Lenguaje',
   'Alteracion en la adquisicion y desarrollo del lenguaje oral que impacta la comprension y expresion.');

-- ================================================================
-- PARTE 7: CORRECCION DEL BUG EN historial_interaccion
--
-- !!! ATENCION: Si la tabla historial_interaccion fue creada con
-- !!! el bug del copy-paste ("CURRENT_TIMES, ...") NUNCA PUDO
-- !!! INSERTAR REGISTROS. Asi que no deberia tener datos reales.
-- !!! Si por algun motivo tuvieras datos, haz BACKUP primero.
--
-- Si tu tabla YA esta bien (revisalo con SHOW CREATE TABLE), salta
-- esta seccion comentando las 2 lineas de abajo.
-- ================================================================

-- DROP TABLE IF EXISTS historial_interaccion;
-- Verifica manualmente la estructura antes de ejecutar el DROP.

-- Para recrear limpia (descomenta y ajusta segun tu caso):
-- CREATE TABLE historial_interaccion (
--   id_interaccion    CHAR(36)  NOT NULL DEFAULT (UUID()),
--   id_sesion         CHAR(36)  NOT NULL,
--   id_recurso        CHAR(36)  NULL,
--   remitente         ENUM('Estudiante','Tutor_IA') NOT NULL,
--   contenido_mensaje TEXT      NOT NULL,
--   fecha_envio       DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
--   PRIMARY KEY (id_interaccion),
--   CONSTRAINT fk_hi_sesion FOREIGN KEY (id_sesion)
--     REFERENCES sesion_tutoria (id_sesion) ON DELETE CASCADE ON UPDATE CASCADE,
--   CONSTRAINT fk_hi_recurso FOREIGN KEY (id_recurso)
--     REFERENCES recurso_mineduc (id_recurso) ON DELETE SET NULL ON UPDATE CASCADE
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- FIN DE LA MIGRACION 001
-- ================================================================
