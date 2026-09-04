# Aplicación móvil — Android

La misma estación, en el radio control. Pensada para el **SIYI**, que es un
Android con la pantalla y los mandos integrados.

Como en la versión de escritorio, el código fuente vive en
`../estacion-tierra/`; aquí está la receta de compilación, firma e instalación,
y las trampas que cuestan una tarde si no se conocen de antemano.

---

## Estado

**Compila, se instala y corre.** Verificado en un radio control SIYI real y en
el emulador `Pixel_9_Pro_XL_API_34`.

Dos observaciones abiertas del despliegue en el SIYI: la interfaz del sistema
del radio está en chino (es la configuración regional del aparato, no de la
aplicación), y el recuadro de video muestra *WAITING FOR VIDEO* porque no le
llega flujo de la cámara.

---

## Requisitos

| Pieza | Versión | Por qué esa |
|-------|---------|-------------|
| Qt Android | **6.8.3**, `android_arm64_v8a` | Debe coincidir con la etiqueta v5.0.8. |
| `QT_HOST_PATH` | `6.8.3/msvc2022_64` | Qt necesita sus herramientas de anfitrión. |
| NDK | **26.1.10909125** (r26b) | Es el que elige la CI de Qt 6.8.3. El r25b es para Qt 6.5.x, y equivocarse produce fallos de enlazado incomprensibles. |
| SDK | API 34, build‑tools 34.0.0 | |
| JDK | Adoptium 21 | **No sobrescribas `JAVA_HOME`.** Hereda el del sistema. |
| ABI | `arm64-v8a` únicamente | Compilar las cuatro cuadruplica el tiempo sin aportar nada. |
| minSdk | 28 | Determina que el icono de lanzador sea solo el adaptativo. |

Sobre `JAVA_HOME`: apuntarlo al JBR de Android Studio hace fallar el paso de
gradle con *«JAVA_HOME is set to an invalid directory»*. Lo traicionero es que
las bibliotecas nativas `.so` enlazan bien antes de ese punto, así que el fallo
aparece al final del todo, cuando parece que ya estaba hecho.

## Compilar

Hay que exportar `QT_ROOT_DIR`, `QT_HOST_PATH`, `ANDROID_SDK_ROOT`,
`ANDROID_HOME`, `ANDROID_NDK_ROOT`, `ANDROID_NDK_HOME` y `JAVA_HOME`, y añadir
al `PATH` el Ninja de Qt, `$JAVA_HOME\bin` y `$ANDROID_SDK_ROOT\platform-tools`.

La configuración usa **`qt-cmake.bat`, no `cmake` a secas** — el envoltorio de
Qt es el que inyecta el archivo de cadena de herramientas de Android:

```
qt-cmake.bat -S estacion-tierra -B build\qt6-Android -G "Ninja Multi-Config" ^
  -DQT_ANDROID_ABIS=arm64-v8a -DQT_ANDROID_BUILD_ALL_ABIS=OFF
cmake --build build\qt6-Android --target all --config Release
```

## Firmar — el APK sale sin firma

`adb install` del APK recién construido falla con
`INSTALL_PARSE_FAILED_NO_CERTIFICATES`. Desde `<SDK>\build-tools\34.0.0`:

```bat
zipalign -p -f 4 ^
  build\qt6-Android\android-build\build\outputs\apk\release\android-build-release-unsigned.apk ^
  alineado.apk

apksigner.bat sign --ks %USERPROFILE%\.android\debug.keystore ^
  --ks-pass pass:android --key-pass pass:android ^
  --ks-key-alias androiddebugkey --out OTECH-GroundStation.apk alineado.apk
```

**`zipalign` va antes que `apksigner`.** Al revés, la alineación invalida la
firma que se acaba de poner.

La clave del ejemplo es la de depuración. Para distribuir de verdad hace falta
una clave de publicación propia y guardada donde no se pierda: si se pierde, no
se pueden publicar actualizaciones de esa aplicación nunca más.

## Instalar y arrancar

```bat
adb install -r OTECH-GroundStation.apk
adb shell appops set com.otech.groundstation MANAGE_EXTERNAL_STORAGE allow
adb shell am start -n com.otech.groundstation/.QGCActivity
```

