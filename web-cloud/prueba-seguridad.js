"use strict";
/**
 * Pruebas de seguridad del puente. Requiere el puente corriendo:
 *
 *     node bridge.js --demo        (en otra terminal)
 *     node prueba-seguridad.js
 *
 * Cada caso corresponde a un agujero que existió de verdad y se cerró. Están
 * aquí para que no vuelva ninguno sin que nadie se entere; una prueba de
 * seguridad sin el fallo original documentado envejece hasta ser ruido.
 */

const net = require("net");
const http = require("http");
const path = require("path");
const fs = require("fs");
const WebSocket = require("ws");

const WEB = Number(process.env.OTECH_WEB || 8080);
const WS  = Number(process.env.OTECH_WS  || 8081);
const AJENO = "https://sitio-malicioso.example";

let ok = 0, mal = 0;
function comprueba(t, cond, det) {
  if (cond) { ok++; console.log("  ok     " + t + (det ? "   " + det : "")); }
  else { mal++; console.log("  FALLO  " + t + (det ? "   " + det : "")); }
}
const titulo = (t) => console.log("\n" + t);

function pedir(opciones, cuerpo) {
  return new Promise((resolve) => {
    const req = http.request(Object.assign({ host: "127.0.0.1", port: WEB }, opciones), (res) => {
      let d = "";
      res.on("data", (c) => d += c);
      res.on("end", () => resolve({ estado: res.statusCode, cuerpo: d }));
    });
    req.on("error", () => resolve({ estado: 0, cuerpo: "" }));
    req.end(cuerpo);
  });
}

/* Petición cruda: el cliente http de Node normaliza la ruta y no dejaría
   enviar `//../`, que es justamente el vector que hay que probar. */
function crudo(lineaPeticion, conHost = true) {
  return new Promise((resolve) => {
    const cabeceras = (conHost ? "Host: localhost:" + WEB + "\r\n" : "") + "Connection: close\r\n";
    const s = net.connect(WEB, "127.0.0.1", () =>
      s.write(lineaPeticion + "\r\n" + cabeceras + "\r\n"));
    let d = "";
    s.on("data", (x) => d += x);
    s.on("close", () => resolve(d));
    s.on("error", () => resolve(""));
  });
}
const estado = (r) => (r.split("\r\n")[0] || "").trim();

function socket(origen) {
  return new Promise((resolve) => {
    const ws = new WebSocket("ws://127.0.0.1:" + WS + "/", origen ? { origin: origen } : {});
    const fin = (r) => { try { ws.close(); } catch (e) {} resolve(r); };
    ws.on("message", (m) => fin({ abierto: true, flota: (JSON.parse(m).flota || []).length }));
    ws.on("error", (e) => fin({ abierto: false, motivo: e.message }));
    setTimeout(() => fin({ abierto: false, motivo: "sin respuesta" }), 5000);
  });
}

