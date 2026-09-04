"use strict";
/**
 * Puente MAVLink -> WebSocket para Torre OTECH, en local.
 *
 *   OTECH-GroundStation  --UDP 14550-->  este proceso  --WS 8081-->  navegador
 *                                              |
 *                                              +--> MariaDB (histórico, opcional)
 *
 * Solo escucha. No emite nada hacia la aeronave: el mando vive en el enlace RF
 * y esta capa es de supervisión, conforme a la hipótesis S-1 de OTECH-GCS-SW-001.
 * Por eso el socket UDP nunca llama a send().
 */

const dgram = require("dgram");
const http = require("http");
const fs = require("fs");
const path = require("path");
const { WebSocketServer } = require("ws");
const { MavlinkParser, SEVERITY, FIX_TYPE, MAV_TYPE, px4Mode } = require("./mavlink");

/* ── Configuración ────────────────────────────────────────────────────── */

const CFG = {
  udpPort:  Number(process.env.OTECH_UDP  || 14550),
  wsPort:   Number(process.env.OTECH_WS   || 8081),
  webPort:  Number(process.env.OTECH_WEB  || 8080),
  webRoot:  path.join(__dirname, "web"),
  emitHz:   Number(process.env.OTECH_HZ   || 5),     // ritmo hacia el navegador
  logsDir:  path.join(__dirname, "logs"),
  maxLog:   Number(process.env.OTECH_MAX_LOG || 512) * 1048576,
  db:       process.env.OTECH_DB === "1",            // persistencia opcional
  dbConf: {
    host: process.env.OTECH_DB_HOST || "127.0.0.1",
    port: Number(process.env.OTECH_DB_PORT || 3306),
    user: process.env.OTECH_DB_USER || "root",
    password: process.env.OTECH_DB_PASS || "",
    database: process.env.OTECH_DB_NAME || "otech_torre"
  }
};

/* ── Estado de la aeronave ────────────────────────────────────────────── */

function nuevaAeronave(sysid) {
  return {
    sysid,
    nombre: "SYS-" + String(sysid).padStart(2, "0"),
    visto: Date.now(),
    enlace: false,
    modo: "—", armado: false, tipo: "—",
    lat: null, lon: null,
    altRel: null, altMsl: null,
    velSuelo: null, velAire: null, ascenso: null,
    rumbo: null,
    bateriaPct: null, voltaje: null, corriente: null, consumo: null,
    satelites: null, fix: null, hdop: null,
    wpActual: null, wpTotal: null,
    rssi: null, perdida: null,
    estela: []
  };
}

const flota = new Map();
const eventos = [];          // bitácora en memoria (los últimos 200)
const parsers = new Map();   // un analizador por origen UDP

function aeronave(sysid) {
  if (!flota.has(sysid)) {
    flota.set(sysid, nuevaAeronave(sysid));
    log("info", "Aeronave " + sysid + " detectada en el enlace");
  }
  return flota.get(sysid);
}

function log(nivel, texto, sysid) {
  const e = { t: Date.now(), nivel, texto, sysid: sysid || null };
  eventos.push(e);
  if (eventos.length > 200) eventos.shift();
  difundir({ tipo: "evento", evento: e });
  return e;
}

/* ── Ingesta UDP ──────────────────────────────────────────────────────── */

const udp = dgram.createSocket({ type: "udp4", reuseAddr: true });

