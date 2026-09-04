# AeroHub Link — despliegue local

Capa de supervisión para OTECH-GroundStation, corriendo enteramente en tu máquina.

```
Aeronave ──RF──▶ Radio SIYI / GCS escritorio ──UDP 14550──▶ bridge.js ──WS 8081──▶ navegador
    PX4              (reenvío MAVLink)                          │
                                                                └──▶ MariaDB (opcional)
```

**El mando en tiempo real nunca pasa por aquí.** El socket UDP es de solo lectura
y el puente jamás llama a `send()`. Armado, cambio de modo y retorno se ejecutan
desde la radio, conforme a la hipótesis **S‑1** de OTECH‑GCS‑SW‑001.

---

## Arranque

```bash
cd cloud/local
npm install
npm start
```

Abre **http://localhost:8080/**

Para probar la consola sin sacar nada a volar, con **cuatro aeronaves
sintéticas** de perfiles distintos (VTOL, ala fija y dos multirrotores; una
con la batería en ámbar y otra con el RSSI en rojo, para que los umbrales de
aviso se vean disparados de verdad):

```bash
npm run demo
```

## Las cuatro vistas

El conmutador de la barra superior cambia el centro de la consola:

- **Mapa** — situación de toda la flota, instrumentos de la aeronave elegida y
  su cámara en un recuadro. Todas las aeronaves se dibujan siempre; la elegida
  lleva anillo y estela gruesa, las demás quedan atenuadas.
- **Cámaras** — mosaico con una baldosa por aeronave, todas a la vez, cada una
  con su altura, velocidad, rumbo y batería sobre la imagen.
- **Bitácoras** — el archivero de registros de vuelo.
- **Asistente** — consultas en lenguaje natural sobre todo lo anterior.

Cada aeronave recibe un **color y una etiqueta de dos dígitos** derivados de su
sysid, iguales en el mapa, en las pastillas de flota, en el mosaico y en la
bitácora. Es lo que permite seguir cuatro aeronaves sin leer un solo nombre.

### Puertos

| Puerto | Uso |
|--------|-----|
| 14550/udp | Entrada MAVLink desde la estación |
| 8081/tcp | WebSocket de datos hacia el navegador |
| 8080/tcp | Consola web |

Se cambian con `OTECH_UDP`, `OTECH_WS`, `OTECH_WEB`.

---

## Conectar tu estación

En OTECH-GroundStation: **Ajustes ▸ MAVLink ▸ reenvío**, activa el reenvío y
pon el destino. Corresponde a `forwardMavlink` y `forwardMavlinkHostName` en
`src/Settings/MavlinkSettings.cc`; **no hay que recompilar nada**.

- **GCS de escritorio, misma máquina:** `127.0.0.1:14550`
- **Radio SIYI:** la IP de tu PC en la red de la radio, p. ej. `192.168.1.31:14550`
  (permite el puerto en el firewall de Windows para redes privadas)

Si la consola dice *«Sin telemetría»*, el puente está bien pero no llega nada:
revisa el reenvío y el firewall.

---

## Cámaras

### Lo que ves hoy es una vista representativa

Mientras no haya un flujo declarado, cada baldosa **dibuja** el terreno que
sobrevuela esa aeronave: las parcelas se desplazan con su posición real y giran
con su rumbo, y la bruma aumenta con la altura. Responde al vuelo, pero **no es
imagen de la cámara**, y por eso lleva el rótulo `SIMULADO` en todo momento.
Sirve para dimensionar el mosaico, validar la distribución y enseñar la consola
sin sacar las aeronaves.

### Conectar video real

Copia `camaras.json.ejemplo` a `camaras.json`. Cada clave es un sysid:

```json
{ "1": { "tipo": "mjpeg", "url": "http://127.0.0.1:8090/otech01.mjpg" } }
```

Con una entrada presente, esa baldosa cambia el lienzo por el flujo y el rótulo
pasa a `EN VIVO`. Recarga la página tras editar el archivo.

| tipo | Cómo se pinta | Cuándo usarlo |
|------|---------------|---------------|
| `mjpeg` | `<img>` | Lo más rápido de montar. `ffmpeg` convierte el RTSP y ya. Retardo de 1-3 s y ancho de banda alto. |
| `archivo` | `<video>` | Un `.mp4`/`.webm` en `web/assets/` para ensayos y demostraciones. |

