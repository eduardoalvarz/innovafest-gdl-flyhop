# -*- coding: utf-8 -*-
"""Datos de requisitos, verificación y trazabilidad del documento OTECH-GCS-SW-001.

Se mantienen como datos y no como texto redactado para que la matriz de
trazabilidad se derive del mismo origen que las tablas de requisitos: si un
requisito cambia de identificador aquí, la matriz no puede quedarse desfasada.

Convenciones
------------
Criticidad     Severidad de la condición de fallo según el análisis del cap. 4
               (Crítico / Mayor / Menor), no la prioridad de desarrollo.
Método         I = Inspección, A = Análisis, D = Demostración, T = Prueba.
Estado         IV  Implementado y verificado con evidencia registrada
               IP  Implementado, verificación formal pendiente
               PA  Parcialmente implementado
               PL  Planificado, no implementado
"""

ESTADOS = {
    "IV": "Implementado y verificado",
    "IP": "Implementado / verificación pendiente",
    "PA": "Parcial",
    "PL": "Planificado",
}

# Etiqueta breve para las columnas estrechas de las tablas de requisitos. Con el
# texto largo la columna parte "Implementado" a mitad de palabra.
ESTADOS_CORTO = {
    "IV": "Verificado",
    "IP": "Impl. / v. pend.",
    "PA": "Parcial",
    "PL": "Planificado",
}

DOMINIOS = [
    ("COM", "Comunicaciones y enlace de mando y control (C2)"),
    ("TEL", "Telemetría y presentación del estado de la aeronave"),
    ("MIS", "Planificación y ejecución de la misión"),
    ("SAF", "Seguridad operacional y contención"),
    ("SIT", "Conciencia situacional"),
    ("VID", "Video y carga útil"),
    ("RID", "Identificación remota (Remote ID)"),
    ("UTM", "Integración con servicios UTM / U-space"),
    ("HMI", "Interfaz humano-máquina"),
    ("REG", "Registro de vuelo y evidencia"),
    ("CFG", "Configuración y gestión de parámetros"),
    ("PLT", "Plataforma, despliegue y portabilidad"),
    ("SEC", "Seguridad de la información"),
    ("PER", "Desempeño y comportamiento temporal"),
]

