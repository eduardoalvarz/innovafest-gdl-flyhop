# Aplicación de escritorio — Windows

Puesto de operación completo: planificación de misión, vuelo, calibración,
ajuste de parámetros, video y registro.

El código fuente **no vive en esta carpeta**. Escritorio y móvil se compilan del
mismo árbol, `../estacion-tierra/`, con el mismo CMake; lo único que cambia es
el kit de Qt y el empaquetado. Duplicar el árbol solo garantizaría que las dos
copias se desincronizaran. Aquí está la receta que produce el binario de
Windows y lo que hay que saber para reproducirla.

---

## Estado

**Compila y corre.** Verificado en Windows 11 contra hardware PX4 real
(Standard VTOL, firmware 1.14.3, en HITL).

No hay instalador firmado todavía; hoy se despliega como carpeta portátil.

---

## Requisitos

| Pieza | Versión | Nota |
|-------|---------|------|
| Qt | **6.8.3**, kit `msvc2022_64` | La etiqueta v5.0.8 de QGC fija esta versión. Otras dan errores de compilación. |
| Visual Studio | 2022, MSVC 14.43 | Solo se necesitan las Build Tools. |
| CMake | ≥ 3.22 | |
| Ninja | El que trae Qt | `<Qt>/Tools/Ninja` |
| GStreamer | 1.x MSVC x86_64 | Runtime **y** development. Sin él no hay video. |

## Compilar

```bat
:: vswhere.exe debe estar en el PATH o vcvarsall no configura nada y falla
:: mucho después, con errores de cabeceras que no aparecen.
set "PATH=C:\Program Files (x86)\Microsoft Visual Studio\Installer;%PATH%"
call "<VS>\VC\Auxiliary\Build\vcvars64.bat"

set "QT_ROOT_DIR=<Qt>\6.8.3\msvc2022_64"
set "PATH=%QT_ROOT_DIR%\bin;<Qt>\Tools\Ninja;%PATH%"

cmake -S estacion-tierra -B build\qt6-Windows -G "Ninja Multi-Config" ^
      -DCMAKE_BUILD_TYPE=Release
cmake --build build\qt6-Windows --target all --config Release
```

Una compilación en frío tarda bastante y CMake descarga dependencias durante el
proceso; conviene lanzarla en segundo plano.

## Desplegar

Dos pasos, y **ninguno de los dos es opcional**:

```bat
windeployqt --release --qmldir build\qt6-Windows\qml <ruta>\OTECH-GroundStation.exe
```

> `--qmldir` **es obligatorio**, y apuntando al directorio QML del *árbol de
> compilación*, no al de fuentes: QGC genera sus módulos QML al compilar. Sin
> esa opción los complementos QML no se copian, `QQmlApplicationEngine` no
> consigue cargar `MainWindow.qml`, no llega a crearse ninguna ventana y la
> aplicación se cierra sola a los pocos segundos con una excepción en
> `Qt6Core.dll`. Esa excepción es un síntoma del cierre, no la causa, y cuesta
> horas si se persigue por el camino equivocado.

```bat
:: windeployqt no incluye GStreamer. Hay que copiarlo a mano.
copy <GStreamer>\1.0\msvc_x86_64\bin\*.dll                    <destino>\
xcopy <GStreamer>\1.0\msvc_x86_64\lib\gstreamer-1.0\*.dll     <destino>\gstreamer-1.0\
```

El lanzador `launch.vbs` que acompaña al despliegue existe justamente por esto:
fija `GST_PLUGIN_PATH` a la subcarpeta `gstreamer-1.0` y arranca el ejecutable
sin ventana de consola. Resuelve rutas de forma relativa a sí mismo, así que la
carpeta es portátil.

---

## Hardware verificado

| Elemento | Detalle |
|----------|---------|
| Sistema | Windows 11, x86‑64 |
| Controlador de vuelo | PX4 Standard VTOL, firmware 1.14.3 |
| Enlace | USB serie y UDP |
| Modo de prueba | HITL (hardware‑in‑the‑loop) |

Lo que QGroundControl admite aguas arriba — ArduPilot, otras autopilotos,
telemetría por radio serie — **no lo hemos verificado nosotros**. Ver
`../documentacion/hardware/compatibilidad.md` para la distinción completa entre
lo comprobado y lo heredado.

---

## Diferencias reales frente a la versión móvil

Ninguna en el código. Las diferencias son de entorno:

| | Escritorio | Móvil |
|---|---|---|
| Kit de Qt | `msvc2022_64` | `android_arm64_v8a` |
| Empaquetado | windeployqt + carpeta | androiddeployqt + APK |
| Enlace al vehículo | USB serie, UDP | USB serie por JNI, UDP |
| Firma | No la hay todavía | Obligatoria antes de instalar |

---

## Cambios propios sobre QGroundControl

Detallados en `../AVISO-DE-ORIGEN.md`. En resumen: identidad visual, tema,
pantalla de arranque, consola MAVLink en la vista de vuelo, horizonte
artificial como instrumento por omisión, y cinco correcciones necesarias
simplemente para que la v5.0.8 compilara con las dependencias actuales.