udp.on("message", (buf, rinfo) => {
  const clave = rinfo.address + ":" + rinfo.port;
  if (!parsers.has(clave)) parsers.set(clave, new MavlinkParser());

  for (const m of parsers.get(clave).push(buf)) {
    const v = aeronave(m.sysid);
    v.visto = Date.now();
    if (!v.enlace) { v.enlace = true; log("ok", "Enlace de telemetría activo", m.sysid); }

    const f = m.fields;
    switch (m.name) {
      case "HEARTBEAT":
        v.modo = px4Mode(f.customMode);
        v.armado = (f.baseMode & 0x80) !== 0;
        v.tipo = MAV_TYPE[f.type] || "—";
        break;

      case "GLOBAL_POSITION_INT":
        v.lat = f.lat; v.lon = f.lon;
        v.altRel = f.altRelative; v.altMsl = f.altMsl;
        v.ascenso = -f.vz;
        if (f.heading !== 655.35) v.rumbo = f.heading;
        // La estela se guarda ralamente: un punto cada ~8 m
        const u = v.estela[v.estela.length - 1];
        if (!u || Math.hypot((f.lat - u[0]) * 111320,
                             (f.lon - u[1]) * 104000) > 8) {
          v.estela.push([f.lat, f.lon]);
          if (v.estela.length > 900) v.estela.shift();
        }
        break;

      case "VFR_HUD":
        v.velSuelo = f.groundspeed; v.velAire = f.airspeed;
        if (v.rumbo === null) v.rumbo = (f.heading + 360) % 360;
        break;

      case "GPS_RAW_INT":
        v.satelites = f.satellites;
        v.fix = FIX_TYPE[f.fixType] || String(f.fixType);
        v.hdop = f.eph;
        break;

      case "SYS_STATUS":
        if (f.batteryRemaining >= 0) v.bateriaPct = f.batteryRemaining;
        v.voltaje = f.voltageBattery;
        v.corriente = f.currentBattery;
        v.perdida = f.dropRateComm;
        break;

      case "BATTERY_STATUS":
        if (f.currentConsumed >= 0) v.consumo = f.currentConsumed;
        if (f.batteryRemaining >= 0) v.bateriaPct = f.batteryRemaining;
        break;

      case "MISSION_CURRENT":
        v.wpActual = f.seq;
        if (f.total !== undefined && f.total > 0) v.wpTotal = f.total;
        break;

      case "RADIO_STATUS":
        v.rssi = f.rssi;
        break;

      case "STATUSTEXT": {
        const sev = SEVERITY[f.severity] || "INFO";
        const nivel = f.severity <= 2 ? "crit"
                    : f.severity === 3 ? "alert"
                    : f.severity === 4 ? "warn"
                    : f.severity === 5 ? "ok" : "info";
        log(nivel, sev + " · " + f.text, m.sysid);
        break;
      }
    }
  }
});

udp.on("error", (e) => {
  console.error("  UDP:", e.message);
  if (e.code === "EADDRINUSE") {
    console.error("  El puerto " + CFG.udpPort + " ya está ocupado. ¿Hay otro puente corriendo?");
    process.exit(1);
  }
});

udp.bind(CFG.udpPort, () => {
  console.log("  MAVLink   escuchando  udp://0.0.0.0:" + CFG.udpPort + "  (solo lectura)");
});

/* Un enlace se da por caído si no llega nada en 3 s */
setInterval(() => {
  const ahora = Date.now();
  for (const v of flota.values()) {
    if (v.enlace && ahora - v.visto > 3000) {
      v.enlace = false;
      log("warn", "Telemetría perdida", v.sysid);
    }
  }
}, 1000);

/* ── Archivero de bitácoras ───────────────────────────────────────────── */
/* El puente guarda, cataloga y devuelve los registros; no los interpreta.
   Un .ulg lleva cientos de temas con esquema propio y decodificarlo aquí
   sería reescribir pyulog a medias. Para analizar están Flight Review y el
   propio GCS: esto es el archivero, y su trabajo es no perder nada. */

const EXT_LOG = new Set([".ulg", ".ulog", ".tlog", ".bin", ".log", ".px4log", ".csv", ".txt"]);

function nombreSeguro(s) {
  // Nada de rutas ni sorpresas: solo el nombre, con alfabeto cerrado.
  const base = path.basename(String(s || "")).replace(/[^A-Za-z0-9._-]/g, "_");
  return base.slice(0, 120) || "registro.bin";
}

function carpetaLog(sysid) {
  const n = Number(sysid);
  if (!Number.isInteger(n) || n < 0 || n > 255) return null;
  return path.join(CFG.logsDir, String(n));
}

function catalogo() {
  const salida = [];
  let dirs;
  try { dirs = fs.readdirSync(CFG.logsDir, { withFileTypes: true }); }
  catch (e) { return salida; }

  for (const d of dirs) {
    if (!d.isDirectory() || !Number.isInteger(Number(d.name))) continue;
    let archivos;
    try { archivos = fs.readdirSync(path.join(CFG.logsDir, d.name)); } catch (e) { continue; }
    for (const a of archivos) {
      try {
        const st = fs.statSync(path.join(CFG.logsDir, d.name, a));
        if (st.isFile()) salida.push({ sysid: Number(d.name), archivo: a, bytes: st.size, subido: st.mtimeMs });
      } catch (e) { /* desapareció entre readdir y stat; no es asunto nuestro */ }
    }
  }
  return salida.sort((x, y) => y.subido - x.subido);
}