# (id, título, enunciado, criticidad, fuente normativa, método, estado)
HLR = [
    # --- COM ---------------------------------------------------------------
    ("HLR-COM-001", "Establecimiento del enlace C2",
     "El software deberá establecer y mantener el enlace de mando y control con la aeronave "
     "empleando el protocolo MAVLink 2.0 sobre enlaces serie, UDP, TCP y Bluetooth.",
     "Crítico", "NOM-107 6.1; OACI Doc 10019 cap. 6; SORA OSO#06", "T", "IV"),
    ("HLR-COM-002", "Redundancia de enlaces",
     "El software deberá admitir varios enlaces simultáneos hacia la misma aeronave y conmutar "
     "entre ellos sin pérdida de la capacidad de mando.",
     "Crítico", "SORA OSO#06; DO-278A 2.1", "T", "IP"),
    ("HLR-COM-003", "Detección de pérdida de enlace",
     "El software deberá detectar la pérdida del enlace C2 y notificarla al piloto en un plazo "
     "no superior a 5 segundos desde el último mensaje válido recibido.",
     "Crítico", "NOM-107 7.4; SORA OSO#06", "T", "IV"),
    ("HLR-COM-004", "Operación multiaeronave",
     "El software deberá gestionar de forma concurrente varias aeronaves diferenciadas por su "
     "identificador de sistema MAVLink, sin mezclar telemetría ni mandos entre ellas.",
     "Crítico", "OACI Doc 10019 cap. 6", "T", "IP"),
    ("HLR-COM-005", "Conexión automática de dispositivos",
     "El software deberá reconocer y conectar automáticamente los dispositivos serie compatibles "
     "declarados en su base de identificadores, siendo esta función desactivable por el usuario.",
     "Menor", "Requisito de producto", "D", "IP"),
    ("HLR-COM-006", "Integridad de los mensajes",
     "El software deberá verificar la suma de comprobación de cada trama MAVLink recibida y "
     "descartar sin procesar toda trama que no supere la verificación.",
     "Crítico", "DO-278A 6.4; DO-326A", "T", "IP"),
    ("HLR-COM-007", "Reproducción de registros",
     "El software deberá reproducir registros de vuelo previamente almacenados sin emitir "
     "ningún mensaje hacia enlaces activos durante la reproducción.",
     "Mayor", "Requisito derivado de seguridad DS-04", "T", "IP"),

    # --- TEL ---------------------------------------------------------------
    ("HLR-TEL-001", "Telemetría esencial",
     "El software deberá presentar de forma continua actitud, altitud, velocidad, rumbo, posición, "
     "estado de batería, estado GNSS, modo de vuelo y estado de armado de la aeronave.",
     "Crítico", "NOM-107 6.3; OACI Doc 10019 cap. 6", "D", "IV"),
    ("HLR-TEL-002", "Presentación de actitud",
     "El software deberá presentar un indicador de actitud y un indicador de rumbo conformes a "
     "la convención aeronáutica de cielo arriba, tierra abajo y giro en el sentido del viraje.",
     "Mayor", "OACI Anexo 6 Parte IV; buenas prácticas HMI", "D", "IV"),
    ("HLR-TEL-003", "Mensajes de estado de la aeronave",
     "El software deberá presentar los mensajes STATUSTEXT recibidos, ordenados cronológicamente "
     "y codificados por severidad MAV_SEVERITY 0 a 7 según la convención aeronáutica de alertas.",
     "Mayor", "OACI Doc 9859; SAE ARP4102/4", "D", "IV"),
    ("HLR-TEL-004", "Alertas de condición crítica",
     "El software deberá alertar de forma inequívoca y no suprimible ante batería baja, pérdida "
     "de posición GNSS, activación de un modo de protección y fallo de precondiciones de vuelo.",
     "Crítico", "NOM-107 7.4; SORA OSO#20", "T", "IV"),
    ("HLR-TEL-005", "Calidad del enlace",
     "El software deberá presentar los indicadores de calidad del enlace disponibles, incluyendo "
     "intensidad de señal y porcentaje de pérdida de paquetes.",
     "Mayor", "SORA OSO#06", "D", "IP"),
    ("HLR-TEL-006", "Estado de navegación por satélite",
     "El software deberá presentar el número de satélites empleados y el tipo de fijación GNSS, "
     "destacando visualmente las condiciones inferiores a las mínimas de operación.",
     "Mayor", "NOM-107 6.3", "D", "IV"),

    # --- MIS ---------------------------------------------------------------
    ("HLR-MIS-001", "Edición del plan de vuelo",
     "El software deberá permitir crear, editar, validar y almacenar planes de vuelo compuestos "
     "por puntos de ruta, comandos y elementos de misión complejos.",
     "Mayor", "NOM-107 6.2", "D", "IP"),
    ("HLR-MIS-002", "Transferencia del plan a la aeronave",
     "El software deberá transferir el plan de vuelo mediante el protocolo MAVLink Mission y "
     "confirmar la recepción íntegra antes de declarar la transferencia completada.",
     "Crítico", "NOM-107 6.2; DO-278A 6.4", "T", "IP"),
    ("HLR-MIS-003", "Lectura y cotejo del plan residente",
     "El software deberá leer el plan residente en la aeronave y señalar cualquier discrepancia "
     "respecto del plan mostrado en la estación.",
     "Crítico", "SORA OSO#08", "T", "IP"),
    ("HLR-MIS-004", "Validación de restricciones",
     "El software deberá impedir la carga de un plan que vulnere la altura máxima configurada o "
     "los límites de la geocerca definida, informando del motivo del rechazo.",
     "Crítico", "NOM-107 7.1 y 7.2; SORA OSO#10", "T", "PA"),
    ("HLR-MIS-005", "Cálculo de parámetros de misión",
     "El software deberá calcular y presentar la distancia total, la duración estimada y la altura "
     "máxima del plan antes de su ejecución.",
     "Mayor", "NOM-107 6.2", "D", "IP"),
    ("HLR-MIS-006", "Patrones de levantamiento",
     "El software deberá generar patrones de barrido, corredor y escaneo de estructura a partir de "
     "un área definida y de los parámetros ópticos de la cámara.",
     "Menor", "Requisito de producto", "D", "IP"),
    ("HLR-MIS-007", "Intercambio de planes",
     "El software deberá exportar e importar planes de vuelo en formatos interoperables, incluyendo "
     "el formato nativo .plan y KML para su presentación ante terceros.",
     "Menor", "NOM-107 6.2 (documentación de la operación)", "D", "IP"),

    # --- SAF ---------------------------------------------------------------
    ("HLR-SAF-001", "Definición de geocercas",
     "El software deberá permitir definir, transferir y verificar geocercas de inclusión y de "
     "exclusión, tanto poligonales como circulares.",
     "Crítico", "NOM-107 7.2; SORA OSO#10 y M2", "T", "IP"),
    ("HLR-SAF-002", "Puntos de recuperación",
     "El software deberá permitir definir y transferir puntos de recuperación a los que la "
     "aeronave pueda dirigirse ante una contingencia.",
     "Crítico", "SORA OSO#10; NOM-107 7.4", "T", "IP"),
    ("HLR-SAF-003", "Confirmación de mandos críticos",
     "El software deberá exigir una confirmación explícita e inequívoca del piloto antes de emitir "
     "cualquier mando que modifique el estado de vuelo: armado, despegue, cambio de modo, retorno, "
     "aterrizaje y terminación de vuelo.",
     "Crítico", "SORA OSO#20; DO-278A 6.3", "T", "IV"),
    ("HLR-SAF-004", "Retorno al punto de lanzamiento",
     "El software deberá ofrecer el mando de retorno al punto de lanzamiento accesible en un máximo "
     "de dos acciones del piloto desde la vista de vuelo.",
     "Crítico", "NOM-107 7.4; SORA OSO#20", "D", "IV"),
    ("HLR-SAF-005", "Advertencias de precondición",
     "El software deberá presentar de forma permanente y no ocultable las advertencias de "
     "precondición de vuelo emitidas por la aeronave mientras la condición persista.",
     "Crítico", "SORA OSO#20; NOM-107 7.3", "D", "IV"),
    ("HLR-SAF-006", "Inhibición de mandos sin enlace",
     "El software deberá inhibir la emisión de mandos de vuelo cuando no exista un enlace válido e "
     "informar al piloto de la causa de la inhibición.",
     "Crítico", "SORA OSO#06; DS-01", "T", "IP"),
    ("HLR-SAF-007", "Estado de los modos de protección",
     "El software deberá presentar la configuración vigente de los modos de protección de la "
     "aeronave, incluyendo las acciones ante pérdida de enlace y ante batería baja.",
     "Crítico", "NOM-107 7.4; SORA OSO#10", "D", "IP"),
    ("HLR-SAF-008", "Terminación de vuelo",
     "El software deberá permitir activar la terminación de vuelo cuando la aeronave implemente "
     "dicha función, protegida por una confirmación reforzada distinta del resto de mandos.",
     "Crítico", "SORA M2; OACI Doc 10019 cap. 6", "T", "PA"),

    # --- SIT ---------------------------------------------------------------
    ("HLR-SIT-001", "Presentación cartográfica",
     "El software deberá presentar la posición de la aeronave sobre cartografía georreferenciada "
     "con indicación explícita del sistema de referencia empleado.",
     "Mayor", "NOM-107 6.3", "D", "IV"),
    ("HLR-SIT-002", "Operación sin conexión",
     "El software deberá operar con cartografía descargada previamente, sin degradar ninguna "
     "función de mando ni de telemetría por ausencia de conexión a Internet.",
     "Mayor", "NOM-107 6.1 (operación en áreas sin cobertura)", "T", "IP"),
    ("HLR-SIT-003", "Altura sobre el terreno",
     "El software deberá presentar el perfil del terreno bajo la trayectoria planificada y la "
     "altura de la aeronave sobre el terreno cuando disponga de datos de elevación.",
     "Mayor", "SORA OSO#10; NOM-107 7.1", "D", "IP"),
    ("HLR-SIT-004", "Presentación de tránsito ADS-B",
     "El software deberá presentar sobre la cartografía las aeronaves detectadas por el receptor "
     "ADS-B conectado, con su identificación y altitud.",
     "Mayor", "OACI Anexo 2; SORA OSO#19", "D", "IP"),
    ("HLR-SIT-005", "Posición del puesto de pilotaje",
     "El software deberá obtener y presentar la posición del puesto de pilotaje a partir del "
     "receptor GNSS del equipo anfitrión.",
     "Mayor", "ASTM F3411-22a; NOM-107 6.3", "D", "IP"),
    ("HLR-SIT-006", "Trayectoria recorrida y planificada",
     "El software deberá presentar simultáneamente la trayectoria recorrida por la aeronave y la "
     "trayectoria planificada pendiente de recorrer.",
     "Menor", "Requisito de producto", "D", "IP"),

    # --- VID ---------------------------------------------------------------
    ("HLR-VID-001", "Recepción de video",
     "El software deberá recibir y presentar video en tiempo real procedente de fuentes RTSP, UDP "
     "con carga H.264 o H.265, TCP-MPEG2TS y dispositivos UVC locales.",
     "Mayor", "Requisito de producto", "D", "IP"),
    ("HLR-VID-002", "Latencia de video",
     "El software deberá presentar el video con una latencia extremo a extremo no superior a "
     "300 ms en modo de baja latencia, medida sobre el enlace de referencia.",
     "Mayor", "Requisito de producto", "T", "PL"),
    ("HLR-VID-003", "Grabación de video",
     "El software deberá grabar el video recibido en el soporte local, con marca temporal y "
     "control del espacio máximo ocupado.",
     "Menor", "NOM-107 6.4 (evidencia de la operación)", "D", "IP"),
    ("HLR-VID-004", "No interferencia del video",
     "La presentación de video no deberá ocultar ninguna alerta crítica ni degradar la "
     "presentación de la telemetría esencial, incluso en modo de pantalla completa.",
     "Crítico", "SORA OSO#20; DS-02", "D", "IV"),
    ("HLR-VID-005", "Control de carga útil orientable",
     "El software deberá permitir el control en acimut y elevación de la carga útil orientable "
     "cuando la aeronave declare dicha capacidad.",
     "Menor", "Requisito de producto", "D", "IP"),

    # --- RID ---------------------------------------------------------------
    ("HLR-RID-001", "Identificación del operador",
     "El software deberá permitir configurar y transmitir el identificador del operador conforme "
     "al formato definido en ASTM F3411-22a.",
     "Crítico", "ASTM F3411-22a; NOM-107 5.2", "T", "IP"),
    ("HLR-RID-002", "Autoidentificación y emergencia",
     "El software deberá permitir transmitir la autoidentificación de la operación y declarar el "
     "estado de emergencia de la aeronave.",
     "Crítico", "ASTM F3411-22a", "T", "IP"),
    ("HLR-RID-003", "Posición del puesto de pilotaje en Remote ID",
     "El software deberá suministrar la posición del puesto de pilotaje a los mensajes de "
     "identificación remota emitidos por la aeronave.",
     "Crítico", "ASTM F3411-22a", "T", "IP"),
    ("HLR-RID-004", "Estado del subsistema Remote ID",
     "El software deberá señalizar al piloto si el subsistema de identificación remota se "
     "encuentra activo, degradado o no disponible antes de autorizar el despegue.",
     "Crítico", "ASTM F3411-22a; SORA OSO#13", "D", "IP"),

    # --- UTM ---------------------------------------------------------------
    ("HLR-UTM-001", "Solicitud de autorización de vuelo",
     "El software deberá registrar la operación y solicitar la autorización de vuelo ante un "
     "proveedor de servicios UTM cuando la operación lo requiera.",
     "Mayor", "ASTM F3548-21; Reglamento (UE) 2021/664 (referencia)", "T", "PA"),
    ("HLR-UTM-002", "Presentación del estado de autorización",
     "El software deberá presentar el estado de la autorización de vuelo antes del despegue y "
     "durante toda la operación.",
     "Mayor", "ASTM F3548-21", "D", "PA"),
    ("HLR-UTM-003", "Notificación de inicio y fin",
     "El software deberá notificar al proveedor UTM el inicio y el fin efectivos de la operación.",
     "Mayor", "ASTM F3548-21", "T", "PA"),

    # --- HMI ---------------------------------------------------------------
    ("HLR-HMI-001", "Legibilidad en exteriores",
     "La interfaz deberá ser legible bajo luz solar directa y operable con guantes, con áreas "
     "activas de al menos 9 mm en su dimensión menor.",
     "Mayor", "SAE ARP4102/7; buenas prácticas HMI", "I", "IV"),
    ("HLR-HMI-002", "Codificación cromática",
     "La interfaz deberá emplear la convención aeronáutica de color (rojo para aviso, ámbar para "
     "precaución, verde y cian para información) y no deberá emplear el color como único "
     "codificador de una condición.",
     "Mayor", "SAE ARP4102/7; OACI Doc 9859", "I", "PA"),
    ("HLR-HMI-003", "Adaptación a la pantalla",
     "La interfaz deberá presentar la información crítica sin pérdida ni solapamiento en pantallas "
     "desde 7 pulgadas hasta 27 pulgadas de diagonal.",
     "Mayor", "Requisito de producto", "D", "IV"),
    ("HLR-HMI-004", "Idioma y unidades",
     "El software deberá permitir seleccionar el idioma de la interfaz y el sistema de unidades, "
     "incluyendo unidades aeronáuticas.",
     "Menor", "NOM-107 6.3", "D", "IP"),
    ("HLR-HMI-005", "Prioridad de las alertas",
     "Ninguna alerta crítica deberá quedar cubierta, desplazada ni truncada por otro elemento de "
     "la interfaz, cualquiera que sea la configuración de paneles activa.",
     "Crítico", "SORA OSO#20; SAE ARP4102/4", "D", "IV"),
    ("HLR-HMI-006", "Consola de mensajes",
     "El software deberá presentar una consola cronológica de mensajes MAVLink consultable durante "
     "el vuelo sin abandonar la vista de vuelo.",
     "Mayor", "Requisito derivado de la investigación de sucesos", "D", "IV"),

    # --- REG ---------------------------------------------------------------
    ("HLR-REG-001", "Registro del tráfico MAVLink",
     "El software deberá registrar la totalidad del tráfico MAVLink intercambiado con la aeronave, "
     "con marca temporal, en un archivo recuperable tras la operación.",
     "Crítico", "NOM-107 6.4; OACI Doc 9859 cap. 5", "T", "IP"),
    ("HLR-REG-002", "Registro de eventos de la aplicación",
     "El software deberá registrar los eventos internos relevantes y los errores detectados, con "
     "marca temporal e identificación del componente que los origina.",
     "Mayor", "DO-278A 6.5", "I", "IP"),
    ("HLR-REG-003", "Descarga de registros de la aeronave",
     "El software deberá permitir la descarga de los registros almacenados a bordo de la aeronave.",
     "Mayor", "NOM-107 6.4", "D", "IP"),
    ("HLR-REG-004", "Exportación para investigación",
     "Los registros deberán poder exportarse en un formato documentado y legible por herramientas "
     "de terceros, para su aportación en la investigación de sucesos.",
     "Crítico", "OACI Anexo 13; NOM-107 6.4", "D", "IP"),
    ("HLR-REG-005", "Preservación ante cierre inesperado",
     "El software deberá preservar los registros ya escritos ante un cierre inesperado de la "
     "aplicación o una pérdida de alimentación del equipo anfitrión.",
     "Crítico", "OACI Anexo 13; DS-03", "T", "PA"),

    # --- CFG ---------------------------------------------------------------
    ("HLR-CFG-001", "Gestión de parámetros",
     "El software deberá leer, presentar, modificar y escribir los parámetros de configuración de "
     "la aeronave, confirmando la escritura efectiva de cada valor modificado.",
     "Crítico", "SORA OSO#08; DO-278A 6.4", "T", "IP"),
    ("HLR-CFG-002", "Respaldo y restauración",
     "El software deberá permitir respaldar el conjunto completo de parámetros de la aeronave y "
     "restaurarlo posteriormente.",
     "Mayor", "SORA OSO#08", "D", "IP"),
    ("HLR-CFG-003", "Asistencia a la calibración",
     "El software deberá guiar la calibración de los sensores de la aeronave y de los mandos "
     "asociados, indicando el resultado de cada procedimiento.",
     "Mayor", "SORA OSO#08; NOM-107 7.3", "D", "IP"),
    ("HLR-CFG-004", "Persistencia de la configuración",
     "El software deberá conservar la configuración de la estación entre sesiones y declarar la "
     "versión del esquema de configuración almacenado.",
     "Menor", "DO-278A 7 (gestión de configuración)", "I", "IV"),
    ("HLR-CFG-005", "Identificación de versiones",
     "El software deberá presentar de forma inequívoca su propia versión y la versión del "
     "programa de la aeronave conectada.",
     "Crítico", "DO-278A 7.2; NOM-107 5.3", "I", "IV"),

    # --- PLT ---------------------------------------------------------------
    ("HLR-PLT-001", "Plataformas soportadas",
     "El software deberá ejecutarse sobre Windows 10 y 11 de 64 bits y sobre Android 9 o superior "
     "en arquitectura arm64-v8a, con idéntica funcionalidad operacional.",
     "Mayor", "Requisito de producto", "T", "IV"),
    ("HLR-PLT-002", "Tiempo de puesta en servicio",
     "El software deberá alcanzar el estado operativo en un plazo no superior a 30 segundos desde "
     "su arranque sobre el equipo de referencia.",
     "Mayor", "Requisito de producto", "T", "IP"),
    ("HLR-PLT-003", "Integridad del paquete de instalación",
     "El paquete de instalación deberá distribuirse firmado digitalmente con una identidad "
     "verificable por el usuario final.",
     "Crítico", "DO-326A; DO-278A 7.2", "I", "PA"),
    ("HLR-PLT-004", "Independencia de la conectividad",
     "El software deberá operar sin conexión a Internet, quedando degradadas únicamente las "
     "funciones que la requieran de forma explícita y declarada.",
     "Crítico", "NOM-107 6.1", "T", "IP"),
    ("HLR-PLT-005", "Degradación controlada",
     "El software deberá continuar operando cuando un recurso opcional no esté disponible, "
     "informando de la función pérdida y sin interrumpir el mando de la aeronave.",
     "Crítico", "DO-278A 2.2; DS-05", "T", "PA"),

    # --- SEC ---------------------------------------------------------------
    ("HLR-SEC-001", "Firma de mensajes MAVLink",
     "El software deberá admitir la firma de mensajes MAVLink 2.0 y rechazar los mensajes firmados "
     "cuya firma no sea válida.",
     "Crítico", "DO-326A; SORA OSO#13", "T", "PA"),
    ("HLR-SEC-002", "Protección de credenciales",
     "El software no deberá almacenar en claro las credenciales de acceso a servicios externos.",
     "Mayor", "DO-326A; ISO/IEC 27001 A.9", "I", "PA"),
    ("HLR-SEC-003", "Validación de canales seguros",
     "El software deberá validar la cadena de certificados de todo canal TLS establecido con "
     "servicios externos y rechazar la conexión si la validación falla.",
     "Mayor", "DO-326A", "T", "IP"),
    ("HLR-SEC-004", "Verificación de integridad en ejecución",
     "El software deberá verificar la integridad de sus componentes cargados dinámicamente antes "
     "de utilizarlos.",
     "Mayor", "DO-326A", "A", "PL"),
    ("HLR-SEC-005", "Registro de eventos de seguridad",
     "El software deberá registrar los intentos fallidos de conexión y de autenticación contra "
     "servicios externos.",
     "Menor", "DO-326A; ISO/IEC 27001 A.12.4", "I", "PA"),

    # --- PER ---------------------------------------------------------------
    ("HLR-PER-001", "Frecuencia de refresco",
     "La vista de vuelo deberá mantener una frecuencia de refresco no inferior a 30 imágenes por "
     "segundo sobre el equipo de referencia con un vehículo conectado.",
     "Mayor", "Requisito de producto", "T", "IP"),
    ("HLR-PER-002", "Capacidad de proceso de mensajes",
     "El software deberá procesar al menos 500 mensajes MAVLink por segundo sin descartar mensajes "
     "por saturación de sus colas internas.",
     "Crítico", "DO-278A 6.3.4", "T", "PL"),
    ("HLR-PER-003", "Consumo de memoria",
     "El software no deberá superar 1,5 GB de memoria residente en operación nominal con una "
     "aeronave conectada y una fuente de video activa.",
     "Mayor", "Requisito de producto", "T", "PL"),
    ("HLR-PER-004", "Estabilidad prolongada",
     "El software deberá operar durante al menos 4 horas continuas sin degradación acumulativa de "
     "su tiempo de respuesta ni crecimiento sostenido de memoria.",
     "Crítico", "DO-278A 6.3.4; SORA OSO#05", "T", "PL"),
]

