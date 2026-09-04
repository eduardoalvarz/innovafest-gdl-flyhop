"use strict";
/**
 * Analizador MAVLink v1/v2 mínimo, sin dependencias.
 *
 * Solo decodifica los mensajes que la consola muestra. Se escribió a mano en
 * lugar de traer una biblioteca porque así no hay que generar dialectos ni
 * depender de la red para instalar, y porque el conjunto de mensajes es chico
 * y estable.
 */

/* ── CRC X.25 sobre la trama, con el byte CRC_EXTRA del mensaje ──────────── */

function crcAccumulate(byte, crc) {
  let tmp = byte ^ (crc & 0xff);
  tmp = (tmp ^ (tmp << 4)) & 0xff;
  return ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xffff;
}

function crcCalculate(buf, extra) {
  let crc = 0xffff;
  for (let i = 0; i < buf.length; i++) crc = crcAccumulate(buf[i], crc);
  return crcAccumulate(extra, crc);
}

/* ── Catálogo: id -> { nombre, mínimo, completo, CRC_EXTRA } ──────────────
   `min` es MIN_LEN: el mensaje base, sin extensiones. Es a lo que se rellena
   un payload recortado por v2, y cubre todos los campos que aquí se leen.
   `full` es MAVLINK_MSG_ID_*_LEN, con extensiones; se deja documentado porque
   un PX4 moderno emite esa longitud y conviene no confundirla con un error.
   Los CRC salen de las cabeceras generadas que compila el propio proyecto.   */

const MSG = {
  0:   { name: "HEARTBEAT",           min: 9,  full: 9,  crc: 50  },
  1:   { name: "SYS_STATUS",          min: 31, full: 43, crc: 124 },
  24:  { name: "GPS_RAW_INT",         min: 30, full: 52, crc: 24  },
  33:  { name: "GLOBAL_POSITION_INT", min: 28, full: 28, crc: 104 },
  42:  { name: "MISSION_CURRENT",     min: 2,  full: 18, crc: 28  },
  74:  { name: "VFR_HUD",             min: 20, full: 20, crc: 20  },
  109: { name: "RADIO_STATUS",        min: 9,  full: 9,  crc: 185 },
  147: { name: "BATTERY_STATUS",      min: 36, full: 54, crc: 154 },
  253: { name: "STATUSTEXT",          min: 51, full: 54, crc: 83  }
};

/* ── Decodificadores ──────────────────────────────────────────────────────
   El orden de los campos es el del cable (ordenados por tamaño descendente),
   no el del XML. Los payload de v2 llegan con los ceros finales recortados,
   así que se rellenan antes de leer.                                        */

const DECODE = {
  HEARTBEAT: (p) => ({
    customMode:    p.readUInt32LE(0),
    type:          p.readUInt8(4),
    autopilot:     p.readUInt8(5),
    baseMode:      p.readUInt8(6),
    systemStatus:  p.readUInt8(7)
  }),

  SYS_STATUS: (p) => ({
    load:            p.readUInt16LE(12) / 10,          // %
    voltageBattery:  p.readUInt16LE(14) / 1000,        // V
    currentBattery:  p.readInt16LE(16) / 100,          // A
    dropRateComm:    p.readUInt16LE(18) / 100,         // %
    batteryRemaining: p.readInt8(30)                   // %
  }),

  GPS_RAW_INT: (p) => ({
    lat:        p.readInt32LE(8) / 1e7,
    lon:        p.readInt32LE(12) / 1e7,
    altMsl:     p.readInt32LE(16) / 1000,              // m
    eph:        p.readUInt16LE(20) / 100,              // HDOP
    fixType:    p.readUInt8(28),
    satellites: p.readUInt8(29)
  }),

  GLOBAL_POSITION_INT: (p) => ({
    timeBootMs:  p.readUInt32LE(0),
    lat:         p.readInt32LE(4) / 1e7,
    lon:         p.readInt32LE(8) / 1e7,
    altMsl:      p.readInt32LE(12) / 1000,             // m
    altRelative: p.readInt32LE(16) / 1000,             // m sobre el despegue
    vx:          p.readInt16LE(20) / 100,
    vy:          p.readInt16LE(22) / 100,
    vz:          p.readInt16LE(24) / 100,
    heading:     p.readUInt16LE(26) / 100              // grados; 65535 = desconocido
  }),

  MISSION_CURRENT: (p) => {
    const o = { seq: p.readUInt16LE(0) };
    if (p.length >= 4) o.total = p.readUInt16LE(2);    // extensión posterior
    return o;
  },

  VFR_HUD: (p) => ({
    airspeed:    p.readFloatLE(0),
    groundspeed: p.readFloatLE(4),
    altMsl:      p.readFloatLE(8),
    climb:       p.readFloatLE(12),
    heading:     p.readInt16LE(16),
    throttle:    p.readUInt16LE(18)
  }),

  RADIO_STATUS: (p) => ({
    rxerrors: p.readUInt16LE(0),
    // El campo va 0..254; la convención de SiK es dBm = valor/1.9 - 127
    rssi:     Math.round(p.readUInt8(4) / 1.9 - 127),
    remrssi:  Math.round(p.readUInt8(5) / 1.9 - 127),
    noise:    p.readUInt8(7)
  }),

  BATTERY_STATUS: (p) => ({
    currentConsumed:  p.readInt32LE(0),                // mAh
    temperature:      p.readInt16LE(8),
    voltageCell1:     p.readUInt16LE(10) / 1000,
    currentBattery:   p.readInt16LE(30) / 100,
    batteryRemaining: p.readInt8(35)
  }),

  STATUSTEXT: (p) => {
    const raw = p.subarray(1, 51);
    const end = raw.indexOf(0);
    return {
      severity: p.readUInt8(0),
      text: raw.subarray(0, end === -1 ? raw.length : end).toString("ascii").trim()
    };
  }
};

