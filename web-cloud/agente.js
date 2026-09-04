"use strict";
/**
 * Asistente de AeroHub Link — consultas en lenguaje natural sobre la flota.
 *
 *   pregunta ──▶ informe construido en código ──▶ Ollama (local) ──▶ respuesta
 *
 * Principio de diseño, y es el que gobierna todo este archivo:
 *
 *   EL JUICIO DE SEGURIDAD VIVE EN EL CÓDIGO, NO EN EL MODELO.
 *
 * Un modelo de 3B no decide si una batería al 30 % es preocupante. Eso lo
 * decide `revisar()` con los mismos umbrales que pinta la consola, y al modelo
 * se le entrega el hallazgo ya formado para que lo redacte y lo relacione. Así
 * el asistente y la interfaz nunca se contradicen, y una alucinación del modelo
 * no puede inventarse una alarma ni, peor, callarse una real.
 *
 * El asistente tampoco manda. No existe aquí ninguna ruta hacia la aeronave:
 * puede recomendar una acción, y la ejecuta una persona en la radio. Es la
 * hipótesis S-1 de OTECH-GCS-SW-001 aplicada a la capa de lenguaje.
 */

const CFG = {
  host:     process.env.OTECH_LLM_HOST  || "http://127.0.0.1:11434",
  modelo:   process.env.OTECH_LLM_MODEL || "llama3.2:latest",
  temp:     Number(process.env.OTECH_LLM_TEMP || 0.25),
  maxTok:   Number(process.env.OTECH_LLM_MAX  || 700),
  turnos:   6            // pares pregunta/respuesta que se conservan
};

/* ── Umbrales ─────────────────────────────────────────────────────────────
   Los mismos que usa web/index.html para colorear los instrumentos. Si
   cambian ahí, cambian aquí: dos criterios distintos en un mismo producto
   son un defecto, no una opción de configuración.                        */

const U = {
  bateriaCrit: 20,      // %
  bateriaAviso: 35,
  rssiCrit: -90,        // dBm
  rssiAviso: -75,
  satsCrit: 6,
  satsAviso: 9,
  hdopAviso: 2.0,
  perdidaAviso: 2.0,    // %
  enlaceMuerto: 3000    // ms sin trama
};

/* ── Hallazgos ────────────────────────────────────────────────────────── */

function revisar(v) {
  const h = [];
  const add = (grado, texto) => h.push({ grado, texto });

  if (!v.enlace) {
    add("CRÍTICO", "sin telemetría: no llega ninguna trama desde hace más de " +
                   (U.enlaceMuerto / 1000) + " s");
    return h;   // sin enlace, el resto de los datos están rancios
  }

  if (v.bateriaPct !== null) {
    if (v.bateriaPct < U.bateriaCrit)
      add("CRÍTICO", "batería al " + v.bateriaPct + " %, por debajo del mínimo de " + U.bateriaCrit + " %");
    else if (v.bateriaPct < U.bateriaAviso)
      add("AVISO", "batería al " + v.bateriaPct + " %, por debajo del umbral de aviso de " + U.bateriaAviso + " %");
  }

  if (v.rssi !== null) {
    if (v.rssi < U.rssiCrit)
      add("CRÍTICO", "RSSI " + v.rssi + " dBm, enlace de mando degradado por debajo de " + U.rssiCrit + " dBm");
    else if (v.rssi < U.rssiAviso)
      add("AVISO", "RSSI " + v.rssi + " dBm, margen de enlace reducido");
  }

  if (v.perdida !== null && v.perdida > U.perdidaAviso)
    add("AVISO", "pérdida de paquetes " + v.perdida.toFixed(1) + " %");

  if (v.satelites !== null) {
    if (v.satelites < U.satsCrit)
      add("CRÍTICO", "solo " + v.satelites + " satélites; la posición no es fiable");
    else if (v.satelites < U.satsAviso)
      add("AVISO", v.satelites + " satélites, constelación justa");
  }

  if (v.hdop !== null && v.hdop > U.hdopAviso)
    add("AVISO", "HDOP " + v.hdop.toFixed(1) + ", dilución de precisión alta");

  if (v.fix && /^(sin|no)/i.test(v.fix))
    add("CRÍTICO", "sin fijación GNSS (" + v.fix + ")");

  return h;
}