# (id, hlr_padre, enunciado, componente de código, método, estado)
LLR = [
    # COM
    ("LLR-COM-001", "HLR-COM-001", "LinkManager deberá instanciar un objeto de enlace por cada configuración declarada y publicar su estado de conexión.", "src/Comms/LinkManager.cc", "T", "IP"),
    ("LLR-COM-002", "HLR-COM-001", "Cada implementación de LinkInterface deberá exponer un método de escritura no bloqueante y emitir los bytes recibidos por señal.", "src/Comms/LinkInterface.cc", "T", "IP"),
    ("LLR-COM-003", "HLR-COM-001", "SerialLink deberá reintentar la apertura del puerto ante desconexión física sin requerir intervención del usuario.", "src/Comms/SerialLink.cc", "T", "IP"),
    ("LLR-COM-004", "HLR-COM-001", "UDPLink y TCPLink deberán admitir la configuración de la dirección y el puerto remotos y validar su formato antes de conectar.", "src/Comms/UDPLink.cc, TCPLink.cc", "T", "IP"),
    ("LLR-COM-005", "HLR-COM-002", "VehicleLinkManager deberá mantener la lista de enlaces asociados a un vehículo y seleccionar el enlace primario según la última recepción válida.", "src/Vehicle/VehicleLinkManager.cc", "T", "IP"),
    ("LLR-COM-006", "HLR-COM-002", "La conmutación de enlace primario no deberá reiniciar la máquina de estados de conexión inicial del vehículo.", "src/Vehicle/InitialConnectStateMachine.cc", "T", "IP"),
    ("LLR-COM-007", "HLR-COM-003", "VehicleLinkManager deberá declarar perdido un enlace transcurrido el intervalo de vigilancia sin recepción y emitir la notificación correspondiente.", "src/Vehicle/VehicleLinkManager.cc", "T", "IV"),
    ("LLR-COM-008", "HLR-COM-003", "La pérdida de todos los enlaces de un vehículo deberá generar una alerta de severidad de aviso en la vista de vuelo.", "src/FlightDisplay/VehicleWarnings.qml", "D", "IV"),
    ("LLR-COM-009", "HLR-COM-004", "MultiVehicleManager deberá crear una instancia de Vehicle por cada identificador de sistema detectado y mantener la referencia al vehículo activo.", "src/Vehicle/MultiVehicleManager.cc", "T", "IP"),
    ("LLR-COM-010", "HLR-COM-004", "El encaminamiento de mandos deberá dirigirse exclusivamente al identificador de sistema del vehículo activo.", "src/Vehicle/Vehicle.cc", "T", "IP"),
    ("LLR-COM-011", "HLR-COM-005", "QGCSerialPortInfo deberá identificar la placa conectada a partir de la tabla de identificadores USB declarada en USBBoardInfo.json.", "src/Comms/QGCSerialPortInfo.cc", "T", "IP"),
    ("LLR-COM-012", "HLR-COM-005", "La conexión automática deberá poder desactivarse de forma independiente por cada tipo de dispositivo.", "src/Settings/AutoConnect.SettingsGroup.json", "I", "IP"),
    ("LLR-COM-013", "HLR-COM-006", "MAVLinkProtocol deberá descartar toda trama cuya suma de comprobación no coincida e incrementar el contador de pérdidas.", "src/Comms/MAVLinkProtocol.cc", "T", "IP"),
    ("LLR-COM-014", "HLR-COM-006", "El contador de mensajes perdidos deberá exponerse a la interfaz para su presentación como indicador de calidad de enlace.", "src/Comms/MAVLinkProtocol.cc", "T", "IP"),
    ("LLR-COM-015", "HLR-COM-007", "LogReplayLink deberá operar en modo de solo lectura y no deberá registrar ningún escritor sobre enlaces activos.", "src/Comms/LogReplayLink.cc", "T", "IP"),
    ("LLR-COM-016", "HLR-COM-007", "La reproducción deberá respetar las marcas temporales del registro y admitir control de velocidad y posición.", "src/Comms/LogReplayLinkController.cc", "D", "IP"),

    # TEL
    ("LLR-TEL-001", "HLR-TEL-001", "Vehicle deberá exponer los grupos de hechos de actitud, posición global, velocidad, batería y GPS actualizados desde los mensajes MAVLink correspondientes.", "src/Vehicle/FactGroups/", "T", "IV"),
    ("LLR-TEL-002", "HLR-TEL-001", "TelemetryValuesBar deberá presentar los valores seleccionados por el usuario con su unidad y precisión declaradas en los metadatos del hecho.", "src/FlightDisplay/TelemetryValuesBar.qml", "D", "IV"),
    ("LLR-TEL-003", "HLR-TEL-002", "QGCAttitudeWidget deberá representar cabeceo y balanceo con la línea de horizonte móvil y la escala de cabeceo graduada.", "src/FlightMap/Widgets/", "D", "IV"),
    ("LLR-TEL-004", "HLR-TEL-002", "El instrumento por defecto de la vista de vuelo deberá incluir indicador de actitud e indicador de rumbo simultáneos.", "src/FlightMap/Widgets/VerticalCompassAttitude.qml", "I", "IV"),
    ("LLR-TEL-005", "HLR-TEL-003", "La consola deberá asociar a cada valor de MAV_SEVERITY un color y una etiqueta de texto fijos, de modo que la severidad sea legible sin depender del color.", "src/FlightDisplay/FlyViewMavlinkConsole.qml", "I", "IV"),
    ("LLR-TEL-006", "HLR-TEL-003", "La consola deberá conservar los mensajes en orden de recepción con marca temporal local de resolución de segundo.", "src/FlightDisplay/FlyViewMavlinkConsole.qml", "D", "IV"),
    ("LLR-TEL-007", "HLR-TEL-003", "El indicador de telemetría periódica deberá emitir una línea únicamente cuando una magnitud supere su umbral de cambio o transcurra el intervalo de latido, para no enmascarar los mensajes de la aeronave.", "src/FlightDisplay/FlyViewMavlinkConsole.qml", "T", "IV"),
    ("LLR-TEL-008", "HLR-TEL-004", "VehicleWarnings deberá presentar las condiciones críticas comunicadas por la aeronave sin que el usuario pueda desactivar su presentación.", "src/FlightDisplay/VehicleWarnings.qml", "D", "IV"),
    ("LLR-TEL-009", "HLR-TEL-005", "El grupo de hechos del enlace deberá exponer intensidad de señal y porcentaje de pérdida cuando la aeronave los comunique.", "src/Vehicle/FactGroups/", "T", "IP"),
    ("LLR-TEL-010", "HLR-TEL-006", "El indicador GNSS deberá cambiar a codificación de precaución cuando el número de satélites sea inferior al mínimo configurado.", "src/FlightDisplay/FlyViewMavlinkConsole.qml", "D", "IV"),

    # MIS
    ("LLR-MIS-001", "HLR-MIS-001", "PlanMasterController deberá coordinar los controladores de misión, geocerca y puntos de recuperación sobre un único plan.", "src/MissionManager/PlanMasterController.cc", "T", "IP"),
    ("LLR-MIS-002", "HLR-MIS-001", "MissionController deberá validar el tipo y el rango de cada parámetro de un elemento de misión antes de aceptarlo.", "src/MissionManager/MissionController.cc", "T", "IP"),
    ("LLR-MIS-003", "HLR-MIS-002", "MissionManager deberá implementar el protocolo de transferencia MAVLink Mission con reintento y confirmación de conteo de elementos.", "src/MissionManager/MissionManager.cc", "T", "IP"),
    ("LLR-MIS-004", "HLR-MIS-002", "Una transferencia incompleta deberá notificarse como error y no deberá dejar el plan marcado como sincronizado.", "src/MissionManager/MissionManager.cc", "T", "IP"),
    ("LLR-MIS-005", "HLR-MIS-003", "La lectura del plan residente deberá cotejar elemento a elemento y marcar las diferencias en la interfaz.", "src/MissionManager/PlanMasterController.cc", "T", "IP"),
    ("LLR-MIS-006", "HLR-MIS-004", "La validación del plan deberá rechazar todo elemento cuya altura supere el límite configurado.", "src/MissionManager/MissionController.cc", "T", "PA"),
    ("LLR-MIS-007", "HLR-MIS-004", "La validación del plan deberá rechazar todo elemento situado fuera de una geocerca de inclusión o dentro de una de exclusión.", "src/MissionManager/GeoFenceController.cc", "T", "PA"),
    ("LLR-MIS-008", "HLR-MIS-005", "MissionController deberá calcular distancia acumulada, duración estimada y altura máxima y actualizarlas ante cualquier edición del plan.", "src/MissionManager/MissionController.cc", "T", "IP"),
    ("LLR-MIS-009", "HLR-MIS-006", "SurveyComplexItem y CorridorScanComplexItem deberán generar la traza de barrido a partir del polígono y de los parámetros ópticos declarados en CameraCalc.", "src/MissionManager/SurveyComplexItem.cc", "T", "IP"),
    ("LLR-MIS-010", "HLR-MIS-007", "El plan deberá serializarse en JSON con número de versión del esquema y deserializarse rechazando versiones no soportadas.", "src/MissionManager/PlanMasterController.cc", "T", "IP"),
    ("LLR-MIS-011", "HLR-MIS-007", "KMLPlanDomDocument deberá exportar la geometría del plan en KML válido según el esquema OGC.", "src/MissionManager/KMLPlanDomDocument.cc", "T", "IP"),

    # SAF
    ("LLR-SAF-001", "HLR-SAF-001", "GeoFenceController deberá admitir polígonos y círculos de inclusión y exclusión y validar que cada polígono sea simple y cerrado.", "src/MissionManager/GeoFenceController.cc", "T", "IP"),
    ("LLR-SAF-002", "HLR-SAF-001", "GeoFenceManager deberá transferir la geocerca a la aeronave y confirmar el número de elementos aceptados.", "src/MissionManager/GeoFenceManager.cc", "T", "IP"),
    ("LLR-SAF-003", "HLR-SAF-002", "RallyPointController deberá admitir la definición de puntos de recuperación con altura asociada y transferirlos a la aeronave.", "src/MissionManager/RallyPointController.cc", "T", "IP"),
    ("LLR-SAF-004", "HLR-SAF-003", "GuidedActionsController deberá enrutar toda acción de vuelo a través de un diálogo de confirmación antes de emitir el mando.", "src/FlightDisplay/GuidedActionsController.qml", "T", "IV"),
    ("LLR-SAF-005", "HLR-SAF-003", "El diálogo de confirmación deberá identificar la acción solicitada y requerir un gesto deliberado, no un único toque sobre el control que la originó.", "src/FlightDisplay/GuidedActionConfirm.qml", "D", "IV"),
    ("LLR-SAF-006", "HLR-SAF-004", "La acción de retorno deberá estar presente en la barra de acciones de la vista de vuelo siempre que el vehículo esté armado.", "src/FlightDisplay/GuidedActionsController.qml", "D", "IV"),
    ("LLR-SAF-007", "HLR-SAF-005", "Las advertencias de precondición deberán presentarse en una capa superior a la del video y a la de los paneles de instrumentos.", "src/FlightDisplay/FlyViewWidgetLayer.qml", "I", "IV"),
    ("LLR-SAF-008", "HLR-SAF-006", "Las acciones guiadas deberán deshabilitarse cuando el vehículo no tenga enlace activo y presentar el motivo al piloto.", "src/FlightDisplay/GuidedActionsController.qml", "T", "IP"),
    ("LLR-SAF-009", "HLR-SAF-007", "La vista de configuración de seguridad deberá presentar los parámetros de protección vigentes leídos de la aeronave, no valores por defecto locales.", "src/AutoPilotPlugins/", "D", "IP"),
    ("LLR-SAF-010", "HLR-SAF-008", "La terminación de vuelo deberá requerir una confirmación adicional distinta del resto de acciones guiadas.", "src/FlightDisplay/GuidedActionsController.qml", "T", "PA"),

    # SIT
    ("LLR-SIT-001", "HLR-SIT-001", "FlightMap deberá presentar la aeronave en su posición global con el rumbo indicado por el mensaje de actitud.", "src/FlightMap/", "D", "IV"),
    ("LLR-SIT-002", "HLR-SIT-002", "El gestor de cartografía sin conexión deberá servir las teselas descargadas desde el almacén local cuando no haya red disponible.", "src/QtLocationPlugin/", "T", "IP"),
    ("LLR-SIT-003", "HLR-SIT-002", "La ausencia de red no deberá bloquear ninguna operación de la capa de comunicaciones ni de la capa de aplicación.", "src/QtLocationPlugin/", "T", "IP"),
    ("LLR-SIT-004", "HLR-SIT-003", "TerrainQuery deberá obtener la elevación del terreno para la traza planificada y almacenarla en caché local.", "src/Terrain/TerrainQuery.cc", "T", "IP"),
    ("LLR-SIT-005", "HLR-SIT-004", "ADSBVehicleManager deberá mantener la lista de aeronaves detectadas y eliminar las que superen el tiempo de vigencia sin actualización.", "src/ADSB/ADSBVehicleManager.cc", "T", "IP"),
    ("LLR-SIT-006", "HLR-SIT-005", "PositionManager deberá seleccionar la mejor fuente de posición disponible del equipo anfitrión y publicar su exactitud declarada.", "src/PositionManager/", "T", "IP"),
    ("LLR-SIT-007", "HLR-SIT-006", "TrajectoryPoints deberá acumular la traza recorrida limitando el número de puntos para no degradar el refresco de la vista.", "src/Vehicle/TrajectoryPoints.cc", "T", "IP"),

    # VID
    ("LLR-VID-001", "HLR-VID-001", "VideoManager deberá instanciar el receptor correspondiente al tipo de fuente configurado y publicar su estado de recepción.", "src/VideoManager/VideoManager.cc", "T", "IP"),
    ("LLR-VID-002", "HLR-VID-001", "El receptor GStreamer deberá reconstruir la tubería ante pérdida de la fuente y reintentar la conexión con el periodo configurado.", "src/VideoManager/VideoReceiver/GStreamer/", "T", "IP"),
    ("LLR-VID-003", "HLR-VID-002", "El modo de baja latencia deberá limitar el almacenamiento intermedio de la tubería al mínimo compatible con la decodificación.", "src/VideoManager/VideoReceiver/GStreamer/", "T", "PL"),
    ("LLR-VID-004", "HLR-VID-003", "La grabación deberá detenerse automáticamente al alcanzar el límite de espacio configurado y notificarlo al usuario.", "src/VideoManager/VideoManager.cc", "T", "IP"),
    ("LLR-VID-005", "HLR-VID-004", "La capa de video deberá situarse por debajo de la capa de alertas en el orden de apilamiento de la vista de vuelo.", "src/FlightDisplay/FlyViewWidgetLayer.qml", "I", "IV"),
    ("LLR-VID-006", "HLR-VID-004", "Los paneles superpuestos sobre el video deberán declarar su área ocupada al sistema de márgenes para no solaparse entre sí.", "src/FlightDisplay/FlyViewWidgetLayer.qml", "T", "IV"),
    ("LLR-VID-007", "HLR-VID-005", "GimbalController deberá emitir los mandos de orientación únicamente cuando la aeronave declare la capacidad correspondiente.", "src/Gimbal/GimbalController.cc", "T", "IP"),

    # RID
    ("LLR-RID-001", "HLR-RID-001", "RemoteIDManager deberá validar el formato del identificador de operador antes de habilitar su transmisión.", "src/Vehicle/RemoteIDManager.cc", "T", "IP"),
    ("LLR-RID-002", "HLR-RID-002", "RemoteIDManager deberá transmitir la autoidentificación y el estado de emergencia con la cadencia exigida por la norma.", "src/Vehicle/RemoteIDManager.cc", "T", "IP"),
    ("LLR-RID-003", "HLR-RID-003", "RemoteIDManager deberá obtener la posición del puesto de pilotaje de PositionManager y no de la última posición conocida de la aeronave.", "src/Vehicle/RemoteIDManager.cc", "T", "IP"),
    ("LLR-RID-004", "HLR-RID-004", "El indicador de Remote ID deberá distinguir visualmente los estados activo, degradado y no disponible.", "src/QmlControls/RemoteIDIndicatorPage.qml", "D", "IP"),

    # UTM
    ("LLR-UTM-001", "HLR-UTM-001", "UTMSPFlightPlanManager deberá construir la solicitud de plan de vuelo a partir del plan activo y del volumen de operación declarado.", "src/UTMSP/UTMSPFlightPlanManager.cpp", "T", "PA"),
    ("LLR-UTM-002", "HLR-UTM-001", "UTMSPAuthorization deberá gestionar la obtención y renovación del testigo de acceso al proveedor.", "src/UTMSP/UTMSPAuthorization.cpp", "T", "PA"),
    ("LLR-UTM-003", "HLR-UTM-002", "El indicador de estado de la operación deberá reflejar el resultado de la última consulta al proveedor con su marca temporal.", "src/UTMSP/UTMSPFlightStatusIndicator.qml", "D", "PA"),
    ("LLR-UTM-004", "HLR-UTM-003", "UTMSPBlenderRestInterface deberá notificar el inicio y el fin de la operación y registrar el resultado de cada notificación.", "src/UTMSP/UTMSPBlenderRestInterface.cpp", "T", "PA"),

    # HMI
    ("LLR-HMI-001", "HLR-HMI-001", "ScreenTools deberá derivar todas las dimensiones de la interfaz de la métrica de fuente del dispositivo, sin dimensiones absolutas en píxeles.", "src/QmlControls/ScreenTools.qml", "I", "IV"),
    ("LLR-HMI-002", "HLR-HMI-001", "Los controles interactivos deberán dimensionarse a partir de la altura de fuente por defecto, garantizando el área mínima activa exigida.", "src/QmlControls/ScreenTools.qml", "I", "IV"),
    ("LLR-HMI-003", "HLR-HMI-002", "QGCPalette deberá definir los colores de aviso, precaución e información como entradas únicas reutilizadas por toda la interfaz.", "src/QmlControls/QGCPalette.cc", "I", "IV"),
    ("LLR-HMI-004", "HLR-HMI-002", "Toda condición codificada por color deberá acompañarse de una etiqueta de texto o de un icono distintivo.", "src/FlightDisplay/", "I", "PA"),
    ("LLR-HMI-005", "HLR-HMI-003", "Los instrumentos de la vista de vuelo deberán acotar su tamaño contra la altura de la ventana para no desbordarla en pantallas de alta densidad.", "src/FlightMap/Widgets/VerticalCompassAttitude.qml", "T", "IV"),
    ("LLR-HMI-006", "HLR-HMI-003", "Los gráficos de sintonía y de análisis deberán adoptar el tamaño disponible mediante sugerencias de disposición y no mediante dimensiones fijas.", "src/QmlControls/PIDTuning.qml", "T", "IV"),
    ("LLR-HMI-007", "HLR-HMI-004", "SettingsManager deberá exponer la selección de idioma y de sistema de unidades y aplicarla sin reiniciar la aplicación cuando sea posible.", "src/Settings/", "D", "IP"),
    ("LLR-HMI-008", "HLR-HMI-005", "El orden de apilamiento de la vista de vuelo deberá situar las alertas por encima de cualquier panel, video o diálogo no modal.", "src/FlightDisplay/FlyViewWidgetLayer.qml", "I", "IV"),
    ("LLR-HMI-009", "HLR-HMI-006", "La consola de mensajes deberá ocupar una fracción fija de la vista, ser plegable y declarar su área al sistema de márgenes.", "src/FlightDisplay/FlyViewMavlinkConsole.qml", "D", "IV"),
    ("LLR-HMI-010", "HLR-HMI-006", "La consola deberá ocultarse cuando el video se presente en pantalla completa, para no reducir el área útil de la fuente de video.", "src/FlightDisplay/FlyViewWidgetLayer.qml", "T", "IV"),

    # REG
    ("LLR-REG-001", "HLR-REG-001", "MAVLinkLogManager deberá abrir un registro por sesión de vuelo y escribir cada trama recibida con su marca temporal.", "src/Vehicle/MAVLinkLogManager.cc", "T", "IP"),
    ("LLR-REG-002", "HLR-REG-001", "El registro deberá nombrarse de forma unívoca incluyendo fecha y hora de inicio de la sesión.", "src/Vehicle/MAVLinkLogManager.cc", "I", "IP"),
    ("LLR-REG-003", "HLR-REG-002", "El subsistema de registro de la aplicación deberá categorizar los mensajes por componente y nivel de severidad.", "src/Utilities/", "I", "IP"),
    ("LLR-REG-004", "HLR-REG-003", "La descarga de registros de la aeronave deberá emplear el protocolo de transferencia de archivos MAVLink y verificar el tamaño recibido.", "src/Vehicle/FTPManager.cc", "T", "IP"),
    ("LLR-REG-005", "HLR-REG-004", "El formato del registro deberá ser el formato .tlog documentado, sin transformaciones propietarias que impidan su lectura por herramientas de terceros.", "src/Vehicle/MAVLinkLogManager.cc", "I", "IP"),
    ("LLR-REG-006", "HLR-REG-005", "El registro deberá vaciarse a disco con una periodicidad acotada, de modo que un cierre inesperado no comprometa más que el último intervalo.", "src/Vehicle/MAVLinkLogManager.cc", "T", "PA"),

    # CFG
    ("LLR-CFG-001", "HLR-CFG-001", "ParameterManager deberá mantener la tabla completa de parámetros de la aeronave y su estado de sincronización individual.", "src/FactSystem/ParameterManager.cc", "T", "IP"),
    ("LLR-CFG-002", "HLR-CFG-001", "Toda escritura de parámetro deberá confirmarse releyendo el valor efectivo desde la aeronave antes de marcarlo como aplicado.", "src/FactSystem/ParameterManager.cc", "T", "IP"),
    ("LLR-CFG-003", "HLR-CFG-001", "Los metadatos de cada parámetro deberán acotar el rango admisible y la interfaz deberá impedir la introducción de valores fuera de rango.", "src/FactSystem/FactMetaData.cc", "T", "IP"),
    ("LLR-CFG-004", "HLR-CFG-002", "El respaldo de parámetros deberá almacenar identificador de aeronave, versión de programa y marca temporal junto con los valores.", "src/FactSystem/ParameterManager.cc", "T", "IP"),
    ("LLR-CFG-005", "HLR-CFG-003", "Los asistentes de calibración deberán presentar el resultado comunicado por la aeronave y no declarar éxito sin confirmación de esta.", "src/AutoPilotPlugins/", "D", "IP"),
    ("LLR-CFG-006", "HLR-CFG-004", "La configuración de la estación deberá almacenar el número de versión del esquema y descartarse de forma controlada al detectar una versión incompatible.", "src/Settings/SettingsManager.cc", "I", "IV"),
    ("LLR-CFG-007", "HLR-CFG-005", "La versión de la aplicación deberá derivarse del sistema de control de versiones en el momento de la compilación y no editarse manualmente.", "cmake/Git.cmake", "I", "IV"),
    ("LLR-CFG-008", "HLR-CFG-005", "La versión de programa de la aeronave conectada deberá presentarse junto con su identificador de plataforma.", "src/Vehicle/Vehicle.cc", "D", "IV"),

    # PLT
    ("LLR-PLT-001", "HLR-PLT-001", "La compilación deberá producir artefactos para Windows x64 y para Android arm64-v8a a partir del mismo árbol de fuentes, sin ramas divergentes.", "CMakeLists.txt", "I", "IV"),
    ("LLR-PLT-002", "HLR-PLT-001", "El paquete de Windows deberá incluir la totalidad de los complementos QML y de las bibliotecas de video requeridos en ejecución.", "deploy/windows/", "T", "IV"),
    ("LLR-PLT-003", "HLR-PLT-002", "La pantalla de presentación deberá indicar el progreso de la inicialización y ceder el control a la ventana principal al concluir.", "src/UI/OtechSplashScreen.qml", "D", "IV"),
    ("LLR-PLT-004", "HLR-PLT-003", "El artefacto distribuible deberá firmarse con el certificado de la organización como paso obligatorio del procedimiento de publicación.", "deploy/", "I", "PL"),
    ("LLR-PLT-005", "HLR-PLT-004", "Ninguna función de mando o de telemetría deberá depender de una consulta de red para completarse.", "src/Comms/", "A", "IP"),
    ("LLR-PLT-006", "HLR-PLT-005", "La ausencia del entorno de ejecución de video deberá desactivar únicamente las funciones de video, dejando operativo el resto de la aplicación.", "src/VideoManager/VideoManager.cc", "T", "PA"),
    ("LLR-PLT-007", "HLR-PLT-005", "La ausencia de un componente opcional en la aeronave no deberá provocar el acceso a referencias no inicializadas.", "src/Vehicle/Vehicle.cc", "T", "IV"),

    # SEC
    ("LLR-SEC-001", "HLR-SEC-001", "MAVLinkProtocol deberá verificar la firma de los mensajes que la incorporen y descartar los que no la superen.", "src/Comms/MAVLinkProtocol.cc", "T", "PA"),
    ("LLR-SEC-002", "HLR-SEC-002", "Las credenciales de servicios externos deberán almacenarse mediante el almacén seguro de la plataforma anfitriona.", "src/Settings/", "I", "PL"),
    ("LLR-SEC-003", "HLR-SEC-003", "Toda petición a servicios externos deberá emplear TLS con validación de cadena de certificados activa.", "src/UTMSP/, src/Terrain/", "T", "IP"),
    ("LLR-SEC-004", "HLR-SEC-004", "Deberá definirse y ejecutarse un análisis de integridad de los componentes cargados dinámicamente en el arranque.", "deploy/", "A", "PL"),
    ("LLR-SEC-005", "HLR-SEC-005", "Los fallos de conexión y de autenticación contra servicios externos deberán registrarse con marca temporal y motivo.", "src/UTMSP/UTMSPLogger.h", "I", "PA"),

    # PER
    ("LLR-PER-001", "HLR-PER-001", "La vista de vuelo no deberá contener expresiones de dimensión mutuamente dependientes que provoquen ciclos de reevaluación en cada fotograma.", "src/FlightDisplay/", "A", "IV"),
    ("LLR-PER-002", "HLR-PER-001", "El número de puntos de traza representados deberá acotarse para mantener constante el coste de dibujado.", "src/Vehicle/TrajectoryPoints.cc", "T", "IP"),
    ("LLR-PER-003", "HLR-PER-002", "La recepción de mensajes deberá desacoplarse del hilo de interfaz mediante colas acotadas con política de descarte declarada.", "src/Comms/MAVLinkProtocol.cc", "T", "PL"),
    ("LLR-PER-004", "HLR-PER-003", "El consumo de memoria deberá medirse en el escenario de referencia y registrarse como línea base de cada versión.", "test/", "T", "PL"),
    ("LLR-PER-005", "HLR-PER-004", "Deberá ejecutarse una prueba de resistencia de 4 horas con registro periódico de memoria y de tiempo de respuesta.", "test/", "T", "PL"),
]

