"use strict";
/**
 * Prueba de extremo a extremo: inyecta tramas MAVLink por UDP como lo haría
 * la estación, y comprueba que salen decodificadas por el WebSocket.
 *
 * Requiere el puente corriendo:   node bridge.js
 */

const dgram = require("dgram");
const { WebSocket } = require("ws");
const { MSG } = require("./mavlink");

const UDP = Number(process.env.OTECH_UDP || 14550);
const WS = Number(process.env.OTECH_WS || 8081);
const SYSID = 42;                       // distinto del demo, para no confundirlos

let fallos = 0;
const ok = (c, n, d) => { console.log((c ? "  ok   " : "  FALLA") + "  " + n + (d ? "   " + d : "")); if (!c) fallos++; };

/* Constructor de tramas v2 (mismo CRC ya validado en prueba-mavlink.js) */
function crcAcc(b, c) { let t = b ^ (c & 0xff); t = (t ^ (t << 4)) & 0xff; return ((c >> 8) ^ (t << 8) ^ (t << 3) ^ (t >> 4)) & 0xffff; }
function frame(msgid, payload, seq) {
  let pay = Buffer.from(payload);
  let n = pay.length; while (n > 1 && pay[n - 1] === 0) n--; pay = pay.subarray(0, n);
  const head = Buffer.from([0xfd, pay.length, 0, 0, seq & 0xff, SYSID, 1,
                            msgid & 0xff, (msgid >> 8) & 0xff, (msgid >> 16) & 0xff]);
  let crc = 0xffff;
  for (const b of Buffer.concat([head.subarray(1), pay])) crc = crcAcc(b, crc);
  crc = crcAcc(MSG[msgid].crc, crc);
  const tail = Buffer.alloc(2); tail.writeUInt16LE(crc, 0);
  return Buffer.concat([head, pay, tail]);
}

const LAT = 20.7455, LON = -100.4488;

function tramas(seq) {
  const out = [];

  const hb = Buffer.alloc(9);
  hb.writeUInt32LE((4 << 16) | (4 << 24), 0);      // AUTO / MISSION
  hb.writeUInt8(22, 4); hb.writeUInt8(12, 5);
  hb.writeUInt8(0x81, 6); hb.writeUInt8(4, 7);     // armado
  out.push(frame(0, hb, seq));

  const gp = Buffer.alloc(28);
  gp.writeUInt32LE(seq * 200, 0);
  gp.writeInt32LE(Math.round((LAT + seq * 0.0004) * 1e7), 4);
  gp.writeInt32LE(Math.round(LON * 1e7), 8);
  gp.writeInt32LE(1924000, 12);
  gp.writeInt32LE(120400, 16);
  gp.writeInt16LE(1840, 20); gp.writeInt16LE(0, 22); gp.writeInt16LE(-60, 24);
  gp.writeUInt16LE(7300, 26);
  out.push(frame(33, gp, seq));

  const hud = Buffer.alloc(20);
  hud.writeFloatLE(21.2, 0); hud.writeFloatLE(18.4, 4);
  hud.writeFloatLE(1924, 8); hud.writeFloatLE(0.6, 12);
  hud.writeInt16LE(73, 16); hud.writeUInt16LE(62, 18);
  out.push(frame(74, hud, seq));

  const gps = Buffer.alloc(30);
  gps.writeInt32LE(Math.round(LAT * 1e7), 8);
  gps.writeInt32LE(Math.round(LON * 1e7), 12);
  gps.writeInt32LE(1924000, 16);
  gps.writeUInt16LE(70, 20);                       // HDOP 0.70
  gps.writeUInt8(6, 28);                           // RTK fijo
  gps.writeUInt8(18, 29);
  out.push(frame(24, gps, seq));

  const sys = Buffer.alloc(31);
  sys.writeUInt16LE(22100, 14);                    // 22.1 V
  sys.writeInt16LE(1420, 16);                      // 14.2 A
  sys.writeUInt16LE(20, 18);                       // 0.2 % pérdida
  sys.writeInt8(68, 30);                           // 68 %
  out.push(frame(1, sys, seq));

  const mc = Buffer.alloc(18);
  mc.writeUInt16LE(7, 0); mc.writeUInt16LE(14, 2);
  out.push(frame(42, mc, seq));

  const rs = Buffer.alloc(9);
  rs.writeUInt8(Math.round((-67 + 127) * 1.9), 4); // −67 dBm
  out.push(frame(109, rs, seq));

  if (seq === 3) {
    const st = Buffer.alloc(51);
    st.writeUInt8(5, 0);                            // NOTICE
    Buffer.from("Prueba de extremo a extremo", "ascii").copy(st, 1);
    out.push(frame(253, st, seq));
  }
  return out;
}

