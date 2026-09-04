# Marco normativo

Qué normas aplican a este software, cuáles adoptamos, y —lo más importante—
qué significa y qué no significa haberlas adoptado.

El desarrollo completo está en **OTECH‑GCS‑SW‑001 Rev. A**, 53 páginas, en
esta misma carpeta (`.docx` y `.pdf`). Esto es el resumen.

---

## Advertencia previa

**Este paquete es una especificación y un plan, no un certificado.** Nadie ha
auditado el software, ninguna autoridad lo ha aprobado, y el capítulo 13 del
documento lista sin adornos ocho limitaciones reales (L‑1 a L‑8).

Se dice aquí arriba y no en una nota al pie porque la diferencia entre
«desarrollado conforme a DO‑278A» y «certificado bajo DO‑278A» es exactamente
la clase de afirmación que descalifica una candidatura, además de ser falsa.

---

## Marco nacional (México)

### NOM‑107‑SCT3‑2019

La norma oficial mexicana que rige la operación de sistemas de aeronave
pilotada a distancia. Es el marco que aplica a la operación, y de ahí salen
condiciones que el software tiene que respetar:

- **Operación dentro de la línea visual (VLOS)** como caso general. La consola
  en la nube supervisa; no sustituye al piloto que ve la aeronave.
- Clasificación por peso máximo de despegue, que determina el régimen aplicable.
- Registro de la aeronave y licencia del piloto según la categoría.
- Restricciones de espacio aéreo, altura y distancia a personas y aeródromos.

La autoridad competente es la **AFAC** (Agencia Federal de Aviación Civil).

### Consecuencia de diseño

El vuelo BVLOS y el mando desde la nube **no** están cubiertos por la operación
VLOS ordinaria. Requieren autorización específica y análisis de seguridad
propio. Por eso este sistema mantiene el mando en el enlace RF local — ver más
abajo.

---

## Marco de software

### DO‑278A / ED‑109A — la norma adoptada

Publicada por RTCA y EUROCAE. Es la norma para **software de tierra CNS/ATM**,
que es lo que una estación de control de tierra es. La adoptamos a ella, y no
a DO‑178C, que rige el software **embarcado**: aplicarla a un programa de
escritorio sería confundir la categoría del producto.

DO‑278A gradúa el rigor en niveles de garantía **AL1** (el más exigente) a
**AL6**. Lo adoptado:

| Operación | Nivel | Razón |
|-----------|-------|-------|
| VLOS, mando en el enlace RF | **AL4** | Línea base propuesta. |
| BVLOS | **AL3** | Al perderse la referencia visual, el software pasa a ser la única fuente de conciencia situacional. |

### Normas de apoyo

| Norma | Para qué |
|-------|----------|
| **DO‑326A / ED‑202A** | Seguridad informática aeronáutica. Marca el proceso para tratar la superficie de ataque, y es la que obliga a mirar con lupa cualquier puerto abierto hacia la red. |
| **SAE ARP4761** | Evaluación de seguridad: FHA, análisis de condiciones de fallo. |
| **SAE ARP4754A** | Desarrollo de sistemas aéreos y sus equipos. |
| **SAE ARP4102** | Prácticas de interfaz de cabina — de dónde sale la convención de color de las alertas. |
| **DO‑330** | Cualificación de herramientas de desarrollo. |
| **ICAO Doc 10019** | Manual RPAS. Aporta el concepto de **RLP** (*Required Link Performance*), decisivo para cualquier propuesta de mando por red. |
| **ISO/IEC 27001** | Gestión de seguridad de la información, como referencia. |
| **SORA / OSO** | Metodología de referencia para evaluación de riesgo operacional. No se adopta formalmente. |

---

## La hipótesis S‑1, y por qué gobierna la arquitectura

> **S‑1 — La aeronave conserva sus protecciones autónomas, y el mando en tiempo
> real permanece en el enlace RF local.**

No es una restricción técnica que no supiéramos resolver. Es una decisión de
seguridad, y de ella se deriva la forma del sistema entero.

**La capa en la nube observa. No manda.** El socket UDP de `web-cloud/` es de
solo lectura y **nunca llama a `send()`**. Armado, cambio de modo de vuelo y
retorno se ejecutan desde la radio. Se puede comprobar leyendo el código, que
son unas doscientas líneas.

### Qué pasaría si se moviera el mando a la nube

Cuatro consecuencias concretas, ninguna hipotética:

1. **Nuevas condiciones de fallo en la FHA.** La pérdida del enlace de red pasa
   a ser una condición de fallo del sistema de mando, con su clasificación de
   severidad y su presupuesto de probabilidad. Hoy no lo es.
2. **Se rompe la hipótesis VLOS de la NOM‑107.** Mandar por red implica que el
   piloto puede no estar viendo la aeronave, lo que cambia el régimen aplicable.
3. **Hay que demostrar RLP** (ICAO Doc 10019): latencia, disponibilidad,
   continuidad e integridad del enlace, con números y con evidencia. Internet
   público no ofrece garantías de latencia, y una latencia variable y no acotada
   no se puede acotar por declaración.
4. **La superficie de ataque de DO‑326A cambia de naturaleza.** Un sistema que
   solo observa filtra información si lo comprometen. Uno que manda, vuela la
   aeronave.

Esta es también la razón de que el video en la nube no habilite pilotar contra
la imagen. Que se vea fluida no acota su retardo.

---

## Trazabilidad

El documento normativo desarrolla la cadena completa:

```
Necesidad operacional → HLR (76) → LLR (124) → Código → Casos de verificación (76)
```

Las figuras del modelo en V, la arquitectura en capas y la cadena de
trazabilidad están en `../figuras/`.

**Los estados de verificación de cada requisito son una estimación** a partir
del código y de lo probado en sesión (HITL con PX4 v1.14.3). **No están
auditados por un tercero.**

---

## Origen del software y §2.7

El capítulo 2.7 del documento declara expresamente que QGroundControl es
**software preexistente**. Sin esa declaración y sin el capítulo 13 de
limitaciones, el documento sería una declaración de conformidad falsa.

Ver `../../AVISO-DE-ORIGEN.md` para el desglose de autoría.

---

## Regenerar el documento

```bash
cd documentacion/_generador
python diagramas.py && python documento.py
powershell -File a_pdf.ps1 -Docx ../normativa/OTECH-GCS-SW-001_RevA.docx
```

El PDF se produce automatizando Word por COM y no con un motor propio: los
índices son campos TOC que hay que actualizar y repaginar dos veces para que
los números de página coincidan con el `.docx`.

### Pendiente al reeditar

`_generador/documento.py:492` todavía declara el identificador de paquete
Android como `org.mavlink.qgroundcontrol`. Ya se renombró a
`com.otech.groundstation`; al reemitir hay que actualizar §1.3 y dar por
cerrada la acción P‑10.

### Una trampa del generador

En Python 3.9, `tokenize` entrega una f‑string como un único token `STRING`. Un
script que sustituya texto dentro de literales toca también los identificadores
interpolados (`{CODIGO}` → `{CÓDIGO}`) y el módulo revienta con `NameError`.
`ast.parse` no lo detecta.
