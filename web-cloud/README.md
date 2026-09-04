# Torre OTECH — despliegue local

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

## Las tres vistas

El conmutador de la barra superior cambia el centro de la consola:

- **Mapa** — situación de toda la flota, instrumentos de la aeronave elegida y
  su cámara en un recuadro. Todas las aeronaves se dibujan siempre; la elegida
  lleva anillo y estela gruesa, las demás quedan atenuadas.
- **Cámaras** — mosaico con una baldosa por aeronave, todas a la vez, cada una
  con su altura, velocidad, rumbo y batería sobre la imagen.
- **Bitácoras** — el archivero de registros de vuelo.

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

## Pruebas

```bash
npm test               # analizador MAVLink: CRC, decodificación, resincronía
node prueba-extremo.js # UDP -> puente -> WebSocket, con el puente corriendo
```

El primero contrasta el CRC contra el valor publicado de CRC-16/MCRF4XX
(`0x6F91` para `"123456789"`) en vez de contra sí mismo, y los `CRC_EXTRA`
salen de las cabeceras MAVLink que compila el propio proyecto.

---

## Archivos

| Archivo | Qué hace |
|---------|----------|
| `mavlink.js` | Analizador v1/v2 sin dependencias; 9 mensajes decodificados |
| `bridge.js` | Ingesta UDP, estado de flota, WebSocket, servidor web, API, MariaDB |
| `web/index.html` | La consola: mapa, mosaico de cámaras y archivero |
| `camaras.json.ejemplo` | Plantilla para declarar flujos de video reales |
| `schema.sql` | Esquema de MariaDB |
| `prueba-mavlink.js` | Pruebas del analizador |
| `prueba-extremo.js` | Prueba de extremo a extremo |
| `logs/` | Bitácoras subidas. Fuera de git. |

## Aún no hecho

- **Autenticación** — hoy cualquiera en tu red alcanza el 8080 y el 8081, y eso
  ahora incluye borrar bitácoras
- Repetidor WebRTC para video de baja latencia (ver arriba)
- Trazado de la misión planeada sobre el mapa (requiere leer `MISSION_ITEM_INT`)
- Escritura de eventos a la tabla `eventos` (el esquema ya está; falta cablearlo)
- Análisis de los `.ulg` en el navegador; hoy solo se archivan