# (id, hlr cubierto, título, nivel, método, entorno, criterio de aceptación)
VER = [
    ("VER-001", "HLR-COM-001", "Conexión sobre los cuatro tipos de enlace", "Sistema", "T", "HIL + MockLink",
     "Se establece comunicación bidireccional y se reciben mensajes HEARTBEAT en los cuatro transportes."),
    ("VER-002", "HLR-COM-002", "Conmutación de enlace primario", "Sistema", "T", "HIL con doble enlace",
     "Al interrumpir el enlace primario el mando permanece disponible sin reconexión manual."),
    ("VER-003", "HLR-COM-003", "Detección de pérdida de enlace", "Sistema", "T", "HIL",
     "La notificación se presenta antes de 5 s desde la última trama válida."),
    ("VER-004", "HLR-COM-004", "Segregación multiaeronave", "Sistema", "T", "MockLink, 3 vehículos",
     "La telemetría y los mandos no se cruzan entre identificadores de sistema."),
    ("VER-005", "HLR-COM-005", "Reconocimiento de dispositivos serie", "Integración", "D", "Banco",
     "Las placas declaradas se conectan automáticamente; la función es desactivable."),
    ("VER-006", "HLR-COM-006", "Rechazo de tramas corruptas", "Unitario", "T", "test/Comms",
     "Toda trama con suma de comprobación inválida se descarta y se contabiliza."),
    ("VER-007", "HLR-COM-007", "Aislamiento de la reproducción", "Integración", "T", "Banco + analizador",
     "Durante la reproducción no se observa tráfico saliente en ningún enlace activo."),
    ("VER-008", "HLR-TEL-001", "Presentación de telemetría esencial", "Sistema", "D", "HIL PX4",
     "Las nueve magnitudes esenciales se presentan y se actualizan de forma continua."),
    ("VER-009", "HLR-TEL-002", "Conformidad del indicador de actitud", "Sistema", "D", "HIL PX4",
     "El horizonte responde en el sentido correcto en cabeceo y balanceo en todo el rango."),
    ("VER-010", "HLR-TEL-003", "Codificación de severidad de mensajes", "Sistema", "D", "HIL PX4",
     "Los ocho niveles MAV_SEVERITY se distinguen por color y por etiqueta de texto."),
    ("VER-011", "HLR-TEL-004", "Alertas de condición crítica", "Sistema", "T", "HIL con inyección de fallos",
     "Cada condición crítica inyectada genera una alerta visible y no suprimible."),
    ("VER-012", "HLR-TEL-005", "Indicadores de calidad de enlace", "Integración", "D", "Banco con radio",
     "Se presentan intensidad de señal y pérdida de paquetes coherentes con el enlace real."),
    ("VER-013", "HLR-TEL-006", "Indicación de estado GNSS", "Sistema", "D", "HIL PX4",
     "Con menos satélites que el mínimo el indicador adopta codificación de precaución."),
    ("VER-014", "HLR-MIS-001", "Edición y validación de plan", "Sistema", "D", "Escritorio",
     "Se crea, edita y almacena un plan; los parámetros fuera de rango se rechazan."),
    ("VER-015", "HLR-MIS-002", "Transferencia íntegra del plan", "Sistema", "T", "HIL PX4",
     "El plan cargado coincide elemento a elemento con el plan de la estación."),
    ("VER-016", "HLR-MIS-003", "Cotejo del plan residente", "Sistema", "T", "HIL PX4",
     "Una modificación introducida a bordo se señala como discrepancia."),
    ("VER-017", "HLR-MIS-004", "Rechazo de plan fuera de límites", "Sistema", "T", "HIL PX4",
     "Un plan que excede la altura máxima o sale de la geocerca es rechazado con motivo explícito."),
    ("VER-018", "HLR-MIS-005", "Cálculo de parámetros de misión", "Unitario", "T", "test/MissionManager",
     "Distancia, duración y altura máxima coinciden con el cálculo de referencia."),
    ("VER-019", "HLR-MIS-006", "Generación de patrones de barrido", "Unitario", "T", "test/MissionManager",
     "La traza generada cubre el polígono con el solape declarado."),
    ("VER-020", "HLR-MIS-007", "Intercambio de planes", "Integración", "D", "Escritorio",
     "El plan exportado se reimporta sin pérdida y el KML abre en una herramienta de terceros."),
    ("VER-021", "HLR-SAF-001", "Definición y transferencia de geocerca", "Sistema", "T", "HIL PX4",
     "La geocerca transferida coincide con la definida y la aeronave la reconoce."),
    ("VER-022", "HLR-SAF-002", "Puntos de recuperación", "Sistema", "T", "HIL PX4",
     "Los puntos transferidos coinciden en posición y altura con los definidos."),
    ("VER-023", "HLR-SAF-003", "Confirmación de mandos críticos", "Sistema", "T", "HIL PX4",
     "Ningún mando de vuelo se emite sin confirmación explícita previa."),
    ("VER-024", "HLR-SAF-004", "Accesibilidad del retorno", "Sistema", "D", "HIL PX4",
     "El retorno se activa en dos acciones o menos desde la vista de vuelo."),
    ("VER-025", "HLR-SAF-005", "Persistencia de las advertencias", "Sistema", "D", "HIL PX4",
     "La advertencia de precondición permanece visible mientras la condición persiste."),
    ("VER-026", "HLR-SAF-006", "Inhibición sin enlace", "Sistema", "T", "HIL PX4",
     "Sin enlace válido los mandos quedan deshabilitados y se indica la causa."),
    ("VER-027", "HLR-SAF-007", "Presentación de modos de protección", "Sistema", "D", "HIL PX4",
     "Los valores presentados coinciden con los leídos de la aeronave."),
    ("VER-028", "HLR-SAF-008", "Terminación de vuelo", "Sistema", "T", "HIL PX4",
     "La terminación exige confirmación reforzada y solo se ofrece si la aeronave la declara."),
    ("VER-029", "HLR-SIT-001", "Presentación cartográfica", "Sistema", "D", "Escritorio",
     "La posición presentada coincide con la coordenada comunicada dentro de la tolerancia declarada."),
    ("VER-030", "HLR-SIT-002", "Operación sin conexión", "Sistema", "T", "Escritorio sin red",
     "Sin red se conserva la cartografía descargada y ninguna función de mando se degrada."),
    ("VER-031", "HLR-SIT-003", "Perfil de terreno", "Integración", "D", "Escritorio",
     "El perfil presentado coincide con los datos de elevación de referencia."),
    ("VER-032", "HLR-SIT-004", "Presentación de tránsito ADS-B", "Integración", "D", "Banco con receptor",
     "Las aeronaves detectadas se presentan con identificación y altitud y caducan al perder la señal."),
    ("VER-033", "HLR-SIT-005", "Posición del puesto de pilotaje", "Integración", "D", "Radio Android",
     "La posición presentada coincide con la del receptor GNSS del equipo."),
    ("VER-034", "HLR-SIT-006", "Trayectorias recorrida y planificada", "Sistema", "D", "HIL PX4",
     "Ambas trayectorias se distinguen y se actualizan de forma continua."),
    ("VER-035", "HLR-VID-001", "Recepción de las cuatro fuentes de video", "Integración", "D", "Banco",
     "Cada tipo de fuente se presenta con imagen estable."),
    ("VER-036", "HLR-VID-002", "Medida de latencia de video", "Sistema", "T", "Banco con cronómetro óptico",
     "La latencia medida no supera 300 ms en modo de baja latencia."),
    ("VER-037", "HLR-VID-003", "Grabación y límite de espacio", "Integración", "D", "Banco",
     "La grabación se detiene al alcanzar el límite y el archivo resultante es reproducible."),
    ("VER-038", "HLR-VID-004", "No interferencia del video", "Sistema", "D", "HIL PX4 con video",
     "Con video a pantalla completa las alertas críticas siguen siendo visibles."),
    ("VER-039", "HLR-VID-005", "Control de carga útil orientable", "Integración", "D", "Banco con gimbal",
     "Los mandos de acimut y elevación producen el movimiento esperado."),
    ("VER-040", "HLR-RID-001", "Identificador de operador", "Sistema", "T", "HIL con Remote ID",
     "El identificador transmitido coincide con el configurado y el formato inválido se rechaza."),
    ("VER-041", "HLR-RID-002", "Autoidentificación y emergencia", "Sistema", "T", "HIL con Remote ID",
     "La autoidentificación y el estado de emergencia se transmiten con la cadencia exigida."),
    ("VER-042", "HLR-RID-003", "Posición del puesto en Remote ID", "Sistema", "T", "HIL con Remote ID",
     "La posición transmitida corresponde al puesto de pilotaje y no a la aeronave."),
    ("VER-043", "HLR-RID-004", "Estado del subsistema Remote ID", "Sistema", "D", "HIL con Remote ID",
     "Los tres estados se distinguen y el estado no disponible se advierte antes del despegue."),
    ("VER-044", "HLR-UTM-001", "Solicitud de autorización", "Integración", "T", "Proveedor UTM de pruebas",
     "La solicitud se acepta y el identificador de operación se almacena."),
    ("VER-045", "HLR-UTM-002", "Estado de autorización", "Integración", "D", "Proveedor UTM de pruebas",
     "El estado presentado coincide con el del proveedor y se refresca durante la operación."),
    ("VER-046", "HLR-UTM-003", "Notificación de inicio y fin", "Integración", "T", "Proveedor UTM de pruebas",
     "Ambas notificaciones se emiten y su resultado queda registrado."),
    ("VER-047", "HLR-HMI-001", "Legibilidad y área activa", "Sistema", "I", "Radio SIYI en exteriores",
     "Todos los controles superan el área mínima y son legibles bajo luz solar directa."),
    ("VER-048", "HLR-HMI-002", "Codificación cromática", "Sistema", "I", "Revisión de diseño",
     "Los colores siguen la convención y ninguna condición depende solo del color."),
    ("VER-049", "HLR-HMI-003", "Adaptación a la pantalla", "Sistema", "D", "7\" a 27\"",
     "Sin pérdida ni solapamiento de información crítica en todo el rango de pantallas."),
    ("VER-050", "HLR-HMI-004", "Idioma y unidades", "Sistema", "D", "Escritorio",
     "Los cambios se aplican en toda la interfaz de forma coherente."),
    ("VER-051", "HLR-HMI-005", "Prioridad de las alertas", "Sistema", "D", "HIL PX4",
     "Ninguna configuración de paneles llega a cubrir una alerta crítica."),
    ("VER-052", "HLR-HMI-006", "Consola de mensajes en vuelo", "Sistema", "D", "HIL PX4",
     "La consola presenta los mensajes en orden y es consultable sin abandonar la vista de vuelo."),
    ("VER-053", "HLR-REG-001", "Registro íntegro del tráfico", "Sistema", "T", "HIL PX4",
     "El registro contiene la totalidad de las tramas de la sesión con marca temporal."),
    ("VER-054", "HLR-REG-002", "Registro de eventos internos", "Integración", "I", "Escritorio",
     "Los eventos relevantes aparecen categorizados por componente y severidad."),
    ("VER-055", "HLR-REG-003", "Descarga de registros de la aeronave", "Sistema", "D", "HIL PX4",
     "El registro descargado coincide en tamaño y contenido con el de a bordo."),
    ("VER-056", "HLR-REG-004", "Legibilidad por terceros", "Integración", "D", "Herramienta externa",
     "El registro se abre y se interpreta correctamente en una herramienta de análisis de terceros."),
    ("VER-057", "HLR-REG-005", "Preservación ante cierre inesperado", "Sistema", "T", "Escritorio",
     "Tras una terminación abrupta el registro conserva todo salvo el último intervalo de volcado."),
    ("VER-058", "HLR-CFG-001", "Lectura y escritura de parámetros", "Sistema", "T", "HIL PX4",
     "Cada escritura se confirma por relectura y los valores fuera de rango se rechazan."),
    ("VER-059", "HLR-CFG-002", "Respaldo y restauración", "Sistema", "D", "HIL PX4",
     "El conjunto restaurado coincide con el respaldado."),
    ("VER-060", "HLR-CFG-003", "Asistentes de calibración", "Sistema", "D", "HIL PX4",
     "El resultado presentado corresponde al comunicado por la aeronave."),
    ("VER-061", "HLR-CFG-004", "Persistencia de la configuración", "Integración", "I", "Escritorio",
     "La configuración se conserva entre sesiones y las versiones incompatibles se descartan."),
    ("VER-062", "HLR-CFG-005", "Identificación de versiones", "Sistema", "I", "Escritorio",
     "Las versiones de la aplicación y del programa de la aeronave son visibles y correctas."),
    ("VER-063", "HLR-PLT-001", "Paridad entre plataformas", "Sistema", "T", "Windows 11 y Android",
     "Ambas plataformas superan el conjunto de pruebas operacionales acordado."),
    ("VER-064", "HLR-PLT-002", "Tiempo de puesta en servicio", "Sistema", "T", "Equipo de referencia",
     "El estado operativo se alcanza antes de 30 s en diez arranques consecutivos."),
    ("VER-065", "HLR-PLT-003", "Firma del paquete", "Proceso", "I", "Cadena de publicación",
     "El artefacto publicado presenta una firma válida y verificable."),
    ("VER-066", "HLR-PLT-004", "Operación sin Internet", "Sistema", "T", "Equipo aislado",
     "El mando y la telemetría son plenamente operativos sin red."),
    ("VER-067", "HLR-PLT-005", "Degradación controlada", "Sistema", "T", "Entorno con recursos suprimidos",
     "La ausencia de cada recurso opcional degrada solo su función y no interrumpe el mando."),
    ("VER-068", "HLR-SEC-001", "Firma de mensajes MAVLink", "Sistema", "T", "Banco con firma activa",
     "Los mensajes con firma inválida se descartan y quedan registrados."),
    ("VER-069", "HLR-SEC-002", "Protección de credenciales", "Integración", "I", "Revisión de código",
     "Ninguna credencial aparece en claro en la configuración almacenada."),
    ("VER-070", "HLR-SEC-003", "Validación de certificados", "Integración", "T", "Servidor con certificado inválido",
     "La conexión se rechaza y el motivo queda registrado."),
    ("VER-071", "HLR-SEC-004", "Integridad de componentes cargados", "Proceso", "A", "Análisis de despliegue",
     "El análisis identifica y cubre todos los componentes cargados dinámicamente."),
    ("VER-072", "HLR-SEC-005", "Registro de eventos de seguridad", "Integración", "I", "Escritorio",
     "Los fallos de conexión y autenticación quedan registrados con motivo."),
    ("VER-073", "HLR-PER-001", "Frecuencia de refresco", "Sistema", "T", "Equipo de referencia",
     "El refresco no baja de 30 imágenes por segundo en el escenario nominal."),
    ("VER-074", "HLR-PER-002", "Capacidad de proceso de mensajes", "Sistema", "T", "Generador de carga",
     "Con 500 mensajes por segundo no se descarta ningún mensaje por saturación."),
    ("VER-075", "HLR-PER-003", "Consumo de memoria", "Sistema", "T", "Equipo de referencia",
     "La memoria residente permanece por debajo de 1,5 GB en el escenario nominal."),
    ("VER-076", "HLR-PER-004", "Prueba de resistencia", "Sistema", "T", "Equipo de referencia",
     "Tras 4 horas no se observa crecimiento sostenido de memoria ni degradación de respuesta."),
]