function recibirLog(req, res, dir, sysid, archivo) {
  if (!EXT_LOG.has(path.extname(archivo).toLowerCase()))
    return json(res, 415, { error: "extensión no admitida: " + path.extname(archivo) });

  try { fs.mkdirSync(dir, { recursive: true }); }
  catch (e) { return json(res, 500, { error: e.message }); }

  const destino = path.join(dir, archivo);
  const salida = fs.createWriteStream(destino);
  let bytes = 0, abortado = false;

  req.on("data", (c) => {
    bytes += c.length;
    if (bytes > CFG.maxLog && !abortado) {
      abortado = true;
      salida.destroy();
      fs.unlink(destino, () => {});
      json(res, 413, { error: "el registro supera " + Math.round(CFG.maxLog / 1048576) + " MB" });
      req.destroy();
    }
  });
  req.pipe(salida);

  salida.on("finish", () => {
    if (abortado) return;
    log("info", "Bitácora recibida · " + archivo + " (" + (bytes / 1048576).toFixed(1) + " MB)", sysid);
    json(res, 200, { ok: true, archivo, bytes });
  });
  salida.on("error", (e) => { if (!abortado) json(res, 500, { error: e.message }); });
}

/* ── Fuentes de cámara ────────────────────────────────────────────────── */
/* Sin flujo real configurado la consola dibuja una vista representativa,
   rotulada como tal, para que el mosaico se pueda evaluar sin sacar las
   aeronaves. Con camaras.json presente, cada sysid puede apuntar a un flujo
   de verdad. Ver camaras.json.ejemplo. */

function camaras() {
  try { return JSON.parse(fs.readFileSync(path.join(__dirname, "camaras.json"), "utf8")); }
  catch (e) { return {}; }
}

/* ── API ──────────────────────────────────────────────────────────────── */

function json(res, code, obj) {
  res.writeHead(code, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(obj));
}

function api(req, res, ruta) {
  const p = ruta.split("/").filter(Boolean);          // ["api", "logs", ...]

  if (p[1] === "camaras" && req.method === "GET") return json(res, 200, { camaras: camaras() });
  if (p[1] !== "logs") return json(res, 404, { error: "ruta desconocida" });

  if (p.length === 2 && req.method === "GET") return json(res, 200, { logs: catalogo() });

  const dir = p.length >= 3 ? carpetaLog(p[2]) : null;
  if (!dir) return json(res, 400, { error: "sysid inválido" });

  if (p.length === 3 && req.method === "POST") {
    const q = req.url.indexOf("?");
    const params = new URLSearchParams(q >= 0 ? req.url.slice(q + 1) : "");
    return recibirLog(req, res, dir, Number(p[2]), nombreSeguro(params.get("archivo")));
  }

  if (p.length === 4) {
    const destino = path.join(dir, nombreSeguro(p[3]));
    if (req.method === "GET") {
      const fl = fs.createReadStream(destino);
      fl.on("error", () => json(res, 404, { error: "no existe" }));
      fl.once("open", () => res.writeHead(200, {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": 'attachment; filename="' + path.basename(destino) + '"'
      }));
      return fl.pipe(res);
    }
    if (req.method === "DELETE") {
      return fs.unlink(destino, (e) => e ? json(res, 404, { error: "no existe" })
                                         : json(res, 200, { ok: true }));
    }
  }
  json(res, 405, { error: "método no admitido" });
}

/* ── Servidor web para la consola ─────────────────────────────────────── */

const MIME = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8", ".png": "image/png", ".svg": "image/svg+xml",
  ".json": "application/json", ".ico": "image/x-icon"
};

const VENDOR = path.join(__dirname, "node_modules", "leaflet", "dist");

const web = http.createServer((req, res) => {
  let rel = decodeURIComponent(req.url.split("?")[0]);
  if (rel.startsWith("/api/")) return api(req, res, rel);
  if (rel === "/") rel = "/index.html";

  // Leaflet se sirve desde node_modules en vez de un CDN, para que la consola
  // levante sin internet. Las teselas sí necesitan red, salvo que se use un
  // juego local (ver README).
  let base = CFG.webRoot, sub = rel;
  if (rel.startsWith("/vendor/leaflet/")) {
    base = VENDOR;
    sub = rel.slice("/vendor/leaflet".length);
  }

  const destino = path.join(base, path.normalize(sub));
  if (!destino.startsWith(base)) { res.writeHead(403).end("403"); return; }

  fs.readFile(destino, (err, data) => {
    if (err) { res.writeHead(404, { "Content-Type": "text/plain" }).end("404"); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(destino)] || "application/octet-stream" });
    res.end(data);
  });
});
/* Un puerto ocupado no debe tumbar el proceso con un 'error' sin manejar:
   se avisa en claro y se sale con código, que es lo que espera quien lo lance
   desde un script o un servicio. */
