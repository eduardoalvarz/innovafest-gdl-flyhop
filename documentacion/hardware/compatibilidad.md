# Compatibilidad de hardware

Este documento separa deliberadamente **lo que hemos verificado nosotros** de
**lo que el software admite porque lo hereda de QGroundControl**. La segunda
lista es mucho más larga que la primera, y confundirlas sería afirmar más de lo
que podemos sostener.

---

## Verificado por nosotros

Probado en este proyecto, con estos aparatos concretos.

### Controlador de vuelo

| | |
|---|---|
| Autopiloto | **PX4** |
| Firmware | **1.14.3** |
| Configuración | Standard VTOL |
| Modo de prueba | HITL (hardware‑in‑the‑loop) |
| Protocolo | MAVLink v2 |

Comprobado en vuelo simulado: telemetría en directo, `STATUSTEXT` con su
severidad coloreada según la convención aeronáutica, la corrección de la
gráfica de ajuste PID, y el conteo de satélites en ámbar por debajo de 6.

### Estación de escritorio

| | |
|---|---|
| Sistema | Windows 11, x86‑64 |
| Enlaces | USB serie, UDP |
| Video | GStreamer 1.x (MSVC x86_64) |

### Radio control

| | |
|---|---|
| Aparato | **SIYI**, con Android integrado |
| ABI | `arm64-v8a` |
| Android mínimo | API 28 (9 Pie) |
| Enlaces | USB serie por JNI, UDP por Wi‑Fi |
| Emulador adicional | Pixel 9 Pro XL, API 34 |

Instalado y en marcha con la identidad OTECH correcta.

**Dos observaciones abiertas:** la interfaz del sistema del radio está en chino
—configuración regional del aparato, no de la aplicación— y el recuadro de
video muestra *WAITING FOR VIDEO*: no le llega flujo de la cámara. Está sin
diagnosticar.

---

## Admitido, heredado de QGroundControl

QGroundControl lleva más de una década de desarrollo y su lista de hardware
compatible es amplia. **Nosotros no la hemos verificado.** Lo que sigue es
capacidad heredada, y así hay que presentarla.

### Autopilotos

- **PX4** — toda la familia (nosotros verificamos 1.14.3 en VTOL estándar)
- **ArduPilot** — Copter, Plane, Rover, Sub. **Sin verificar por nosotros.**

### Controladores de vuelo

La serie Pixhawk (1, 2/Cube, 4, 5X, 6C, 6X), Holybro, CUAV, mRo y cualquier
otro que hable MAVLink. **Sin verificar por nosotros** salvo el usado en las
pruebas.

### Enlaces de telemetría

| Tipo | Detalle |
|------|---------|
| Serie / USB | Directo al controlador de vuelo |
| Radio serie | SiK (3DR, RFD900 y compatibles) |
| UDP / TCP | Red, incluido el reenvío MAVLink |
| Bluetooth | Según el sistema operativo |
| AirLink | Módem por servicio remoto (`src/Comms/AirLink/`) |

### Video

GStreamer: RTSP, RTP, UDP y UVC. En Windows exige copiar el runtime a mano —
ver `../../app-escritorio/README.md`.

### Mandos

Joysticks y gamepads por SDL en escritorio, y por la API de entrada de Android
en el radio (`JoystickAndroid.cc`).

---

## Torre OTECH (la capa web)

`web-cloud/` no habla con el hardware. Recibe MAVLink reenviado por la
estación, así que su compatibilidad es la de la estación.

| | |
|---|---|
| Entrada | UDP 14550, MAVLink v1 y v2 |
| Mensajes decodificados | 9: `HEARTBEAT`, `SYS_STATUS`, `GPS_RAW_INT`, `GLOBAL_POSITION_INT`, `MISSION_CURRENT`, `VFR_HUD`, `RADIO_STATUS`, `BATTERY_STATUS`, `STATUSTEXT` |
| Varias aeronaves | Sí, indexadas por `sysid`, sin configurar nada |
| Servidor | Node.js ≥ 18 |
| Navegador | Cualquiera con WebSocket y `<canvas>` |
| Base de datos | MariaDB / MySQL, opcional (XAMPP sirve) |

**No emite hacia la aeronave.** El socket UDP nunca llama a `send()`, conforme
a la hipótesis S‑1.

### Conectar la estación a la torre

No hace falta recompilar nada. En la estación: **Ajustes ▸ MAVLink ▸ reenvío**,
que corresponde a `forwardMavlink` y `forwardMavlinkHostName` en
`estacion-tierra/src/Settings/MavlinkSettings.cc`.

- Escritorio, misma máquina → `127.0.0.1:14550`
- Radio SIYI → la IP del PC en la red del radio, y abrir el puerto en el
  cortafuegos para redes privadas

---

## Requisitos de la máquina de desarrollo

Lo que hace falta para **compilar**, que es bastante más que para ejecutar.

| Pieza | Versión | Nota |
|-------|---------|------|
| Qt | 6.8.3 | Fijada por la etiqueta v5.0.8. Otras no compilan. |
| Visual Studio | 2022, MSVC 14.43 | Escritorio |
| NDK de Android | 26.1.10909125 (r26b) | Móvil. El r25b es de Qt 6.5.x. |
| SDK de Android | API 34, build‑tools 34.0.0 | Móvil |
| JDK | Adoptium 21 | No sobrescribir `JAVA_HOME` |
| CMake | ≥ 3.22 | |
| Node.js | ≥ 18 | Solo para `web-cloud/` |

---

## Limitaciones conocidas

1. **No hay compilación para macOS ni Linux.** El código las admite aguas
   arriba; nosotros no las hemos construido.
2. **iOS no está contemplado.**
3. **El video no llega al SIYI.** Sin diagnosticar.
4. **`web-cloud/` no tiene autenticación.** Cualquiera en la red local alcanza
   los puertos 8080 y 8081, y eso incluye borrar bitácoras. Es lo primero que
   hay que resolver antes de exponerlo fuera de un puesto de operación.
5. **Solo una ABI de Android** (`arm64-v8a`). Aparatos de 32 bits quedan fuera.
6. **No hay instalador firmado** para escritorio, ni clave de publicación para
   Android; hoy se firma con la clave de depuración.