**RTSP y HLS no los reproduce el navegador por sí solo.** Para retardo por
debajo del segundo hace falta un repetidor WebRTC delante — [MediaMTX], un
binario suelto bajo Apache-2.0, toma el RTSP de la cámara y lo publica como
WebRTC. Es la ruta recomendada para supervisión.

Con todo, el video en la nube sigue siendo observación: **no habilita pilotar
contra la imagen**. El retardo de red es variable y no acotado, y eso no cambia
por que la imagen se vea fluida.

[MediaMTX]: https://github.com/bluenviron/mediamtx

---

## Asistente en lenguaje natural

Vista **Asistente**. Pregunta en español sobre el estado de la flota, los
problemas abiertos, los resúmenes de vuelo, las incidencias, las inspecciones
y el archivero de bitácoras.

Corre sobre **[Ollama] en tu máquina**. Nada de lo que escribes sale a
internet, y el asistente ve exactamente el mismo estado que pinta la consola —
no hay una fuente de verdad paralela que pueda desincronizarse.

```bash
ollama serve            # si no está ya corriendo como servicio
ollama pull llama3.2    # 1.9 GB
```

| Variable | Por omisión | Qué hace |
|----------|-------------|----------|
| `OTECH_LLM_HOST` | `http://127.0.0.1:11434` | Dónde escucha Ollama |
| `OTECH_LLM_MODEL` | `llama3.2:latest` | Modelo por omisión |
| `OTECH_LLM_TEMP` | `0.25` | Temperatura |
| `OTECH_LLM_MAX` | `700` | Tope de tokens por respuesta |
| `OTECH_LLM_CTX` | `8192` | Ventana de contexto que se le pide al modelo |
| `OTECH_LLM_FICHAS` | `4200` | Presupuesto de caracteres para las fichas detalladas |

El selector del pie del chat permite cambiar de modelo sin reiniciar.

El panel es translúcido para que la flota se siga viendo moverse por debajo.
La transparencia va en el panel, no en los mensajes: cada burbuja conserva su
propio fondo, así que se ve el mapa **entre** los mensajes y no a través de
ellos. El compositor y el aviso de «no manda» se quedan sólidos. Si sobre un
ortomosaico cargado una respuesta larga cuesta de leer, el botón del círculo
mitad-lleno de la barra superior opaca el panel, y la elección se recuerda.

[Ollama]: https://ollama.com

### El juicio de seguridad vive en el código, no en el modelo

Es la decisión de diseño que gobierna todo `agente.js`, y no es teórica.
Durante el desarrollo, con un RSSI de **-92 dBm** presente en el informe,
llama3.2 respondió *«no hay problemas críticos en la flota»* y acto seguido se
inventó una pérdida de GNSS que no existía. Un modelo de 3B no puede ser el
canal de alarma de una estación de control.

Así que no lo es:

- **`revisar()` evalúa los umbrales**, los mismos que colorean los
  instrumentos de la consola. Batería < 20 % crítico y < 35 % aviso; RSSI
  < -90 dBm crítico y < -75 dBm aviso; menos de 6 satélites crítico; HDOP > 2
  aviso. Si cambian ahí, cambian aquí: dos criterios distintos en un mismo
  producto son un defecto, no una opción.
- **Las alarmas críticas se emiten antes que el modelo y sin pasar por él.**
  Aparecen en una tarjeta roja propia, separada de la burbuja de la respuesta.
  Lo que dice el sistema y lo que dice el modelo no se mezclan nunca en el
  mismo bloque.
- **Los hallazgos van al principio del informe**, antes que ninguna ficha. Un
  modelo pequeño atiende mucho mejor al inicio del contexto que a su mitad.

Con eso, la prosa del modelo pasó a coincidir con la alarma. Pero la garantía
no es que coincida: es que **la tarjeta sale igual aunque el modelo se
equivoque**.

### Cuánto cuesta un informe, medido

Un **token** es el trozo de texto que el modelo procesa de una vez: ni una
letra ni una palabra, sino algo intermedio que sale de comprimir el corpus de
entrenamiento. Todo lo que entra y sale se cuenta en tokens, y la ventana de
contexto es un techo duro.

Tokenizando con llama3.2 en esta máquina:

