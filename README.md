# InnovaFest GDL 2026 — Fly-Hop Delivery

Continuidad del **dron de delivery de InnovaFest Querétaro**, ahora bajo un esquema de **Fly-Hop para delivery**: además del dron, una **plataforma de software para gestionar la operación de entregas**, tomando como referencia soluciones tipo DJI (FlightHub / Dock).

## Objetivo del MVP

Prototipo funcional y demostrable en GDL que cubra el flujo completo:

```
solicitud de entrega → origen y destino → asignación del dron → seguimiento del vuelo → entrega y confirmación
```

La prioridad es **el mínimo viable** para demostrar ese flujo de punta a punta.

## InnovaFest GDL 2026 — fechas y bases

| Qué | Cuándo / dónde |
|---|---|
| **Cierre de postulación** | **14 de octubre de 2026, 23:59 CDMX** (convocatoria oficial PDF). La tabla del sitio decía 5-oct en agosto; en QRO el sitio fue la fuente correcta, no el PDF → **confirmar en innovafest.mx antes de planear al límite** |
| Evento / ceremonia | **23 de octubre de 2026**, 9:00–20:00, Expo Guadalajara (Av. Mariano Otero 1499) |
| Resultados | Se notifican al menos una semana antes del 23-oct |
| Premios | Etapa temprana $150k · Etapa avanzada $250k (8 ganadores por etapa) + en especie |
| Registro | Perfil ECOIIN en innovafest.mx → Convocatorias → Premio a la Innovación Mexicana |

**Categorías donde encaja el proyecto**
- Nacional 2: Movilidad / Desarrollo urbano
- Regional 3: **Movilidad inteligente** — preguntas detonadoras: "¿Cómo optimizar logística multimodal entre puertos, ciudades e industria?" / "¿Qué tecnologías pueden reducir emisiones en transporte de carga?"
- Regional 2: Sistemas agroalimentarios — "¿Qué innovaciones pueden mejorar logística y conservación de alimentos?"
- Se puede proponer pregunta propia si encaja en una categoría.

**Entregables** (se suben a la plataforma, sin cambios después de enviar; previsualizar)
1. Formulario con datos personales y generales del proyecto.
2. **PDF máx. 5 cuartillas** (+ portada no contabilizada) con subtítulos: Necesidad y contexto · Propuesta de valor · Ventajas competitivas e impacto esperado · (equipo, viabilidad, modelo de negocio).
3. **Video pitch máx. 3:00**, MP4 ≤150 MB: equipo y roles, problema y solución, avances (prototipo funcional, pruebas, evidencia).

**Criterios de evaluación**

| Peso | Criterio |
|---|---|
| 20% | Claridad del problema e impacto |
| 15% | Solución y grado de innovación |
| 20% | Viabilidad técnica y operativa |
| 20% | Impacto medible (indicadores) |
| 15% | Sostenibilidad / modelo de negocio |
| 10% | Equipo ejecutor |

Equipo: mayoría de nacionalidad mexicana (50%+1). Fuente: [Convocatoria GDL (PDF)](https://innovafest.mx/files/Convocatoria-GUADALAJARA.pdf) · [Encuentro Guadalajara](https://innovafest.mx/encuentros/guadalajara).

## Lecciones de InnovaFest Querétaro (ago-2026)

- El deadline del sitio y el del PDF pueden diferir; manda el sitio.
- La plataforma usa Cloudflare Turnstile: el token caduca tras horas en la misma página y la subida del PDF falla; recargar. El borrador vive en localStorage (`innovafest_draft`) salvo datos personales.
- 3:00 de video es el gate de todo el contenido: bloques con voz real, nunca placas estáticas.
- Cuidado con reclamar "diseñamos/fabricamos" lo que no es propio: la cláusula de veracidad descalifica propuesta y equipo. Reclamar integración y desarrollo propio.
- El premio se paga a quien registra: definir desde el inicio quién es el representante.

## Siguientes pasos

- [ ] Confirmar fecha de cierre (5-oct vs 14-oct) en innovafest.mx
- [ ] Definir qué se reutiliza del dron de Querétaro
- [ ] Definir alcance del MVP de software y del dron
- [ ] Aterrizar el flujo de operación
- [ ] Definir responsables, tiempos y entregables (PDF 5 cuartillas + video 3:00)