/* ── Estadística de vuelo ─────────────────────────────────────────────── */

function distancia(estela) {
  let d = 0;
  for (let i = 1; i < estela.length; i++) {
    const [a1, o1] = estela[i - 1], [a2, o2] = estela[i];
    d += Math.hypot((a2 - a1) * 111320,
                    (o2 - o1) * 111320 * Math.cos(a1 * Math.PI / 180));
  }
  return d;
}

function duracion(ms) {
  if (!ms || ms < 0) return "—";
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600), m = Math.floor(s / 60) % 60;
  return h ? h + " h " + m + " min" : m + " min " + (s % 60) + " s";
}

/* Extremos acumulados. bridge.js llama a esto una vez por segundo; guardar
   los máximos al vuelo evita tener que releer un histórico que puede no
   existir (la base de datos es opcional). */
function acumular(v) {
  if (!v.acum) v.acum = { desde: null, altMax: null, velMax: null, batMin: null, batMax: null };
  const a = v.acum;
  if (!v.enlace) { a.desde = null; return; }
  if (a.desde === null) a.desde = Date.now();
  if (v.altRel !== null)    a.altMax = a.altMax === null ? v.altRel : Math.max(a.altMax, v.altRel);
  if (v.velSuelo !== null)  a.velMax = a.velMax === null ? v.velSuelo : Math.max(a.velMax, v.velSuelo);
  if (v.bateriaPct !== null) {
    a.batMin = a.batMin === null ? v.bateriaPct : Math.min(a.batMin, v.bateriaPct);
    a.batMax = a.batMax === null ? v.bateriaPct : Math.max(a.batMax, v.bateriaPct);
  }
}

/* ── Construcción del informe ─────────────────────────────────────────── */

const n = (x, d) => (x === null || x === undefined || isNaN(x)) ? "—" : Number(x).toFixed(d === undefined ? 1 : d);
const tag = (s) => String(s).padStart(2, "0");

function fichaAeronave(v) {
  const L = [];
  const a = v.acum || {};
  // El nombre que publica la aeronave suele traer ya el tipo; no lo repetimos.
  const tipo = (v.tipo && v.tipo !== "—" && v.nombre.indexOf(v.tipo) === -1) ? " · " + v.tipo : "";
  L.push("[" + tag(v.sysid) + "] " + v.nombre + tipo + " · " + v.modo +
         (v.armado ? " · ARMADO" : " · desarmado") +
         (v.enlace ? " · enlace activo" : " · SIN ENLACE"));

  if (v.enlace) {
    L.push("   posición " + n(v.lat, 5) + ", " + n(v.lon, 5) +
           " · altura " + n(v.altRel, 0) + " m AGL (" + n(v.altMsl, 0) + " m AMSL)");
    L.push("   velocidad suelo " + n(v.velSuelo) + " m/s · aire " + n(v.velAire) +
           " m/s · vertical " + n(v.ascenso) + " m/s · rumbo " + n(v.rumbo, 0) + "°");
    L.push("   batería " + (v.bateriaPct === null ? "—" : v.bateriaPct + " %") +
           " (" + n(v.voltaje) + " V" + (v.consumo !== null ? ", " + v.consumo + " mAh consumidos" : "") + ")");
    L.push("   GNSS " + (v.fix || "—") + " · " + (v.satelites === null ? "—" : v.satelites) +
           " satélites · HDOP " + n(v.hdop) + " · RSSI " + (v.rssi === null ? "—" : v.rssi + " dBm") +
           " · pérdida " + n(v.perdida) + " %");
    if (v.wpTotal) L.push("   misión: waypoint " + v.wpActual + " de " + v.wpTotal);
    L.push("   acumulado: en el aire " + duracion(a.desde ? Date.now() - a.desde : 0) +
           " · recorrido " + (distancia(v.estela || []) / 1000).toFixed(2) + " km" +
           " · techo " + n(a.altMax, 0) + " m · vel. máx " + n(a.velMax) + " m/s" +
           " · batería mínima " + (a.batMin === null ? "—" : a.batMin + " %"));
  }

  const h = revisar(v);
  if (!h.length) L.push("   HALLAZGOS: ninguno");
  else {
    L.push("   HALLAZGOS:");
    for (const x of h) L.push("     - " + x.grado + ": " + x.texto);
  }
  return L.join("\n");
}