| Texto | Caracteres | Tokens |
|-------|-----------:|-------:|
| `hola` | 4 | 2 |
| `aeronave` | 8 | 3 |
| `batería` | 8 | 4 |
| `OTECH-03` | 8 | 4 |
| `El multirrotor tiene la batería al treinta por ciento.` | 55 | 18 |
| **El informe completo, 4 aeronaves** | **3 490** | **1 483** |

Salen **2.35 caracteres por token**. La cifra que se cita habitualmente, 3.5-4,
vale para inglés corriente; el español técnico con tildes, cifras, unidades y
guiones se parte mucho más. Conviene medirlo y no suponerlo: la primera
estimación de este proyecto usó 3.4 y **subestimó el coste un 45 %**.

Costes reales medidos:

| Pieza | Tokens |
|-------|-------:|
| Prompt de sistema | 388 |
| Informe, 4 aeronaves | 1 483 |
| Informe, 14 aeronaves | 2 232 |
| Respuesta reservada | 700 |

### Flotas grandes

Ollama carga llama3.2 con **4096 tokens** de contexto por omisión. Con el
sistema, un informe de 4 aeronaves, algo de historial y la respuesta, eso ya
queda al filo; con la flota crecida, se desborda. Y Ollama **recorta en
silencio**: nadie se entera de que el modelo dejó de ver media flota.

Dos medidas. El puente pide **8192 tokens** explícitamente, y si aun así el
informe crece, las aeronaves **sin hallazgos** pasan a una línea resumida
mientras las que tienen aviso o crítico conservan su ficha completa y van
primero. El informe declara cuántas resumió, para que el modelo sepa que no lo
está viendo todo.

Con 14 aeronaves: ~2 070 tokens de informe, ninguna desaparece, y quedan más
de 3 500 tokens libres.

### El asistente no manda

No existe ninguna ruta desde el asistente hacia las aeronaves. Si le pides
armar, despegar, cambiar de modo o retornar, **no lo hace y no dice que lo
haya hecho**: describe la acción que debe ejecutar el operador en la radio y
por qué. Es la hipótesis S-1 aplicada a la capa de lenguaje, por las mismas
razones por las que el socket UDP nunca llama a `send()`.

Un modelo de lenguaje interpretando «bájalo» y transmitiendo un comando añade
un modo de fallo —la mala interpretación— que ninguna evaluación de seguridad
de este sistema contempla hoy.

### Qué esperar de un modelo pequeño

llama3.2 de 3B da unos **56 tok/s** en esta máquina; una respuesta típica tarda
de 3 a 15 segundos. Es bueno redactando y relacionando datos que ya tiene
delante, y flojo razonando por su cuenta: en pruebas llegó a llamar «1.4 %» a
un HDOP, que no tiene unidades. Trátalo como un redactor con el informe en la
mano, no como un analista.

`qwen3-vl:8.8B` también está disponible y razona mejor, pero da 20 tok/s y es
un modelo de razonamiento: gasta el presupuesto de tokens en pensar antes de
responder. Para chat interactivo, llama3.2 es la elección.

### API

| Método | Ruta | Qué hace |
|--------|------|----------|
| `GET` | `/api/agente` | Estado de Ollama, modelo activo, catálogo y umbrales |
| `GET` | `/api/agente/informe` | El informe exacto que se le entrega al modelo |
| `POST` | `/api/agente/chat` | Pregunta; responde por SSE, token a token |

`/api/agente/informe` es la herramienta de diagnóstico: si una respuesta te
sorprende, mira primero qué vio el modelo.

Va por SSE y no por el WebSocket de telemetría a propósito: una respuesta
larga bloquearía las tramas de vuelo, y esas tienen prioridad sobre cualquier
conversación.

---

## Bitácoras de vuelo

Vista **Bitácoras**: eliges la aeronave, arrastras los registros y quedan
guardados en `logs/<sysid>/`. La tabla los lista con tamaño y fecha, y permite
descargarlos o borrarlos.

Extensiones admitidas: `.ulg` `.ulog` `.tlog` `.bin` `.px4log` `.csv` `.log`
`.txt`. Tope de 512 MB por archivo, ajustable con `OTECH_MAX_LOG` (en MB).