Sin ese `appops`, en el primer arranque la aplicación abre la pantalla de
permisos de «acceso a todos los archivos» de Android y **aparenta no hacer
nada**. Concedido el permiso y relanzada, carga la vista de vuelo.

Que las rutas JNI están bien se comprueba en logcat con estas tres líneas:
`Registering Native Functions`, `QGCActivity: Multicast lock` y
`QGCUsbSerialManager: BroadcastReceiver registered successfully`.

---

## El renombrado de paquete, y por qué importa

El identificador es **`com.otech.groundstation`**, no el
`org.mavlink.qgroundcontrol` original. Se cambió para que la aplicación pueda
convivir con un QGroundControl de fábrica en el mismo aparato: el de fábrica
está firmado con otra clave y bloquea la instalación con
`INSTALL_FAILED_UPDATE_INCOMPATIBLE`.

El renombrado toca **cinco sitios**, y omitir los tres últimos deja una
aplicación que compila, arranca y parece correcta, pero **pierde el puerto
serie USB y el joystick en tiempo de ejecución**, sin ningún error visible:

1. `android/AndroidManifest.xml` — el atributo `package` y el `android:name` de la actividad.
2. `android/build.gradle` — el `namespace`, que está escrito a mano y **prevalece** sobre `QT_ANDROID_PACKAGE_NAME`.
3. `android/src/com/otech/groundstation/*.java` — mover el directorio, las declaraciones `package`, el import interno y la cadena `ACTION_USB_PERMISSION`.
4. Los literales de ruta de clase JNI en C++: `src/Android/AndroidInterface.h`, `src/Android/AndroidSerial.h`, `src/Joystick/JoystickAndroid.cc`.
5. **Borrar `<build>/android-build/` antes de recompilar** — conserva las copias Java antiguas y gradle falla por clases duplicadas.

## El icono de lanzador

`android/res/` es el `QT_ANDROID_PACKAGE_SOURCE_DIR`, así que los iconos van
ahí y no en `resources/`. Con minSdk 28 el lanzador es solo el adaptativo:
`mipmap-anydpi-v26/ic_launcher.xml` más las capas de 108 dp y
`drawable/ic_launcher_background.xml`.

`drawable-*/icon.png` también está rebrandeado, pero hoy solo lo usa
`drawable/splashscreen.xml`. No conviertas `@drawable/icon` en un XML de icono
adaptativo o ese `<bitmap>` se rompe.

**androiddeployqt copia `android/res` al principio de la compilación.** Editar
un icono con la compilación ya empezada empaqueta silenciosamente el anterior;
compara siempre `android-build/res/...` contra el fuente antes de creerte un
rebuild.

---

## Hardware verificado

| Elemento | Detalle |
|----------|---------|
| Radio control | **SIYI** con Android integrado — instalado y en marcha |
| Emulador | Pixel 9 Pro XL, API 34 |
| ABI | `arm64-v8a` |
| Android mínimo | API 28 (9 Pie) |
| Enlace al vehículo | USB serie por JNI (`QGCUsbSerialManager`), UDP por Wi‑Fi |
| Controlador de vuelo | PX4 Standard VTOL, firmware 1.14.3 |

Detalle completo y la separación entre lo comprobado y lo heredado en
`../documentacion/hardware/compatibilidad.md`.

---

## Ajustes de interfaz para pantalla de radio

Una pantalla de radio control no es un monitor, y dos cosas hubo que corregir:

- El **horizonte artificial** (`VerticalCompassAttitude.qml`) mide el doble de
  alto que de ancho y su anchura sale del tamaño de fuente, así que en una
  pantalla densa crecía más que el hueco entre la barra y la consola y se salía
  por arriba. Está limitado a `mainWindow.height * 0.55`. En escritorio nunca
  se alcanza ese tope. Revísalo si cambia la altura de la consola o de la barra.
- El **recuadro de video** se montaba sobre la consola de telemetría. Ahora
  `FlyViewWidgetLayer.qml` publica un `consoleInset` y el recuadro lo suma a su
  margen inferior, así que sube y baja con la consola en vez de taparla.

Regla general: cualquier cosa anclada al borde inferior de la vista de vuelo
tiene que contar con la consola.
