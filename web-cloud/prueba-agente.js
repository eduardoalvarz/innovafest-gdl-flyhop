"use strict";
/**
 * Pruebas del asistente.
 *
 * Lo que se prueba aquí es el juicio de seguridad, que vive en código y por
 * tanto es determinista. La calidad de la prosa del modelo no se prueba: no
 * es reproducible y, por diseño, tampoco es donde vive ninguna alarma.
 */

const a = require("./agente");

let ok = 0, mal = 0;
function comprueba(titulo, condicion, detalle) {
  if (condicion) { ok++; console.log("  ok     " + titulo + (detalle ? "   " + detalle : "")); }
  else { mal++; console.log("  FALLO  " + titulo + (detalle ? "   " + detalle : "")); }
}
function titulo(t) { console.log("\n" + t); }

function nave(extra) {
  return Object.assign({
    sysid: 1, nombre: "OTECH-01", tipo: "VTOL", modo: "MISSION", armado: true, enlace: true,
    lat: 20.74, lon: -100.45, altRel: 100, altMsl: 1900,
    velSuelo: 15, velAire: 18, ascenso: 0, rumbo: 90,
    bateriaPct: 80, voltaje: 24, corriente: 12, consumo: 3000,
    satelites: 16, fix: "3D", hdop: 0.8, rssi: -60, perdida: 0.2,
    wpActual: 2, wpTotal: 10, estela: [],
    acum: { desde: Date.now() - 60000, altMax: 105, velMax: 16, batMin: 80, batMax: 96 }
  }, extra || {});
}

/* ── Umbrales ───────────────────────────────────────────────────────────── */
titulo("Umbrales de hallazgo");

comprueba("una aeronave sana no genera hallazgos",
  a.revisar(nave()).length === 0);

comprueba("batería 34 % es AVISO",
  a.revisar(nave({ bateriaPct: 34 })).some((h) => h.grado === "AVISO" && /batería/.test(h.texto)));

comprueba("batería 19 % es CRÍTICO",
  a.revisar(nave({ bateriaPct: 19 })).some((h) => h.grado === "CRÍTICO" && /batería/.test(h.texto)));

comprueba("batería justo en el umbral (35 %) no avisa",
  a.revisar(nave({ bateriaPct: 35 })).length === 0);

comprueba("RSSI -76 dBm es AVISO",
  a.revisar(nave({ rssi: -76 })).some((h) => h.grado === "AVISO" && /RSSI/.test(h.texto)));

comprueba("RSSI -92 dBm es CRÍTICO",
  a.revisar(nave({ rssi: -92 })).some((h) => h.grado === "CRÍTICO" && /RSSI/.test(h.texto)));

comprueba("5 satélites es CRÍTICO",
  a.revisar(nave({ satelites: 5 })).some((h) => h.grado === "CRÍTICO" && /satélite/.test(h.texto)));

comprueba("HDOP 2.4 es AVISO",
  a.revisar(nave({ hdop: 2.4 })).some((h) => h.grado === "AVISO" && /HDOP/.test(h.texto)));

comprueba("sin enlace es CRÍTICO y silencia el resto",
  (function () {
    const h = a.revisar(nave({ enlace: false, bateriaPct: 5, rssi: -99 }));
    return h.length === 1 && h[0].grado === "CRÍTICO" && /telemetría/.test(h[0].texto);
  })(),
  "los datos rancios no deben generar alarmas propias");

/* ── Canal de alarma ────────────────────────────────────────────────────── */
titulo("El canal de alarma no pasa por el modelo");

const flotaMixta = [
  nave({ sysid: 1, nombre: "OTECH-01" }),
  nave({ sysid: 3, nombre: "OTECH-03", bateriaPct: 11 }),
  nave({ sysid: 4, nombre: "OTECH-04", rssi: -94 })
];

const al = a.alertas(flotaMixta);
comprueba("alertas() recoge los dos críticos y ninguno más",
  al.length === 2, JSON.stringify(al.map((x) => x.sysid)));
comprueba("cada alerta trae sysid, nombre y texto",
  al.every((x) => x.sysid && x.nombre && x.texto));

/* ── Informe ────────────────────────────────────────────────────────────── */
titulo("Informe entregado al modelo");

const inf = a.informe({ flota: flotaMixta, eventos: [], logs: [] });

comprueba("los críticos aparecen antes que las fichas",
  inf.indexOf("HALLAZGOS CRÍTICOS") < inf.indexOf("[01]"),
  "un modelo pequeño atiende al principio del contexto");