# Trazabilidad normativa -> requisitos de alto nivel.
NORMATIVA_HLR = [
    ("NOM-107-SCT3-2019, num. 5.2 y 5.3", "Identificación del RPAS y del operador",
     "HLR-RID-001, HLR-RID-002, HLR-CFG-005"),
    ("NOM-107-SCT3-2019, num. 6.1", "Condiciones generales de operación",
     "HLR-COM-001, HLR-SIT-002, HLR-PLT-004"),
    ("NOM-107-SCT3-2019, num. 6.2", "Planificación de la operación",
     "HLR-MIS-001, HLR-MIS-002, HLR-MIS-005, HLR-MIS-007"),
    ("NOM-107-SCT3-2019, num. 6.3", "Información disponible para el piloto",
     "HLR-TEL-001, HLR-TEL-006, HLR-SIT-001, HLR-SIT-005, HLR-HMI-004"),
    ("NOM-107-SCT3-2019, num. 6.4", "Conservación de registros de la operación",
     "HLR-REG-001, HLR-REG-003, HLR-REG-004, HLR-VID-003"),
    ("NOM-107-SCT3-2019, num. 7.1 y 7.2", "Límites de altura y volumen de operación",
     "HLR-MIS-004, HLR-SAF-001, HLR-SIT-003"),
    ("NOM-107-SCT3-2019, num. 7.3", "Verificaciones previas al vuelo",
     "HLR-SAF-005, HLR-CFG-003"),
    ("NOM-107-SCT3-2019, num. 7.4", "Procedimientos de contingencia",
     "HLR-COM-003, HLR-SAF-002, HLR-SAF-004, HLR-SAF-007, HLR-TEL-004"),
    ("OACI Anexo 13", "Investigación de accidentes e incidentes",
     "HLR-REG-004, HLR-REG-005"),
    ("OACI Doc 10019, cap. 6", "Estación de pilotaje a distancia",
     "HLR-COM-001, HLR-COM-004, HLR-TEL-001, HLR-SAF-008"),
    ("OACI Doc 9859", "Gestión de la seguridad operacional",
     "HLR-TEL-003, HLR-HMI-002, HLR-REG-001"),
    ("JARUS SORA, OSO#05", "Diseño considerando la seguridad del sistema",
     "HLR-PER-004, HLR-PLT-005"),
    ("JARUS SORA, OSO#06", "Desempeño del enlace C3",
     "HLR-COM-001, HLR-COM-002, HLR-COM-003, HLR-SAF-006, HLR-TEL-005"),
    ("JARUS SORA, OSO#08 y OSO#16", "Procedimientos operacionales y configuración",
     "HLR-MIS-003, HLR-CFG-001, HLR-CFG-002, HLR-CFG-003"),
    ("JARUS SORA, OSO#10 y M2", "Contención del volumen de operación",
     "HLR-SAF-001, HLR-SAF-002, HLR-SAF-007, HLR-SAF-008, HLR-MIS-004"),
    ("JARUS SORA, OSO#13", "Sistemas externos que soportan la operación",
     "HLR-RID-004, HLR-SEC-001"),
    ("JARUS SORA, OSO#19 y OSO#20", "Errores humanos y factores humanos",
     "HLR-SAF-003, HLR-SAF-005, HLR-HMI-005, HLR-VID-004, HLR-SIT-004"),
    ("ASTM F3411-22a", "Identificación remota de aeronaves no tripuladas",
     "HLR-RID-001, HLR-RID-002, HLR-RID-003, HLR-RID-004, HLR-SIT-005"),
    ("ASTM F3548-21", "Interoperabilidad con proveedores de servicios UTM",
     "HLR-UTM-001, HLR-UTM-002, HLR-UTM-003"),
    ("RTCA DO-278A / ED-109A", "Aseguramiento de software de sistemas CNS/ATM",
     "Todos los HLR; en particular HLR-COM-006, HLR-PER-002, HLR-CFG-005"),
    ("RTCA DO-326A / ED-202A", "Proceso de seguridad de la información",
     "HLR-SEC-001 a HLR-SEC-005, HLR-PLT-003"),
    ("SAE ARP4102/4 y /7", "Presentación de alertas e instrumentación",
     "HLR-TEL-002, HLR-TEL-003, HLR-HMI-001, HLR-HMI-002, HLR-HMI-005"),
]