/* Alarmas de toda la flota, ya evaluadas. Se devuelven aparte porque NO
   viajan por el modelo: se muestran tal cual, antes de su respuesta. */
function alertas(flota) {
  const out = [];
  for (const v of flota) for (const h of revisar(v))
    if (h.grado === "CRÍTICO")
      out.push({ sysid: v.sysid, nombre: v.nombre, texto: h.texto });
  return out;
}

function informe(estado) {
  const { flota, eventos, logs } = estado;
  const P = [];

  P.push("== FLOTA · " + new Date().toISOString().replace("T", " ").slice(0, 19) + " UTC ==");
  P.push(flota.length + " aeronave(s) conocida(s), " +
         flota.filter((v) => v.enlace).length + " con enlace activo.");
  P.push("");

  /* Los críticos van arriba del todo, antes que ningún detalle. Un modelo
     pequeño atiende mucho mejor al principio del contexto que a su mitad, y
     enterrar la alarma entre fichas es pedirle que la pase por alto. */
  const crit = alertas(flota);
  P.push("== HALLAZGOS CRÍTICOS DE LA FLOTA ==");
  if (!crit.length) P.push("Ninguno.");
  else {
    P.push("HAY " + crit.length + " HALLAZGO(S) CRÍTICO(S). No los omitas ni los degrades a aviso:");
    for (const c of crit) P.push(" - [" + tag(c.sysid) + "] " + c.nombre + ": " + c.texto);
  }
  P.push("");

  for (const v of flota) { P.push(fichaAeronave(v)); P.push(""); }

  const ult = (eventos || []).slice(-14);
  P.push("== ÚLTIMOS EVENTOS MAVLINK (" + ult.length + " de " + (eventos || []).length + ") ==");
  if (!ult.length) P.push("Sin eventos registrados.");
  for (const e of ult) {
    const t = new Date(e.t).toISOString().slice(11, 19);
    P.push(" " + t + "  " + (e.sysid ? "[" + tag(e.sysid) + "] " : "[--] ") +
           e.nivel.toUpperCase() + "  " + e.texto);
  }
  P.push("");

  P.push("== BITÁCORAS ARCHIVADAS ==");
  if (!logs || !logs.length) P.push("El archivero está vacío.");
  else {
    const porSys = {};
    for (const l of logs) (porSys[l.sysid] = porSys[l.sysid] || []).push(l);
    for (const s of Object.keys(porSys)) {
      const g = porSys[s];
      const mb = g.reduce((a, l) => a + l.bytes, 0) / 1048576;
      P.push(" [" + tag(s) + "] " + g.length + " archivo(s), " + mb.toFixed(1) + " MB: " +
             g.slice(0, 6).map((l) => l.archivo).join(", ") + (g.length > 6 ? ", …" : ""));
    }
  }

  return P.join("\n");
}

/* ── Sistema ──────────────────────────────────────────────────────────── */

const SISTEMA = `Eres el asistente de AeroHub Link, la consola de supervisión de la
estación de tierra OTECH-GroundStation. Hablas español de México.

QUÉ ERES
Un analista que lee el informe de estado y responde sobre él: resúmenes de
vuelo, problemas, bitácoras, incidencias e inspecciones.

QUÉ NO ERES
No tienes ningún canal hacia las aeronaves y no puedes ejecutar nada. El mando
vive en el enlace de radio local y lo opera una persona. Si te piden armar,
cambiar de modo, despegar, aterrizar o retornar, NO digas que lo hiciste ni que
lo estás haciendo. Explica la acción concreta que el operador debe ejecutar en
la radio y por qué.

REGLAS
1. Usa SOLO los datos del informe. Si algo no está, di "no tengo ese dato".
   Nunca inventes cifras, matrículas, horas ni nombres de archivo.
2. Los HALLAZGOS ya vienen evaluados con los umbrales oficiales del sistema.
   Repórtalos tal como están. No inventes alarmas nuevas ni suavices las que
   aparecen.
3. Identifica cada aeronave por su etiqueta de dos dígitos y su nombre.
4. Responde breve y en prosa. Viñetas solo si de verdad hay una lista.
5. Números con sus unidades. No redondees a la baja una alarma.
6. Si la pregunta no es sobre la flota, dilo en una línea y ofrece ayuda.`;

