"use strict";
/**
 * Pruebas del analizador. Se ejecutan con:  node prueba-mavlink.js
 *
 * La comprobación del CRC no puede ser circular: si armara las tramas con la
 * misma función que las valida, un polinomio equivocado pasaría inadvertido.
 * Por eso el primer caso contrasta contra el valor de verificación publicado
 * de CRC-16/MCRF4XX, que es el algoritmo que usa MAVLink.
 */

const { MavlinkParser, px4Mode, SEVERITY, FIX_TYPE, MSG } = require("./mavlink");

let fallos = 0;
function ok(cond, nombre, detalle) {
  console.log((cond ? "  ok   " : "  FALLA") + "  " + nombre + (detalle ? "   " + detalle : ""));
  if (!cond) fallos++;
}

/* ── 1. Núcleo del CRC contra el vector publicado ───────────────────────── */

function crcAccumulate(byte, crc) {
  let tmp = byte ^ (crc & 0xff);
  tmp = (tmp ^ (tmp << 4)) & 0xff;
  return ((crc >> 8) ^ (tmp << 8) ^ (tmp << 3) ^ (tmp >> 4)) & 0xffff;
}
function crcRaw(buf) {
  let crc = 0xffff;
  for (const b of buf) crc = crcAccumulate(b, crc);
  return crc;
}

console.log("\nCRC");
const check = crcRaw(Buffer.from("123456789", "ascii"));
ok(check === 0x6f91, "CRC-16/MCRF4XX de \"123456789\" == 0x6F91",
   "obtenido 0x" + check.toString(16).toUpperCase());

/* ── Constructor de tramas, ya con el CRC validado arriba ───────────────── */

function frameV2(msgid, payload, { sysid = 1, compid = 1, seq = 0, truncar = true } = {}) {
  let pay = Buffer.from(payload);
  if (truncar) { let n = pay.length; while (n > 1 && pay[n - 1] === 0) n--; pay = pay.subarray(0, n); }
  const head = Buffer.from([0xfd, pay.length, 0, 0, seq, sysid, compid,
                            msgid & 0xff, (msgid >> 8) & 0xff, (msgid >> 16) & 0xff]);
  const body = Buffer.concat([head.subarray(1), pay]);
  let crc = crcRaw(body);
  crc = crcAccumulate(MSG[msgid].crc, crc);
  const tail = Buffer.alloc(2); tail.writeUInt16LE(crc, 0);
  return Buffer.concat([head, pay, tail]);
}

function frameV1(msgid, payload, { sysid = 1, compid = 1, seq = 0 } = {}) {
  const pay = Buffer.from(payload);
  const head = Buffer.from([0xfe, pay.length, seq, sysid, compid, msgid]);
  const body = Buffer.concat([head.subarray(1), pay]);
  let crc = crcRaw(body);
  crc = crcAccumulate(MSG[msgid].crc, crc);
  const tail = Buffer.alloc(2); tail.writeUInt16LE(crc, 0);
  return Buffer.concat([head, pay, tail]);
}

/* ── 2. GLOBAL_POSITION_INT por v2 ──────────────────────────────────────── */

console.log("\nDecodificación");

const gp = Buffer.alloc(28);
gp.writeUInt32LE(123456, 0);
gp.writeInt32LE(Math.round(20.7431 * 1e7), 4);
gp.writeInt32LE(Math.round(-100.4512 * 1e7), 8);
gp.writeInt32LE(1924000, 12);
gp.writeInt32LE(120400, 16);
gp.writeInt16LE(1840, 20);
gp.writeInt16LE(-320, 22);
gp.writeInt16LE(15, 24);
gp.writeUInt16LE(7300, 26);