function puertoOcupado(quien, puerto) {
  return (e) => {
    if (e.code === "EADDRINUSE") {
      console.error("\n  " + quien + ": el puerto " + puerto + " ya está ocupado.");
      console.error("  Cierra el otro puente, o cambia el puerto con la variable de entorno.\n");
    } else {
      console.error("  " + quien + ":", e.message);
    }
    process.exit(1);
  };
}

web.on("error", puertoOcupado("Consola", CFG.webPort));
web.listen(CFG.webPort, () => {
  console.log("  Consola   http://localhost:" + CFG.webPort + "/");
});

/* ── WebSocket hacia el navegador ─────────────────────────────────────── */

const wss = new WebSocketServer({ port: CFG.wsPort });
wss.on("error", puertoOcupado("WebSocket", CFG.wsPort));
console.log("  Datos     ws://localhost:" + CFG.wsPort + "/");

function difundir(obj) {
  const txt = JSON.stringify(obj);
  for (const c of wss.clients) if (c.readyState === 1) c.send(txt);
}

wss.on("connection", (ws) => {
  // Al conectar, el cliente recibe el estado completo de una vez
  ws.send(JSON.stringify({
    tipo: "inicial",
    flota: [...flota.values()],
    eventos: eventos.slice(-40)
  }));
});

setInterval(() => {
  if (!wss.clients.size) return;
  difundir({
    tipo: "telemetria",
    t: Date.now(),
    flota: [...flota.values()].map((v) => ({ ...v, estela: v.estela.slice(-300) }))
  });
}, Math.round(1000 / CFG.emitHz));

/* ── Persistencia opcional en MariaDB (XAMPP) ─────────────────────────── */

let pool = null;
if (CFG.db) {
  try {
    const mysql = require("mysql2/promise");
    pool = mysql.createPool({ ...CFG.dbConf, connectionLimit: 4, waitForConnections: true });
    console.log("  Histórico MariaDB " + CFG.dbConf.host + "/" + CFG.dbConf.database);

    setInterval(async () => {
      for (const v of flota.values()) {
        if (!v.enlace || v.lat === null) continue;
        try {
          await pool.execute(
            "INSERT INTO telemetria (sysid, t, lat, lon, alt_rel, alt_msl, vel_suelo," +
            " vel_aire, rumbo, bateria_pct, voltaje, satelites, modo, armado)" +
            " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            [v.sysid, new Date(), v.lat, v.lon, v.altRel, v.altMsl, v.velSuelo,
             v.velAire, v.rumbo, v.bateriaPct, v.voltaje, v.satelites, v.modo, v.armado ? 1 : 0]
          );
        } catch (e) {
          console.error("  MariaDB:", e.message);
        }
      }
    }, 1000);
  } catch (e) {
    console.error("  No se pudo iniciar MariaDB (" + e.message + ").");
    console.error("  El puente sigue sin histórico. Instala con:  npm install mysql2");
  }
}

/* ── Modo demostración ────────────────────────────────────────────────── */
/* Sin aeronave conectada no hay nada que ver, así que con --demo el puente
   sintetiza un vuelo. Sirve para probar la consola sin sacar la aeronave.  */

