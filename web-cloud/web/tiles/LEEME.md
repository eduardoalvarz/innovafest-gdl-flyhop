# Teselas propias

La capa **Propio** de la consola lee de aquí:

```
web/tiles/{z}/{x}/{y}.png
```

Esquema XYZ estándar (el mismo de OSM: origen arriba a la izquierda, `y` sin
invertir). No hace falta ningún servidor extra: las sirve el mismo `bridge.js`.

Mientras esté vacío, la capa se ve en blanco y no da error.

## Por qué esta capa importa

Es la única imagen satelital/aérea que puedes usar comercialmente sin pagar ni
pedir permiso: **la tuya**. Vuelas levantamientos, así que produces ortomosaicos
de mejor resolución y más actuales que cualquier mapa base público.

## Cómo llenarla

Desde un ortomosaico GeoTIFF, con GDAL:

```bash
gdal2tiles.py --xyz -z 14-21 --processes=4 ortomosaico.tif web/tiles/
```

El `--xyz` es obligatorio: sin él GDAL escribe el esquema TMS, con la `y`
invertida, y las teselas salen en el lugar equivocado.

Desde QGIS: **Procesos ▸ Raster ▸ Generar teselas XYZ (directorio)**.

## Vuelo sin internet

Con esta carpeta poblada, la consola funciona completamente aislada: Leaflet se
sirve desde `node_modules` y las teselas desde disco. Lo único que seguiría
buscando red son las tipografías de Google; descarga los `.woff2` a
`web/assets/` y cámbialas en el `<link>` si operas sin señal.