/* ── Llamada al modelo ────────────────────────────────────────────────── */

/* Solo se acepta un nombre con la forma de una etiqueta de Ollama. No es
   defensa contra un usuario malicioso —quien alcanza este puerto ya puede
   pedir lo que quiera— sino contra un valor mal formado que acabaría en el
   cuerpo de la petición al demonio. */
const NOMBRE_MODELO = /^[A-Za-z0-9][A-Za-z0-9._\/-]{0,60}(:[A-Za-z0-9._-]{1,40})?$/;

async function *preguntar(mensaje, historial, estado, señal, modelo) {
  const usar = (modelo && NOMBRE_MODELO.test(modelo)) ? modelo : CFG.modelo;
  const brief = informe(estado);

  /* Las alarmas salen ANTES que el modelo y sin pasar por él.
     Motivo, medido: llama3.2 respondió "no hay problemas críticos" teniendo
     un RSSI de -92 dBm en el informe, y de paso inventó una pérdida de GNSS
     inexistente. Un modelo de 3B no puede ser el canal de alarma de una
     estación de control. Aquí solo comenta; la alarma la emite el código. */
  const crit = alertas(estado.flota || []);
  if (crit.length) yield { alertas: crit };

  const mensajes = [
    { role: "system", content: SISTEMA },
    { role: "system", content: "INFORME DE ESTADO (generado por el sistema, es la única fuente de verdad):\n\n" + brief }
  ];
  for (const t of (historial || []).slice(-CFG.turnos * 2)) {
    if (t && (t.role === "user" || t.role === "assistant") && typeof t.content === "string")
      mensajes.push({ role: t.role, content: t.content.slice(0, 4000) });
  }
  mensajes.push({ role: "user", content: String(mensaje).slice(0, 4000) });

  const r = await fetch(CFG.host + "/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model: usar,
      messages: mensajes,
      stream: true,
      think: false,                 // los modelos de razonamiento gastarían el presupuesto pensando
      options: { temperature: CFG.temp, num_predict: CFG.maxTok }
    }),
    signal: señal
  });

  if (!r.ok) throw new Error("Ollama respondió " + r.status + " " + (await r.text()).slice(0, 200));

  /* Ollama devuelve NDJSON: un objeto por línea. Un fragmento de red puede
     partir una línea por la mitad, así que se acumula hasta el salto. */
  const dec = new TextDecoder();
  let resto = "";
  for await (const trozo of r.body) {
    resto += dec.decode(trozo, { stream: true });
    let i;
    while ((i = resto.indexOf("\n")) >= 0) {
      const linea = resto.slice(0, i).trim();
      resto = resto.slice(i + 1);
      if (!linea) continue;
      let j;
      try { j = JSON.parse(linea); } catch (e) { continue; }
      if (j.message && j.message.content) yield { texto: j.message.content };
      if (j.done) {
        yield { fin: true, tokens: j.eval_count || 0,
                velocidad: j.eval_duration ? j.eval_count / (j.eval_duration / 1e9) : null };
        return;
      }
    }
  }
}

async function modelos() {
  const r = await fetch(CFG.host + "/api/tags");
  if (!r.ok) throw new Error("Ollama respondió " + r.status);
  const j = await r.json();
  return (j.models || []).map((m) => ({
    nombre: m.name,
    params: m.details && m.details.parameter_size,
    gb: +(m.size / 1073741824).toFixed(1)
  }));
}

module.exports = { CFG, U, revisar, alertas, acumular, informe, fichaAeronave,
                   distancia, duracion, preguntar, modelos };