if (process.argv.includes("--demo")) {
  /* Cuatro aeronaves con perfiles distintos a propósito: sirven para ver el
     mosaico lleno, comprobar que cada una se distingue en el mapa y que los
     umbrales de aviso (batería, RSSI) se disparan de verdad. */
  const PERFILES = [
    { sysid: 1, nombre: "OTECH-01 · VTOL", tipo: "VTOL", modo: "MISSION",
      paso: 0.0016, alt: 120, vel: 18.4, bat0: 96, gasto: 44, rssi0: -58, sats: 18,
      fix: "RTK fijo", hdop: 0.7,
      ruta: [[20.7431,-100.4512],[20.7442,-100.4506],[20.7458,-100.4462],
             [20.7478,-100.4458],[20.7462,-100.4504],[20.7482,-100.4501],
             [20.7498,-100.4456],[20.7518,-100.4452],[20.7502,-100.4498],
             [20.7431,-100.4512]] },

    { sysid: 2, nombre: "OTECH-02 · Ala fija", tipo: "Ala fija", modo: "MISSION",
      paso: 0.0026, alt: 185, vel: 24.6, bat0: 88, gasto: 38, rssi0: -66, sats: 16,
      fix: "3D DGPS", hdop: 0.9,
      ruta: [[20.7560,-100.4390],[20.7612,-100.4318],[20.7618,-100.4300],
             [20.7566,-100.4372],[20.7572,-100.4354],[20.7624,-100.4282],
             [20.7630,-100.4264],[20.7578,-100.4336],[20.7560,-100.4390]] },

    { sysid: 3, nombre: "OTECH-03 · Multirrotor", tipo: "Multirrotor", modo: "AUTO.LOITER",
      paso: 0.0034, alt: 62, vel: 6.2, bat0: 41, gasto: 30, rssi0: -71, sats: 14,
      fix: "3D", hdop: 1.4,
      ruta: [[20.7352,-100.4618],[20.7368,-100.4602],[20.7372,-100.4578],
             [20.7360,-100.4560],[20.7340,-100.4562],[20.7330,-100.4584],
             [20.7336,-100.4608],[20.7352,-100.4618]] },

    { sysid: 4, nombre: "OTECH-04 · Multirrotor", tipo: "Multirrotor", modo: "AUTO.RTL",
      paso: 0.0021, alt: 95, vel: 11.8, bat0: 63, gasto: 34, rssi0: -84, sats: 11,
      fix: "3D", hdop: 2.1,
      ruta: [[20.7688,-100.4712],[20.7654,-100.4668],[20.7620,-100.4640],
             [20.7590,-100.4664],[20.7602,-100.4706],[20.7644,-100.4730],
             [20.7688,-100.4712]] }
  ];

  console.log("  Demo      " + PERFILES.length + " aeronaves sintéticas (sin vuelo real)");

  for (const p of PERFILES) {
    const v = aeronave(p.sysid);
    v.nombre = p.nombre; v.tipo = p.tipo; v.modo = p.modo; v.armado = true;
    v.wpTotal = p.ruta.length; v.fix = p.fix; v.hdop = p.hdop; v.satelites = p.sats;

    let d = Math.random() * (p.ruta.length - 1);
    setInterval(() => {
      d = (d + p.paso) % (p.ruta.length - 1);
      const i = Math.floor(d), t = d - i;
      const a = p.ruta[i], b = p.ruta[i + 1];

      v.visto = Date.now(); v.enlace = true;
      v.lat = a[0] + (b[0] - a[0]) * t;
      v.lon = a[1] + (b[1] - a[1]) * t;
      v.altRel = p.alt + Math.sin(d * 3) * 4;
      v.altMsl = 1804 + v.altRel;
      v.velSuelo = p.vel + Math.sin(d * 5) * (p.vel * 0.09);
      v.velAire = v.velSuelo + 2.8;
      v.ascenso = Math.cos(d * 3) * 0.6;
      v.rumbo = (Math.atan2(b[1] - a[1], b[0] - a[0]) * 180 / Math.PI + 360) % 360;
      v.bateriaPct = Math.max(5, Math.round(p.bat0 - (d / (p.ruta.length - 1)) * p.gasto));
      v.voltaje = 25.2 - (100 - v.bateriaPct) * 0.072;
      v.corriente = 14.2; v.consumo = Math.round((100 - v.bateriaPct) * 210);
      v.wpActual = i + 1;
      v.rssi = Math.round(p.rssi0 - Math.hypot((v.lat - p.ruta[0][0]) * 111320,
                                               (v.lon - p.ruta[0][1]) * 104000) / 1000 * 9);
      v.perdida = v.rssi < -90 ? 4.5 : 0.2;

      const u = v.estela[v.estela.length - 1];
      if (!u || Math.hypot((v.lat - u[0]) * 111320, (v.lon - u[1]) * 104000) > 8) {
        v.estela.push([v.lat, v.lon]);
        if (v.estela.length > 900) v.estela.shift();
      }
    }, 100);
  }

  const FRASES = [
    ["info", "INFO · Waypoint alcanzado"],
    ["ok",   "NOTICE · Fotografía capturada"],
    ["info", "INFO · Corrección RTCM recibida"],
    ["warn", "WARNING · Viento cruzado sobre el tramo"],
    ["warn", "WARNING · Enlace de telemetría degradado"],
    ["ok",   "NOTICE · Transición a vuelo horizontal"]
  ];
  setInterval(() => {
    const f = FRASES[Math.floor(Math.random() * FRASES.length)];
    log(f[0], f[1], PERFILES[Math.floor(Math.random() * PERFILES.length)].sysid);
  }, 4500);
}

console.log("");
console.log("  Torre OTECH — puente local");
console.log("  El mando permanece en el enlace RF. Esta capa solo observa.");
console.log("");

process.on("SIGINT", () => {
  console.log("\n  Cerrando.");
  udp.close(); wss.close(); web.close();
  if (pool) pool.end();
  process.exit(0);
});