/* ── Ejecución ────────────────────────────────────────────────────────── */

console.log("\nExtremo a extremo (UDP -> puente -> WebSocket)\n");

const sock = dgram.createSocket("udp4");
const ws = new WebSocket("ws://127.0.0.1:" + WS + "/");

let visto = null, evento = false;

ws.on("open", () => {
  ok(true, "WebSocket conectado al puente");
  let seq = 0;
  const it = setInterval(() => {
    if (++seq > 6) { clearInterval(it); return; }
    for (const t of tramas(seq)) sock.send(t, UDP, "127.0.0.1");
  }, 200);
});

ws.on("message", (raw) => {
  const m = JSON.parse(raw);
  if (m.tipo === "telemetria") {
    const v = m.flota.find((x) => x.sysid === SYSID);
    if (v && v.lat !== null) visto = v;
  }
  if (m.tipo === "evento" && /extremo a extremo/i.test(m.evento.texto || "")) evento = true;
});

ws.on("error", (e) => { console.error("  No se pudo conectar: " + e.message);
  console.error("  ¿Está corriendo el puente?  node bridge.js\n"); process.exit(1); });

setTimeout(() => {
  console.log("");
  ok(!!visto, "la aeronave sysid " + SYSID + " apareció en el WebSocket");
  if (visto) {
    ok(visto.enlace === true, "enlace marcado activo");
    ok(visto.modo === "MISSION", "modo de vuelo", visto.modo);
    ok(visto.armado === true, "estado armado");
    ok(visto.tipo === "VTOL", "tipo de aeronave", visto.tipo);
    ok(Math.abs(visto.altRel - 120.4) < 0.05, "altura relativa", visto.altRel + " m");
    ok(Math.abs(visto.velSuelo - 18.4) < 0.05, "velocidad de suelo", visto.velSuelo + " m/s");
    ok(Math.abs(visto.velAire - 21.2) < 0.05, "velocidad aerodinámica", visto.velAire + " m/s");
    ok(visto.satelites === 18, "satélites", String(visto.satelites));
    ok(visto.fix === "RTK fijo", "tipo de fijado", visto.fix);
    ok(Math.abs(visto.hdop - 0.70) < 0.01, "HDOP", String(visto.hdop));
    ok(visto.bateriaPct === 68, "batería", visto.bateriaPct + " %");
    ok(Math.abs(visto.voltaje - 22.1) < 0.01, "voltaje", visto.voltaje + " V");
    ok(visto.wpActual === 7 && visto.wpTotal === 14, "waypoint",
       visto.wpActual + "/" + visto.wpTotal);
    ok(visto.rssi === -67, "RSSI", visto.rssi + " dBm");
    ok(visto.estela.length > 1, "estela acumulada", visto.estela.length + " puntos");
  }
  ok(evento, "STATUSTEXT llegó como evento");

  console.log("\n" + (fallos === 0 ? "Todo correcto." : fallos + " prueba(s) fallidas.") + "\n");
  sock.close(); ws.close();
  process.exit(fallos === 0 ? 0 : 1);
}, 2600);
