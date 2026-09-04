-- AeroHub Link — histórico de telemetría (MariaDB de XAMPP)
--
-- Cargar con:
--   D:\xampp\mysql\bin\mysql.exe -u root < schema.sql
-- o pegándolo en phpMyAdmin.

CREATE DATABASE IF NOT EXISTS aerohub_link
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE aerohub_link;

-- Una fila por segundo y aeronave. A 1 Hz son ~86 k filas por día y aeronave;
-- con la partición mensual de abajo, purgar un periodo es soltar particiones
-- en vez de un DELETE que bloquea la tabla.
CREATE TABLE IF NOT EXISTS telemetria (
  id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  sysid        SMALLINT UNSIGNED NOT NULL,
  t            DATETIME(3)     NOT NULL,
  lat          DOUBLE          NULL,
  lon          DOUBLE          NULL,
  alt_rel      FLOAT           NULL COMMENT 'm sobre el punto de despegue',
  alt_msl      FLOAT           NULL COMMENT 'm sobre el nivel medio del mar',
  vel_suelo    FLOAT           NULL,
  vel_aire     FLOAT           NULL,
  rumbo        FLOAT           NULL,
  bateria_pct  TINYINT         NULL,
  voltaje      FLOAT           NULL,
  satelites    TINYINT UNSIGNED NULL,
  modo         VARCHAR(16)     NULL,
  armado       TINYINT(1)      NOT NULL DEFAULT 0,
  PRIMARY KEY (id, t),
  KEY idx_sysid_t (sysid, t)
) ENGINE=InnoDB
  PARTITION BY RANGE (TO_DAYS(t)) (
    PARTITION p_inicial VALUES LESS THAN (TO_DAYS('2026-01-01')),
    PARTITION p_max     VALUES LESS THAN MAXVALUE
  );

-- Bitácora de eventos MAVLink (STATUSTEXT y los del propio puente).
CREATE TABLE IF NOT EXISTS eventos (
  id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  sysid   SMALLINT UNSIGNED NULL,
  t       DATETIME(3)     NOT NULL,
  nivel   ENUM('info','ok','warn','alert','crit') NOT NULL DEFAULT 'info',
  texto   VARCHAR(255)    NOT NULL,
  KEY idx_t (t)
) ENGINE=InnoDB;

-- Catálogo de aeronaves, para poner nombre y matrícula a cada sysid.
CREATE TABLE IF NOT EXISTS aeronaves (
  sysid       SMALLINT UNSIGNED NOT NULL PRIMARY KEY,
  nombre      VARCHAR(64)  NOT NULL,
  matricula   VARCHAR(32)  NULL COMMENT 'registro AFAC',
  remote_id   VARCHAR(64)  NULL COMMENT 'serie ASTM F3411',
  modelo      VARCHAR(64)  NULL,
  notas       VARCHAR(255) NULL
) ENGINE=InnoDB;

INSERT IGNORE INTO aeronaves (sysid, nombre, modelo) VALUES
  (1, 'VTOL-01', 'PX4 Standard VTOL');

-- Resumen por vuelo, útil para la bitácora que pide la autoridad.
CREATE OR REPLACE VIEW resumen_diario AS
SELECT
  sysid,
  DATE(t)                       AS dia,
  MIN(t)                        AS primer_dato,
  MAX(t)                        AS ultimo_dato,
  COUNT(*)                      AS muestras,
  ROUND(MAX(alt_rel), 1)        AS techo_agl_m,
  ROUND(MAX(vel_suelo), 1)      AS vel_max_ms,
  MIN(bateria_pct)              AS bateria_minima_pct
FROM telemetria
WHERE armado = 1
GROUP BY sysid, DATE(t);
