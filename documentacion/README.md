# Documentación

| Documento | Qué contiene |
|-----------|--------------|
| [`normativa/marco-normativo.md`](normativa/marco-normativo.md) | Qué normas aplican, cuáles se adoptan y qué significa haberlas adoptado. Empieza por aquí. |
| [`normativa/OTECH-GCS-SW-001_RevA.pdf`](normativa/) | El documento completo: 53 páginas, español de México. También en `.docx`. |
| [`hardware/compatibilidad.md`](hardware/compatibilidad.md) | Hardware verificado frente a hardware heredado de QGroundControl. La distinción importa. |
| [`figuras/`](figuras/) | Modelo en V, arquitectura en capas, cadena de trazabilidad. |
| [`_generador/`](_generador/) | El documento normativo se genera con Python; aquí está el código. |

## Lo esencial, en tres líneas

- Se adopta **DO‑278A/ED‑109A** (software de tierra), nivel **AL4**, con AL3
  propuesto para BVLOS. No DO‑178C, que es para software embarcado.
- Marco nacional: **NOM‑107‑SCT3‑2019**, autoridad **AFAC**.
- **No es un certificado.** Es una especificación y un plan. Nadie lo ha
  auditado. El capítulo 13 lista ocho limitaciones reales.

## La hipótesis que gobierna la arquitectura

**S‑1: la aeronave conserva sus protecciones autónomas y el mando en tiempo
real permanece en el enlace RF local.** La capa en la nube observa y no manda:
su socket UDP nunca llama a `send()`.

Mover el mando a la nube introduce condiciones de fallo nuevas en la FHA, rompe
la hipótesis VLOS de la NOM‑107, obliga a demostrar RLP según ICAO Doc 10019 y
cambia la naturaleza de la superficie de ataque bajo DO‑326A. Está desarrollado
en el marco normativo.