/* ── Máquina de tramas ────────────────────────────────────────────────────
   Trabaja sobre un búfer acumulado y resincroniza buscando el byte de inicio,
   de modo que un datagrama partido o basura intermedia no la descarrilan.   */

class MavlinkParser {
  constructor() {
    this.buf = Buffer.alloc(0);
    this.stats = { frames: 0, crcFail: 0, unknown: 0 };
  }

  /** Devuelve el arreglo de mensajes decodificados en este fragmento. */
  push(chunk) {
    this.buf = this.buf.length ? Buffer.concat([this.buf, chunk]) : chunk;
    const out = [];

    let i = 0;
    while (i < this.buf.length) {
      const stx = this.buf[i];

      if (stx !== 0xfd && stx !== 0xfe) { i++; continue; }   // resincronizar

      const v2 = stx === 0xfd;
      const headLen = v2 ? 10 : 6;
      if (i + headLen > this.buf.length) break;              // falta cabecera

      const payLen = this.buf[i + 1];
      let msgid, signed = false;

      if (v2) {
        const incompat = this.buf[i + 2];
        signed = (incompat & 0x01) !== 0;
        msgid = this.buf[i + 7] | (this.buf[i + 8] << 8) | (this.buf[i + 9] << 16);
      } else {
        msgid = this.buf[i + 5];
      }

      const total = headLen + payLen + 2 + (signed ? 13 : 0);
      if (i + total > this.buf.length) break;                // trama incompleta

      const def = MSG[msgid];
      if (def) {
        // El CRC cubre desde el byte siguiente al STX hasta el fin del payload
        const body = this.buf.subarray(i + 1, i + headLen + payLen);
        const want = this.buf.readUInt16LE(i + headLen + payLen);

        if (crcCalculate(body, def.crc) === want) {
          this.stats.frames++;
          let pay = this.buf.subarray(i + headLen, i + headLen + payLen);
          if (pay.length < def.full) {
            // v2 recorta los ceros finales. Hay que rellenar hasta la longitud
            // COMPLETA, no hasta MIN_LEN: si no, los campos de extensión (el
            // `total` de MISSION_CURRENT, por ejemplo) caen fuera del búfer.
            pay = Buffer.concat([pay, Buffer.alloc(def.full - pay.length)]);
          }
          try {
            out.push({
              msgid,
              name: def.name,
              sysid: this.buf[i + (v2 ? 5 : 3)],
              compid: this.buf[i + (v2 ? 6 : 4)],
              fields: DECODE[def.name](pay)
            });
          } catch (e) {
            this.stats.unknown++;   // payload más corto de lo esperado
          }
        } else {
          this.stats.crcFail++;
          i++;                      // CRC malo: probablemente no era un inicio
          continue;
        }
      } else {
        // Mensaje que no decodificamos. Sin su CRC_EXTRA no se puede validar,
        // así que su campo de longitud no es de fiar: saltarlo a ciegas puede
        // devorar la trama buena que viene detrás. Se avanza un byte y se
        // vuelve a buscar inicio. Cuesta unas decenas de iteraciones por
        // mensaje ignorado y a cambio la sincronía se recupera sola.
        this.stats.unknown++;
        i++;
        continue;
      }

      i += total;
    }

    this.buf = i > 0 ? this.buf.subarray(i) : this.buf;
    if (this.buf.length > 64 * 1024) this.buf = Buffer.alloc(0);   // salvaguarda
    return out;
  }
}

/* ── Tablas de traducción ─────────────────────────────────────────────── */

const SEVERITY = ["EMERGENCY", "ALERT", "CRITICAL", "ERROR",
                  "WARNING", "NOTICE", "INFO", "DEBUG"];

const FIX_TYPE = ["sin GPS", "sin fijado", "2D", "3D", "DGPS", "RTK flotante", "RTK fijo"];

/* Modos de vuelo de PX4: el modo va empaquetado en custom_mode.
   Los 8 bits altos son el modo principal; los siguientes, el submodo. */
const PX4_MAIN = {
  1: "MANUAL", 2: "ALTCTL", 3: "POSCTL", 4: "AUTO",
  5: "ACRO", 6: "OFFBOARD", 7: "STABILIZED", 8: "RATTITUDE"
};
const PX4_AUTO_SUB = {
  1: "READY", 2: "TAKEOFF", 3: "LOITER", 4: "MISSION",
  5: "RTL", 6: "LAND", 7: "RTGS", 8: "FOLLOW", 9: "PRECLAND"
};

function px4Mode(customMode) {
  const main = (customMode >> 16) & 0xff;
  const sub = (customMode >> 24) & 0xff;
  if (main === 4) return PX4_AUTO_SUB[sub] || "AUTO";
  return PX4_MAIN[main] || "—";
}

/* MAV_TYPE: los que puede reportar un VTOL estándar */
const MAV_TYPE = {
  1: "ala fija", 2: "multirrotor", 13: "hexacóptero", 14: "octocóptero",
  19: "VTOL dual", 20: "VTOL quad", 21: "VTOL tiltrotor", 22: "VTOL"
};

module.exports = { MavlinkParser, SEVERITY, FIX_TYPE, MAV_TYPE, px4Mode, MSG };