let p = new MavlinkParser();
let msgs = p.push(frameV2(33, gp));
ok(msgs.length === 1 && msgs[0].name === "GLOBAL_POSITION_INT", "GLOBAL_POSITION_INT reconocido");
if (msgs.length) {
  const f = msgs[0].fields;
  ok(Math.abs(f.lat - 20.7431) < 1e-6, "latitud", f.lat.toFixed(6));
  ok(Math.abs(f.lon - (-100.4512)) < 1e-6, "longitud", f.lon.toFixed(6));
  ok(Math.abs(f.altRelative - 120.4) < 1e-3, "altura relativa", f.altRelative + " m");
  ok(Math.abs(f.heading - 73) < 1e-6, "rumbo", f.heading + " grados");
}

/* ── 3. HEARTBEAT por v1 y decodificación del modo PX4 ──────────────────── */

const hb = Buffer.alloc(9);
hb.writeUInt32LE((4 << 16) | (4 << 24), 0);   // AUTO / MISSION
hb.writeUInt8(22, 4);                          // VTOL
hb.writeUInt8(12, 5);                          // PX4
hb.writeUInt8(0x81, 6);
hb.writeUInt8(4, 7);

p = new MavlinkParser();
msgs = p.push(frameV1(0, hb));
ok(msgs.length === 1 && msgs[0].name === "HEARTBEAT", "HEARTBEAT v1 reconocido");
if (msgs.length) ok(px4Mode(msgs[0].fields.customMode) === "MISSION", "modo PX4",
                    px4Mode(msgs[0].fields.customMode));

/* ── 4. Truncamiento de v2 ──────────────────────────────────────────────── */

const mc = Buffer.alloc(18);
mc.writeUInt16LE(7, 0);
mc.writeUInt16LE(14, 2);
p = new MavlinkParser();
msgs = p.push(frameV2(42, mc));
ok(msgs.length === 1 && msgs[0].fields.seq === 7 && msgs[0].fields.total === 14,
   "MISSION_CURRENT con extensión", msgs.length ? JSON.stringify(msgs[0].fields) : "");

const st = Buffer.alloc(51);
st.writeUInt8(6, 0);
Buffer.from("Mission started", "ascii").copy(st, 1);
p = new MavlinkParser();
msgs = p.push(frameV2(253, st));
ok(msgs.length === 1 && msgs[0].fields.text === "Mission started",
   "STATUSTEXT tras relleno de ceros", msgs.length ? '"' + msgs[0].fields.text + '"' : "");
ok(msgs.length === 1 && SEVERITY[msgs[0].fields.severity] === "INFO", "severidad traducida");

/* ── 5. Resincronización y reensamblado ─────────────────────────────────── */

console.log("\nRobustez del flujo");

p = new MavlinkParser();
const basura = Buffer.from([0x00, 0xff, 0xfd, 0x13, 0x37, 0xaa]);   // incluye un 0xFD falso
msgs = p.push(Buffer.concat([basura, frameV2(33, gp)]));
ok(msgs.length === 1, "resincroniza tras basura con 0xFD falso", msgs.length + " mensaje(s)");

/* Trama partida en tres datagramas */
p = new MavlinkParser();
const t = frameV2(33, gp);
let acc = [];
acc = acc.concat(p.push(t.subarray(0, 5)));
acc = acc.concat(p.push(t.subarray(5, 9)));
acc = acc.concat(p.push(t.subarray(9)));
ok(acc.length === 1, "reensambla una trama partida en 3 fragmentos");

/* Dos tramas pegadas en un solo datagrama */
p = new MavlinkParser();
msgs = p.push(Buffer.concat([frameV2(33, gp), frameV1(0, hb)]));
ok(msgs.length === 2, "dos tramas en un datagrama", msgs.map((m) => m.name).join(" + "));

/* CRC corrupto: debe descartarse */
p = new MavlinkParser();
const malo = Buffer.from(frameV2(33, gp));
malo[malo.length - 1] ^= 0xff;
msgs = p.push(malo);
ok(msgs.length === 0 && p.stats.crcFail > 0, "descarta CRC corrupto",
   "crcFail=" + p.stats.crcFail);

/* ── Resultado ──────────────────────────────────────────────────────────── */

console.log("\n" + (fallos === 0
  ? "Todo correcto."
  : fallos + " prueba(s) fallidas.") + "\n");
process.exit(fallos === 0 ? 0 : 1);