El puente **guarda y cataloga; no interpreta**. Un `.ulg` lleva cientos de temas
con esquema propio y decodificarlo aquí sería reescribir pyulog a medias. Para
analizar están [Flight Review] y el propio GCS; esto es el archivero, y su
trabajo es no perder nada.

Los nombres se sanean antes de tocar el disco: solo el nombre base, alfabeto
cerrado y sysid validado, de modo que un `../../../` en el nombre no sale de
`logs/`. Está comprobado.

[Flight Review]: https://review.px4.io/

### API

| Método | Ruta | Qué hace |
|--------|------|----------|
| `GET` | `/api/logs` | Catálogo completo |
| `POST` | `/api/logs/<sysid>?archivo=<nombre>` | Sube el cuerpo tal cual |
| `GET` | `/api/logs/<sysid>/<archivo>` | Descarga |
| `DELETE` | `/api/logs/<sysid>/<archivo>` | Borra, sin papelera |
| `GET` | `/api/camaras` | Configuración de flujos |

---

## Varias aeronaves

No hace falta configurar nada: el puente indexa por **sysid** y da de alta cada
aeronave que aparece en el enlace. Si tu estación reenvía el tráfico de varias,
salen todas.

Todas comparten el puerto 14550, y el analizador mantiene un estado por origen
UDP, así que dos estaciones distintas reenviando a la vez tampoco se pisan.

---

## Histórico en MariaDB (XAMPP)

Opcional. Sin esto el puente funciona igual, solo que sin memoria.

```bash
D:\xampp\mysql\bin\mysql.exe -u root < schema.sql
```

Luego arranca con la persistencia activa:

```bash
set OTECH_DB=1
npm start
```

Variables: `OTECH_DB_HOST`, `OTECH_DB_PORT`, `OTECH_DB_USER`, `OTECH_DB_PASS`,
`OTECH_DB_NAME`. Escribe una fila por segundo y aeronave — unas 86 000 filas
al día por aeronave. La tabla va particionada por fecha para que purgar sea
soltar una partición y no un `DELETE` que bloquea.

La vista `resumen_diario` da techo, velocidad máxima y batería mínima por día,
que es la forma de bitácora que suele pedir la autoridad.

---

## Sobre Apache y PHP

Apache puede servir la consola perfectamente, pero **PHP no sirve como puente**:
bajo `mod_php` cada petición vive y muere sola, y aquí hace falta un proceso
permanente que sostenga un socket UDP y varios WebSocket abiertos. Es la misma
razón por la que esto no cabía en Vercel. Node hace ese trabajo en un archivo.

Si prefieres que Apache sirva la parte estática, apunta un alias a `web/` y deja
el puente en el 8081; la consola solo necesita alcanzar ese WebSocket.

---

## Cartografía

Solo fuentes de uso libre, también comercial. No hay ninguna capa con términos
restrictivos ni que exija clave.

| Capa | Fuente | Licencia | Nota |
|------|--------|----------|------|
| Calles | OpenStreetMap | Datos ODbL | Atribución obligatoria; uso moderado |
| Relieve | OpenTopoMap | CC-BY-SA (OSM + SRTM) | Útil para conciencia del terreno |
| Propio | `web/tiles/` | Tuya | Ver `web/tiles/LEEME.md` |

Los dos servicios públicos corren sobre **infraestructura donada** y su política
pide uso moderado: valen para un puesto de operación, no para repartir la consola
entre muchos clientes.

### Satélite gratuito: el tuyo

No existe imagen satelital de alta resolución que sea gratis y comercialmente
libre. La que sí lo es, es la que tú produces: vuelas levantamientos, así que
generas ortomosaicos mejores y más actuales que cualquier mapa base público.

```bash
gdal2tiles.py --xyz -z 14-21 ortomosaico.tif web/tiles/
```

El `--xyz` no es opcional: sin él GDAL escribe TMS, con la `y` invertida.

### Vuelo sin internet

Con `web/tiles/` poblado la consola funciona aislada — Leaflet se sirve desde
`node_modules` y las teselas desde disco. Lo único que seguiría buscando red son
las tipografías; descarga los `.woff2` a `web/assets/` si operas sin señal.

Alternativa: reaprovechar la caché de teselas que el propio GCS ya mantiene
(`src/QtLocationPlugin/QGCCachedTileSet`).

---

## Seguridad

### Cerrado