comprueba("el informe nombra los dos críticos",
  /\[03\]/.test(inf.slice(inf.indexOf("HALLAZGOS CRÍTICOS"), inf.indexOf("[01]"))) &&
  /\[04\]/.test(inf.slice(inf.indexOf("HALLAZGOS CRÍTICOS"), inf.indexOf("[01]"))));

comprueba("con flota sana el informe dice Ninguno",
  /HALLAZGOS CRÍTICOS DE LA FLOTA ==\nNinguno\./.test(
    a.informe({ flota: [nave()], eventos: [], logs: [] })));

comprueba("no se repite el tipo cuando el nombre ya lo lleva",
  !/OTECH-01 · VTOL · VTOL/.test(a.fichaAeronave(nave({ nombre: "OTECH-01 · VTOL" }))));

comprueba("el informe no filtra la estela completa al modelo",
  !/estela/i.test(inf), "900 puntos de estela llenarían el contexto sin aportar nada");

/* ── Flota grande ───────────────────────────────────────────────────────── */
titulo("Degradación con una flota que no cabe en el contexto");

const grande = [];
for (let i = 1; i <= 14; i++) grande.push(nave({ sysid: i, nombre: "OTECH-" + String(i).padStart(2, "0"),
                                                 bateriaPct: (i === 3 || i === 9) ? 12 : 80 }));
const infG = a.informe({ flota: grande, eventos: [], logs: [] });
const bloqueCrit = infG.slice(infG.indexOf("HALLAZGOS CRÍTICOS"),
                              infG.indexOf("== ", infG.indexOf("HALLAZGOS CRÍTICOS") + 5));

comprueba("los dos críticos están en el bloque de críticos",
  /\[03\]/.test(bloqueCrit) && /\[09\]/.test(bloqueCrit));

comprueba("las aeronaves con hallazgo conservan ficha completa",
  /^\[03\] .*\n(.*\n)*?   HALLAZGOS:/m.test(infG) && /^\[09\]/m.test(infG));

comprueba("las sanas sobrantes se resumen en vez de truncarse en silencio",
  /AERONAVE\(S\) SIN HALLAZGOS, EN RESUMEN/.test(infG));

/* 2.35 car/token es una medida real: se tokenizó el informe con llama3.2 y se
   comparó. La cifra habitual de 3.4 subestimaba el coste un 45 %, porque el
   español técnico con tildes, cifras y unidades se parte mucho más que el
   inglés corriente. */
const CAR_POR_TOKEN = 2.35;
const tokG = Math.round(infG.length / CAR_POR_TOKEN);
comprueba("el informe deja sitio a sistema, historial y respuesta en 8192",
  tokG + 388 + 1500 + 700 < 8192,
  tokG + " tok de informe + 388 sistema + 1500 historial + 700 respuesta");

comprueba("ninguna aeronave desaparece del informe",
  (function () {
    for (let i = 1; i <= 14; i++)
      if (infG.indexOf("[" + String(i).padStart(2, "0") + "]") === -1) return false;
    return true;
  })());

/* ── Estadística ────────────────────────────────────────────────────────── */
titulo("Cálculo de trayecto");

const cuadra = [[20.7400, -100.4500], [20.7409, -100.4500]];   // ~100 m al norte
comprueba("distancia de un tramo norte-sur ≈ 100 m",
  Math.abs(a.distancia(cuadra) - 100) < 2, a.distancia(cuadra).toFixed(1) + " m");

comprueba("distancia de una estela vacía es 0", a.distancia([]) === 0);
comprueba("duracion() formatea horas", /^1 h 1 min$/.test(a.duracion(3660000)), a.duracion(3660000));

/* ── Acumulador ─────────────────────────────────────────────────────────── */
titulo("Extremos acumulados");

const v = nave({ acum: undefined, altRel: 50, velSuelo: 10, bateriaPct: 90 });
a.acumular(v);
v.altRel = 120; v.velSuelo = 4; v.bateriaPct = 70;
a.acumular(v);
v.altRel = 80; v.velSuelo = 22; v.bateriaPct = 85;
a.acumular(v);
comprueba("techo es el máximo", v.acum.altMax === 120, String(v.acum.altMax));
comprueba("velocidad máxima es el máximo", v.acum.velMax === 22, String(v.acum.velMax));
comprueba("batería mínima es el mínimo", v.acum.batMin === 70, String(v.acum.batMin));

const w = nave({ acum: undefined, enlace: false });
a.acumular(w);
comprueba("sin enlace no arranca el cronómetro", w.acum.desde === null);

/* ── Resultado ──────────────────────────────────────────────────────────── */
console.log("\n" + (mal === 0
  ? "Todo correcto. " + ok + " comprobaciones."
  : mal + " fallo(s) de " + (ok + mal) + "."));
process.exit(mal === 0 ? 0 : 1);
