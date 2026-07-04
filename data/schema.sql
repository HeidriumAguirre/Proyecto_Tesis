-- ================================================================
-- MODELO LÓGICO - NIVEL FÍSICO
-- Sistema de Tutoría Inteligente (ITS) basado en RAG
-- Colegio San Leonardo Murialdo - Valparaíso
-- Motor: MySQL 8.0+
-- Codificación: UTF8MB4 (soporta tildes, ñ y emojis)
--
-- INSTRUCCIONES:
--   1) Si tu BD ya existe, primero ELIMINALA con:
--        DROP DATABASE IF EXISTS its_murialdo;
--   2) Luego ejecuta este script completo.
--   3) Credenciales semilla:
--        Docente:    heidrium.aguirre@murialdo.cl  / Demo2026!
--        Estudiante: mateo.gonzalez@murialdo.cl     (sin contrasena)
-- ================================================================

DROP DATABASE IF EXISTS its_murialdo;
CREATE DATABASE its_murialdo
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE its_murialdo;

-- ----------------------------------------------------------------
-- 1. USUARIO
-- ----------------------------------------------------------------
CREATE TABLE usuario (
  id_usuario          CHAR(36)      NOT NULL DEFAULT (UUID()),
  rut                 VARCHAR(12)   NOT NULL,
  nombre_completo     VARCHAR(150)  NOT NULL,
  correo_electronico  VARCHAR(150)  NOT NULL,
  clave_hash          VARCHAR(255)  NOT NULL,
  rol                 ENUM(
                        'Profesor_Asignatura',
                        'Educador_PIE',
                        'Administrador',
                        'Estudiante'
                      )             NOT NULL,
  preferencias_dua    JSON          NULL,
  deleted_at          TIMESTAMP     NULL,
  fecha_registro      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT pk_usuario PRIMARY KEY (id_usuario),
  CONSTRAINT uq_usuario_correo UNIQUE (correo_electronico),
  CONSTRAINT uq_usuario_rut    UNIQUE (rut)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 2. ESTUDIANTE_PIE
-- ----------------------------------------------------------------
CREATE TABLE estudiante_pie (
  id_estudiante              CHAR(36)     NOT NULL DEFAULT (UUID()),
  id_usuario                 CHAR(36)     NULL,
  rut                        VARCHAR(12)  NOT NULL,
  nombre_completo            VARCHAR(150) NOT NULL,
  correo_electronico         VARCHAR(150) NULL,
  curso                      ENUM(
                               '1_Basico',
                               '2_Basico',
                               '3_Basico',
                               '4_Basico'
                             )            NOT NULL,
  curso_subdivision          ENUM('A','B') NULL,
  nivel_adaptacion_lenguaje  ENUM(
                               'Alto',
                               'Medio',
                               'Bajo'
                             )            NOT NULL,
  requiere_apoyo_pictorico   TINYINT      NOT NULL DEFAULT 0,
  preferencias_dua           JSON         NULL,
  deleted_at                 TIMESTAMP    NULL,
  created_by_usuario         CHAR(36)     NULL,
  fecha_registro             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT pk_estudiante_pie PRIMARY KEY (id_estudiante),
  CONSTRAINT uq_estudiante_rut UNIQUE (rut),
  CONSTRAINT fk_estudiante_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario)
    ON DELETE SET NULL
    ON UPDATE CASCADE,
  CONSTRAINT fk_estudiante_created_by
    FOREIGN KEY (created_by_usuario)
    REFERENCES usuario (id_usuario)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 3. DIAGNOSTICO
-- ----------------------------------------------------------------
CREATE TABLE diagnostico (
  id_diagnostico  CHAR(36)     NOT NULL DEFAULT (UUID()),
  codigo          VARCHAR(20)  NOT NULL,
  nombre_completo VARCHAR(150) NOT NULL,
  descripcion     TEXT         NULL,

  CONSTRAINT pk_diagnostico PRIMARY KEY (id_diagnostico),
  CONSTRAINT uq_diagnostico_codigo UNIQUE (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 4. ESTUDIANTE_DIAGNOSTICO (tabla intermedia N:M)
-- ----------------------------------------------------------------
CREATE TABLE estudiante_diagnostico (
  id_estudiante        CHAR(36) NOT NULL,
  id_diagnostico       CHAR(36) NOT NULL,
  fecha_asignacion     DATE     NOT NULL,
  observaciones        TEXT     NULL,
  id_usuario_registro  CHAR(36) NOT NULL,

  CONSTRAINT pk_estudiante_diagnostico
    PRIMARY KEY (id_estudiante, id_diagnostico),

  CONSTRAINT fk_ed_estudiante
    FOREIGN KEY (id_estudiante)
    REFERENCES estudiante_pie (id_estudiante)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_ed_diagnostico
    FOREIGN KEY (id_diagnostico)
    REFERENCES diagnostico (id_diagnostico)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

  CONSTRAINT fk_ed_usuario_registro
    FOREIGN KEY (id_usuario_registro)
    REFERENCES usuario (id_usuario)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 5. OBJETIVO_APRENDIZAJE
-- ----------------------------------------------------------------
CREATE TABLE objetivo_aprendizaje (
  id_oa           CHAR(36)     NOT NULL DEFAULT (UUID()),
  codigo          VARCHAR(10)  NOT NULL,
  descripcion     TEXT         NOT NULL,
  nivel_curso     ENUM(
                    '1_Basico',
                    '2_Basico',
                    '3_Basico',
                    '4_Basico'
                  )            NOT NULL,
  unidad_tematica VARCHAR(150) NULL,
  eje             VARCHAR(100) NULL,

  CONSTRAINT pk_objetivo_aprendizaje PRIMARY KEY (id_oa),
  CONSTRAINT uq_oa_codigo UNIQUE (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 6. SESION_TUTORIA
-- ----------------------------------------------------------------
CREATE TABLE sesion_tutoria (
  id_sesion                CHAR(36)     NOT NULL DEFAULT (UUID()),
  id_estudiante            CHAR(36)     NOT NULL,
  id_usuario               CHAR(36)     NULL,
  id_oa                    CHAR(36)     NOT NULL,
  curso_subdivision        ENUM('A','B') NULL,
  fecha_inicio             DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_fin                DATETIME     NULL,
  estado_emocional_inicial VARCHAR(50)  NULL,
  estado_sesion            ENUM(
                             'Activa',
                             'Completada',
                             'Abandonada'
                           )            NOT NULL DEFAULT 'Activa',
  updated_at               TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                                          ON UPDATE CURRENT_TIMESTAMP,

  CONSTRAINT pk_sesion_tutoria PRIMARY KEY (id_sesion),

  CONSTRAINT fk_sesion_estudiante
    FOREIGN KEY (id_estudiante)
    REFERENCES estudiante_pie (id_estudiante)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

  CONSTRAINT fk_sesion_oa
    FOREIGN KEY (id_oa)
    REFERENCES objetivo_aprendizaje (id_oa)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

  CONSTRAINT fk_sesion_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 7. RECURSO_MINEDUC
-- ----------------------------------------------------------------
CREATE TABLE recurso_mineduc (
  id_recurso        CHAR(36)     NOT NULL DEFAULT (UUID()),
  titulo_documento  VARCHAR(255) NOT NULL,
  tipo_documento    ENUM(
                      'Texto_Escolar',
                      'Guia_Docente',
                      'Programa_Estudio'
                    )            NOT NULL,
  nivel_curso       ENUM(
                      '1_Basico',
                      '2_Basico',
                      '3_Basico',
                      '4_Basico'
                    )            NOT NULL,
  pagina_referencia INT          NULL,
  chunk_id_chromadb VARCHAR(255) NOT NULL,
  url_fuente        VARCHAR(500) NULL,

  CONSTRAINT pk_recurso_mineduc PRIMARY KEY (id_recurso),
  CONSTRAINT uq_chunk_chromadb UNIQUE (chunk_id_chromadb)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 8. HISTORIAL_INTERACCION (bug del copy-paga original corregido)
-- ----------------------------------------------------------------
CREATE TABLE historial_interaccion (
  id_interaccion    CHAR(36)  NOT NULL DEFAULT (UUID()),
  id_sesion         CHAR(36)  NOT NULL,
  id_recurso        CHAR(36)  NULL,
  remitente         ENUM(
                      'Estudiante',
                      'Tutor_IA'
                    )         NOT NULL,
  contenido_mensaje TEXT      NOT NULL,
  fecha_envio       DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT pk_historial_interaccion PRIMARY KEY (id_interaccion),

  CONSTRAINT fk_hi_sesion
    FOREIGN KEY (id_sesion)
    REFERENCES sesion_tutoria (id_sesion)
    ON DELETE CASCADE
    ON UPDATE CASCADE,

  CONSTRAINT fk_hi_recurso
    FOREIGN KEY (id_recurso)
    REFERENCES recurso_mineduc (id_recurso)
    ON DELETE SET NULL
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 9. PLAN_ADAPTACION
-- ----------------------------------------------------------------
CREATE TABLE plan_adaptacion (
  id_plan               CHAR(36)  NOT NULL DEFAULT (UUID()),
  id_estudiante         CHAR(36)  NOT NULL,
  id_educador           CHAR(36)  NOT NULL,
  id_oa                 CHAR(36)  NOT NULL,
  objetivo_priorizado   TEXT      NOT NULL,
  estrategias_sugeridas TEXT      NULL,
  fecha_inicio          DATE      NOT NULL,
  fecha_fin             DATE      NULL,
  estado                ENUM(
                          'Borrador',
                          'Activo',
                          'Cerrado'
                        )         NOT NULL DEFAULT 'Borrador',
  fecha_creacion        DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT pk_plan_adaptacion PRIMARY KEY (id_plan),

  CONSTRAINT fk_pa_estudiante
    FOREIGN KEY (id_estudiante)
    REFERENCES estudiante_pie (id_estudiante)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

  CONSTRAINT fk_pa_educador
    FOREIGN KEY (id_educador)
    REFERENCES usuario (id_usuario)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

  CONSTRAINT fk_pa_oa
    FOREIGN KEY (id_oa)
    REFERENCES objetivo_aprendizaje (id_oa)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 10. SUGERENCIA_PEDAGOGICA
-- ----------------------------------------------------------------
CREATE TABLE sugerencia_pedagogica (
  id_sugerencia      CHAR(36)  NOT NULL DEFAULT (UUID()),
  id_estudiante      CHAR(36)  NOT NULL,
  id_usuario         CHAR(36)  NOT NULL,
  id_oa              CHAR(36)  NOT NULL,
  descripcion_alerta TEXT      NOT NULL,
  actividad_sugerida TEXT      NULL,
  estado             ENUM(
                       'Pendiente',
                       'Vista',
                       'Aplicada'
                     )         NOT NULL DEFAULT 'Pendiente',
  fecha_generacion   DATETIME  NOT NULL DEFAULT CURRENT_TIMESTAMP,
  fecha_vista        DATETIME  NULL,

  CONSTRAINT pk_sugerencia_pedagogica PRIMARY KEY (id_sugerencia),

  CONSTRAINT fk_sp_estudiante
    FOREIGN KEY (id_estudiante)
    REFERENCES estudiante_pie (id_estudiante)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

  CONSTRAINT fk_sp_usuario
    FOREIGN KEY (id_usuario)
    REFERENCES usuario (id_usuario)
    ON DELETE RESTRICT
    ON UPDATE CASCADE,

  CONSTRAINT fk_sp_oa
    FOREIGN KEY (id_oa)
    REFERENCES objetivo_aprendizaje (id_oa)
    ON DELETE RESTRICT
    ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 11. INTENTO_LOGIN (rate limit para login docente)
-- ----------------------------------------------------------------
CREATE TABLE intento_login (
  id_intento  BIGINT       AUTO_INCREMENT PRIMARY KEY,
  email       VARCHAR(150) NOT NULL,
  exitoso     TINYINT      NOT NULL,
  ip_origen   VARCHAR(45)  NULL,
  created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_intento_email_fecha (email, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 12. AUDITORIA_DOCENTE (trazabilidad de acciones PIE)
-- ----------------------------------------------------------------
CREATE TABLE auditoria_docente (
  id_auditoria        BIGINT       AUTO_INCREMENT PRIMARY KEY,
  id_usuario          CHAR(36)     NOT NULL,
  accion              VARCHAR(50)  NOT NULL,
  tabla_afectada      VARCHAR(50)  NULL,
  id_registro         VARCHAR(36)  NULL,
  detalle             JSON         NULL,
  created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_aud_usuario (id_usuario, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------------------------------------------
-- 13. SCHEMA_MIGRATION (control de migraciones)
-- ----------------------------------------------------------------
CREATE TABLE schema_migration (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  filename    VARCHAR(255) NOT NULL UNIQUE,
  applied_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ================================================================
-- ÍNDICES DE RENDIMIENTO
-- ================================================================

CREATE INDEX idx_sesion_estudiante
  ON sesion_tutoria (id_estudiante);

CREATE INDEX idx_historial_sesion
  ON historial_interaccion (id_sesion);

CREATE INDEX idx_plan_estudiante
  ON plan_adaptacion (id_estudiante);

CREATE INDEX idx_plan_estado
  ON plan_adaptacion (estado);

CREATE INDEX idx_sugerencia_estudiante
  ON sugerencia_pedagogica (id_estudiante);

CREATE INDEX idx_sugerencia_estado
  ON sugerencia_pedagogica (estado);

CREATE INDEX idx_recurso_chunk
  ON recurso_mineduc (chunk_id_chromadb);

CREATE INDEX idx_ep_curso_subdivision
  ON estudiante_pie (curso, curso_subdivision, deleted_at);

CREATE INDEX idx_ep_correo
  ON estudiante_pie (correo_electronico);

CREATE INDEX idx_usuario_correo
  ON usuario (correo_electronico);

-- ================================================================
-- DATOS SEMILLA - DIAGNÓSTICOS BASE PIE
-- ================================================================

INSERT INTO diagnostico (id_diagnostico, codigo, nombre_completo, descripcion) VALUES
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
-- DATOS SEMILLA - OBJETIVOS DE APRENDIZAJE (1 por nivel)
-- ================================================================

INSERT INTO objetivo_aprendizaje
  (id_oa, codigo, descripcion, nivel_curso, unidad_tematica, eje) VALUES
  (UUID(), 'MA01-OA01-1B', 'Contar numeros del 0 al 20 de uno en uno y de dos en dos, empezando por cualquier numero menor que 20.', '1_Basico', 'Numeros hasta 20', 'Numeros y operaciones'),
  (UUID(), 'MA01-OA01-2B', 'Contar numeros del 0 al 100 de uno en uno y de diez en diez.', '2_Basico', 'Numeros hasta 100', 'Numeros y operaciones'),
  (UUID(), 'MA01-OA01-3B', 'Contar numeros del 0 al 1000 y leerlos hasta 100.', '3_Basico', 'Numeros hasta 1000', 'Numeros y operaciones'),
  (UUID(), 'MA01-OA01-4B', 'Contar numeros del 0 al 10000.', '4_Basico', 'Numeros hasta 10000', 'Numeros y operaciones');

-- ================================================================
-- DATOS SEMILLA - USUARIO DOCENTE (Educador PIE)
--   Contrasena: Demo2026!  (hash bcrypt rounds=12)
-- ================================================================

INSERT INTO usuario
  (id_usuario, rut, nombre_completo, correo_electronico, clave_hash, rol)
VALUES (
  UUID(),
  '16.234.567-8',
  'Heidi Aguirrre Rivera',
  'heidrium.aguirre@murialdo.cl',
  '$2b$12$ss88pmpNDKdI51cIoK5MiOTTwBiWAb1oLQgPPZGmXOiq/EjFJH8.a',
  'Educador_PIE'
);

-- ================================================================
-- DATOS SEMILLA - USUARIO ESTUDIANTE
--   Sin contrasena: el login es solo por correo.
-- ================================================================

INSERT INTO usuario
  (id_usuario, rut, nombre_completo, correo_electronico, clave_hash, rol)
VALUES (
  UUID(),
  '25.123.456-7',
  'Mateo Gonzalez Perez',
  'mateo.gonzalez@murialdo.cl',
  '!',
  'Estudiante'
);

-- ================================================================
-- DATOS SEMILLA - PERFIL PIE DEL ESTUDIANTE
-- ================================================================

INSERT INTO estudiante_pie
  (id_estudiante, id_usuario, rut, nombre_completo, correo_electronico,
   curso, curso_subdivision, nivel_adaptacion_lenguaje, requiere_apoyo_pictorico)
SELECT
  UUID(),
  u.id_usuario,
  u.rut,
  u.nombre_completo,
  u.correo_electronico,
  '1_Basico',
  'A',
  'Alto',
  1
FROM usuario u
WHERE u.correo_electronico = 'mateo.gonzalez@murialdo.cl';

-- ================================================================
-- DATOS SEMILLA - VINCULACION ESTUDIANTE <-> DIAGNOSTICO TEA
-- ================================================================

INSERT INTO estudiante_diagnostico
  (id_estudiante, id_diagnostico, fecha_asignacion, id_usuario_registro)
SELECT
  e.id_estudiante,
  d.id_diagnostico,
  CURDATE(),
  (SELECT id_usuario FROM usuario WHERE correo_electronico = 'heidrium.aguirre@murialdo.cl' LIMIT 1)
FROM estudiante_pie e
CROSS JOIN diagnostico d
WHERE e.correo_electronico = 'mateo.gonzalez@murialdo.cl'
  AND d.codigo = 'TEA';

-- ================================================================
-- DATOS SEMILLA - MARCAR MIGRACION COMO APLICADA
-- ================================================================

INSERT INTO schema_migration (filename) VALUES ('001_init_its_rag_math.sql');

-- ================================================================
-- FIN DEL SCRIPT
-- ================================================================