Cuatro agujeros encontrados en una revisión y corregidos. Cada uno tiene su
prueba de regresión en `prueba-seguridad.js`.

| Fallo | Qué permitía | Cierre |
|-------|--------------|--------|
| **Fuga de archivos** | `GET //../webSECRETO/x` devolvía 200 con el contenido. `//x` normaliza en Windows a la ruta UNC `\\x` y `path.join` la dejaba salir de `web/`; encima, `startsWith(base)` sin separador daba por bueno un hermano con el mismo prefijo. | `rutaSegura()`: colapsa los separadores iniciales, resuelve con `path.resolve` y compara contra `base + separador` |
| **CSRF** | Cualquier web abierta en el navegador del operador podía subir bitácoras y disparar inferencias. Sin cookies de por medio: no hay sesión que robar, basta con que la petición salga de dentro de la red. | Se valida `Origin` |
| **DNS rebinding** | Un dominio del atacante que resolviera a `127.0.0.1` alcanzaba la API, saltándose que el puerto solo escuche en local. | Se valida `Host` contra una lista de la máquina |
| **WebSocket abierto** | Cualquier página leía la telemetría completa, posiciones incluidas. | `verifyClient` con las mismas dos comprobaciones |

Si accedes a la consola por un nombre propio (no `localhost` ni una IP de esta
máquina), decláralo en `OTECH_HOSTS`, separado por comas.

### Abierto — y esto importa

Lo anterior cierra el ataque **desde el navegador**. No cierra el de alguien
que ya está en tu red.

- **No hay autenticación.** Cualquiera en la red que sepa la dirección puede,
  con `curl`, leer telemetría, descargar y borrar bitácoras y consumir la GPU.
- **No hay TLS.** Todo viaja en claro.
- **MAVLink no va firmado.** Se pueden inyectar tramas en el 14550 y falsear
  lo que ve el supervisor. No permite volar la aeronave —el puente nunca
  emite— pero sí hacer que quien decide, decida mal.
- **No hay cuota total del archivero.** Hay tope por archivo, no por disco.
- **No hay límite de consultas simultáneas** al modelo.

## Pruebas

```bash
npm test               # analizador MAVLink: CRC, decodificación, resincronía
node prueba-extremo.js    # UDP -> puente -> WebSocket, con el puente corriendo
node prueba-seguridad.js  # fuga de rutas, CSRF, DNS rebinding, WebSocket
```

El primero contrasta el CRC contra el valor publicado de CRC-16/MCRF4XX
(`0x6F91` para `"123456789"`) en vez de contra sí mismo, y los `CRC_EXTRA`
salen de las cabeceras MAVLink que compila el propio proyecto.

---

## Archivos

| Archivo | Qué hace |
|---------|----------|
| `mavlink.js` | Analizador v1/v2 sin dependencias; 9 mensajes decodificados |
| `agente.js` | Umbrales, hallazgos, informe y puente con Ollama |
| `bridge.js` | Ingesta UDP, estado de flota, WebSocket, servidor web, API, MariaDB |
| `web/index.html` | La consola: mapa, cámaras, archivero y asistente |
| `camaras.json.ejemplo` | Plantilla para declarar flujos de video reales |
| `schema.sql` | Esquema de MariaDB |
| `prueba-mavlink.js` | Pruebas del analizador |
| `prueba-agente.js` | Pruebas de umbrales y del canal de alarma |
| `prueba-extremo.js` | Prueba de extremo a extremo |
| `prueba-seguridad.js` | Regresión de los cuatro agujeros cerrados |
| `logs/` | Bitácoras subidas. Fuera de git. |

## Aún no hecho

- **Autenticación** — hoy cualquiera en tu red alcanza el 8080 y el 8081, y eso
  ahora incluye borrar bitácoras y consumir el modelo
- El asistente no lee el contenido de los `.ulg`, solo su catálogo: para
  resumir un vuelo pasado hace falta decodificarlos o leer el histórico de
  MariaDB, y hoy no hace ninguna de las dos
- Repetidor WebRTC para video de baja latencia (ver arriba)
- Trazado de la misión planeada sobre el mapa (requiere leer `MISSION_ITEM_INT`)
- Escritura de eventos a la tabla `eventos` (el esquema ya está; falta cablearlo)
- Análisis de los `.ulg` en el navegador; hoy solo se archivan