(async function () {
  const vivo = await pedir({ method: "GET", path: "/" });
  if (vivo.estado !== 200) {
    console.error("\n  El puente no responde en el " + WEB + ". Arráncalo primero:\n" +
                  "      node bridge.js --demo\n");
    process.exit(1);
  }

  /* ── Fuga de archivos ─────────────────────────────────────────────────
     `//x` normalizaba a la ruta UNC `\\x` y path.join la dejaba salir del
     directorio web/; `startsWith(base)` sin separador daba por bueno un
     hermano con el mismo prefijo. Juntas, servían cualquier archivo de un
     directorio `web*` vecino.                                            */
  titulo("Fuga de archivos fuera de web/");

  const centinela = path.join(__dirname, "webPRUEBA");
  fs.mkdirSync(centinela, { recursive: true });
  fs.writeFileSync(path.join(centinela, "centinela.txt"), "CADENA-CENTINELA-NO-DEBE-SALIR");
  try {
    for (const t of ["GET //../webPRUEBA/centinela.txt HTTP/1.1",
                     "GET /\\../webPRUEBA/centinela.txt HTTP/1.1",
                     "GET ///../webPRUEBA/centinela.txt HTTP/1.1",
                     "GET //../../local/bridge.js HTTP/1.1"]) {
      const r = await crudo(t);
      comprueba("rechaza  " + t.split(" ")[1],
        !/CADENA-CENTINELA-NO-DEBE-SALIR/.test(r) && !/const dgram/.test(r),
        (r.split("\r\n")[0] || "").trim());
    }
  } finally {
    fs.rmSync(centinela, { recursive: true, force: true });
  }

  const noExiste = await pedir({ method: "GET", path: "/no-existe.html" });
  comprueba("una ruta legítima inexistente sigue dando 404, no 403",
    noExiste.estado === 404, String(noExiste.estado));

  /* ── CSRF ─────────────────────────────────────────────────────────────
     Sin comprobar Origin, cualquier web disparaba POST simples: escribir en
     el archivero y consumir la GPU. No hacían falta cookies.               */
  titulo("Origen cruzado (CSRF)");

  const chatAjeno = await pedir({
    method: "POST", path: "/api/agente/chat",
    headers: { "Content-Type": "text/plain", "Origin": AJENO }
  }, JSON.stringify({ mensaje: "hola" }));
  comprueba("POST al asistente desde origen ajeno → 403",
    chatAjeno.estado === 403, String(chatAjeno.estado));

  const subeAjeno = await pedir({
    method: "POST", path: "/api/logs/1?archivo=csrf.csv",
    headers: { "Content-Type": "text/plain", "Origin": AJENO }
  }, "datos inyectados");
  comprueba("subida de bitácora desde origen ajeno → 403",
    subeAjeno.estado === 403, String(subeAjeno.estado));

  const borraAjeno = await pedir({
    method: "DELETE", path: "/api/logs/1/lo-que-sea.ulg", headers: { "Origin": AJENO }
  });
  comprueba("borrado desde origen ajeno → 403",
    borraAjeno.estado === 403, String(borraAjeno.estado));

  /* ── DNS rebinding ────────────────────────────────────────────────────
     Sin validar Host, un dominio del atacante que resuelva a 127.0.0.1
     alcanzaba la API desde el navegador de la víctima, saltándose que el
     puerto solo escuche en la red local.                                   */
  titulo("Cabecera Host (DNS rebinding)");

  const hostAjeno = await pedir({ method: "GET", path: "/api/logs", headers: { "Host": "atacante.example" } });
  comprueba("Host desconocido → 403", hostAjeno.estado === 403, String(hostAjeno.estado));

  /* Sin la cabecera Host de verdad, no la que añade el ayudante. Un HTTP/1.0
     sin Host es legítimo pero rarísimo, y admitirlo dejaría una vía sin
     validar; se rechaza. */
  const sinHost = await crudo("GET /api/logs HTTP/1.0", false);
  comprueba("petición sin cabecera Host → rechazada",
    /403/.test(estado(sinHost)) && !/\[/.test(sinHost), estado(sinHost));

  /* ── WebSocket ────────────────────────────────────────────────────────
     Sin comprobar Origin, cualquier página abierta en el navegador del
     operador leía la telemetría completa, posiciones incluidas.            */
  titulo("Origen del WebSocket");

  const wsAjeno = await socket(AJENO);
  comprueba("suscripción desde origen ajeno rechazada",
    !wsAjeno.abierto, wsAjeno.motivo || "quedó abierta");

  /* ── El uso legítimo no se rompe ──────────────────────────────────── */
  titulo("Uso legítimo");

  comprueba("la consola se sirve", vivo.estado === 200);
  comprueba("leaflet desde node_modules",
    (await pedir({ method: "GET", path: "/vendor/leaflet/leaflet.js" })).estado === 200);
  comprueba("el catálogo de bitácoras responde",
    (await pedir({ method: "GET", path: "/api/logs" })).estado === 200);

  const propio = await pedir({
    method: "POST", path: "/api/agente/chat",
    headers: { "Content-Type": "application/json", "Origin": "http://localhost:" + WEB }
  }, JSON.stringify({ mensaje: "ping" }));
  comprueba("POST desde el mismo origen sí pasa", propio.estado === 200, String(propio.estado));

  const wsPropio = await socket(null);
  comprueba("cliente nativo sin Origin recibe telemetría",
    wsPropio.abierto, wsPropio.abierto ? wsPropio.flota + " aeronaves" : wsPropio.motivo);

  console.log("\n" + (mal === 0
    ? "Todo correcto. " + ok + " comprobaciones."
    : mal + " fallo(s) de " + (ok + mal) + "."));
  process.exit(mal === 0 ? 0 : 1);
})();