# Requisitos derivados del análisis de seguridad del capítulo 4.
DERIVADOS = [
    ("DS-01", "La pérdida de enlace no debe permitir que la estación presente información de estado "
              "obsoleta como si fuera vigente.", "HLR-SAF-006, HLR-COM-003"),
    ("DS-02", "La incorporación de una fuente de video no debe reducir la información de seguridad "
              "disponible para el piloto.", "HLR-VID-004, HLR-HMI-005"),
    ("DS-03", "La evidencia de la operación debe sobrevivir a un fallo del equipo anfitrión.",
     "HLR-REG-005"),
    ("DS-04", "El análisis posterior al vuelo no debe poder generar mandos hacia una aeronave real.",
     "HLR-COM-007"),
    ("DS-05", "La indisponibilidad de una función accesoria no debe interrumpir el mando de la aeronave.",
     "HLR-PLT-005"),
]

# Condiciones de fallo consideradas en el análisis funcional de peligros.
FHA = [
    ("FC-01", "Pérdida total de la capacidad de mando desde la estación", "Mayor",
     "La aeronave ejecuta su procedimiento autónomo ante pérdida de enlace (retorno o aterrizaje). "
     "El piloto conserva la observación directa en operaciones VLOS.",
     "HLR-COM-002, HLR-COM-003, HLR-SAF-004, HLR-SAF-007"),
    ("FC-02", "Presentación de telemetría errónea sin indicación de invalidez", "Mayor",
     "Cotejo cruzado entre magnitudes independientes y marcado explícito de los datos caducados. "
     "Procedimiento operativo de contraste con la observación directa.",
     "HLR-TEL-001, HLR-TEL-004, HLR-COM-006"),
    ("FC-03", "Emisión de un mando no solicitado por el piloto", "Mayor",
     "Confirmación explícita obligatoria para todo mando que altere el estado de vuelo.",
     "HLR-SAF-003, HLR-SAF-008"),
    ("FC-04", "Carga de un plan de vuelo que vulnera el volumen autorizado", "Mayor",
     "Validación previa contra altura máxima y geocerca, y contención independiente a bordo.",
     "HLR-MIS-004, HLR-SAF-001"),
    ("FC-05", "Alerta crítica no presentada o cubierta por otro elemento", "Mayor",
     "Las alertas ocupan la capa superior del apilamiento y no son suprimibles por configuración.",
     "HLR-HMI-005, HLR-SAF-005, HLR-VID-004"),
    ("FC-06", "Pérdida de la evidencia registrada de la operación", "Menor",
     "Volcado periódico a disco y formato de registro documentado e independiente.",
     "HLR-REG-001, HLR-REG-005"),
    ("FC-07", "Identificación remota ausente o incorrecta", "Mayor",
     "Verificación del estado del subsistema antes del despegue como precondición operativa.",
     "HLR-RID-001, HLR-RID-004"),
    ("FC-08", "Degradación progresiva del desempeño durante una operación prolongada", "Mayor",
     "Prueba de resistencia con criterio de aceptación sobre memoria y tiempo de respuesta.",
     "HLR-PER-004, HLR-PER-001"),
]
