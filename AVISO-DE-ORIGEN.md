# Aviso de origen y licencias

Este documento existe para que nadie tenga que adivinar qué parte del software
es obra propia y qué parte es software preexistente. Importa por dos razones:
la licencia obliga, y las bases de InnovaFest descalifican por atribuirse lo
que no es propio.

---

## Lo que es software preexistente

`estacion-tierra/` es un **fork de [QGroundControl]**, tomado de la etiqueta
**v5.0.8** del repositorio `mavlink/qgroundcontrol`. No lo escribimos nosotros.
Es un proyecto maduro, con más de una década de desarrollo y cientos de
colaboradores, y aquí se reutiliza tal como su licencia lo permite.

QGroundControl se distribuye bajo **doble licencia Apache 2.0 y GPL v3**; los
textos completos están en `estacion-tierra/LICENSE-APACHE` y
`estacion-tierra/LICENSE-GPL`. La copia en la raíz de este repositorio es la
Apache 2.0.

Junto con él vienen sus propias dependencias, cada una con su licencia:
Qt 6.8.3 (LGPL v3 en las partes que usamos), GStreamer (LGPL), la biblioteca
MAVLink (MIT), y otras que CMake descarga durante la compilación.

[QGroundControl]: https://github.com/mavlink/qgroundcontrol

### Una advertencia concreta sobre Qt Charts

El inspector MAVLink de la estación usa **Qt Charts, que es GPL v3**, no LGPL.
Distribuir un binario que lo incluya obliga a liberar el código de la aplicación
bajo GPL v3. Hay un interruptor previsto para excluirlo —
`QGC_DISABLE_MAVLINK_INSPECTOR` en `estacion-tierra/cmake/CustomOptions.cmake` —
hoy comentado. **Si en algún momento se distribuye un binario cerrado, hay que
activarlo o aceptar la GPL v3.** No es un problema mientras el código sea
abierto, que es el caso aquí.

### El modelo de lenguaje NO es software libre — leer antes de distribuir

El asistente de `web-cloud/` consulta un modelo servido por **[Ollama]**
(licencia MIT, sin problema). El modelo en sí es otra cosa:

| Modelo | Licencia | Qué implica |
|--------|----------|-------------|
| **Llama 3.2** (el que usamos por omisión) | **Llama 3.2 Community License** — *no* es una licencia de código abierto aprobada por la OSI | Obliga a mostrar **«Built with Llama»**, a incluir el aviso de licencia, a nombrar los modelos derivados con el prefijo `Llama`, y a cumplir su política de uso aceptable. Además exige licencia aparte de Meta si el producto supera los 700 millones de usuarios activos mensuales. |
| **Qwen3‑VL** (alternativa instalada) | Apache 2.0 | Sin restricciones de uso ni de escala. |

Dos consecuencias prácticas:

1. **Si el producto se distribuye o se comercializa con Llama por omisión**, hay
   que poner el aviso «Built with Llama» en la interfaz y en la documentación. No
   está puesto todavía.
2. **La salida más limpia es cambiar el modelo por omisión a uno Apache 2.0**
   —Qwen3‑VL ya está instalado, o Mistral, o Gemma bajo sus propios términos— y
   dejar Llama como opción del usuario. El selector de modelo del chat ya lo
   permite sin tocar código.

Nada de esto afecta al uso interno en desarrollo, que es el caso hoy. Afecta al
día que esto se entregue a un cliente o se presente como producto.

[Ollama]: https://ollama.com

---

## Lo que es obra propia

| Qué | Dónde | Naturaleza |
|-----|-------|-----------|
| **AeroHub Link** — puente MAVLink, analizador de protocolo, consola web multi‑aeronave, mosaico de cámaras, archivero de bitácoras | `web-cloud/` | Escrito desde cero. Sin framework, sin dependencias más allá de `ws` y Leaflet. |
| **Analizador MAVLink v1/v2** | `web-cloud/mavlink.js` | Implementación propia, con CRC‑16/MCRF4XX validado contra el valor publicado del estándar. |
| **Asistente en lenguaje natural** | `web-cloud/agente.js` | Motor de umbrales y hallazgos, generador de informe y puente con Ollama. El modelo es de terceros; el juicio de seguridad, el canal de alarma y la negativa a mandar son obra propia. |
| **Identidad visual y tema** | `estacion-tierra/src/QmlControls/QGCPalette.cc`, iconos, splash | Rebranding OTECH sobre la estructura de QGC. |
| **Consola MAVLink en la vista de vuelo** | `estacion-tierra/src/FlightDisplay/FlyViewMavlinkConsole.qml` | Componente nuevo, con ticker de telemetría dirigido por cambio. |
| **Pantalla de arranque** | `estacion-tierra/src/UI/OtechSplashScreen.qml` | Componente nuevo. |
| **Renombrado de paquete Android** a `com.otech.groundstation` | manifiesto, gradle, Java y literales JNI en C++ | Modificación propia, en cinco puntos del árbol. |
| **Correcciones para que v5.0.8 compile** | `GPSProvider.cc`, `MockLink/CMakeLists.txt`, `QGCApplication.cc`, GStreamer/Android | Parches propios sobre código ajeno. |
| **Paquete normativo OTECH‑GCS‑SW‑001** | `documentacion/` | Redacción propia: 76 HLR, 124 LLR, 76 casos de verificación. |

---

## Cómo describirlo sin faltar a la verdad

Correcto:

> Integramos y adaptamos QGroundControl como estación de tierra, y desarrollamos
> sobre él una capa propia de supervisión en la nube, la consola de telemetría
> embarcada y el paquete de documentación normativa.

Incorrecto:

> Desarrollamos una estación de control de tierra.

La diferencia no es de matiz. Las bases de InnovaFest contienen una cláusula de
veracidad que descalifica propuesta y equipo, y la primera formulación describe
un trabajo de integración y desarrollo que es real, verificable y sustancial por
sí mismo. No hace falta la segunda.

---

## Obligaciones que hay que cumplir al distribuir

1. Conservar los avisos de copyright y licencia de QGroundControl y de sus
   dependencias. Ya están en `estacion-tierra/`; no borrarlos.
2. Indicar que el software ha sido modificado respecto del original — para eso
   sirve este archivo.
3. Si se distribuye un binario que incluya Qt Charts, liberar el código bajo
   GPL v3 o excluir ese componente.
4. Qt se usa bajo LGPL v3: el binario debe permitir sustituir las bibliotecas
   Qt, cosa que el enlazado dinámico ya satisface.
