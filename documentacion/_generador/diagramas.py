# -*- coding: utf-8 -*-
"""Figuras del documento de certificación OTECH-GroundStation.

Se generan por código, no a mano, para que vuelvan a salir idénticas cuando el
documento se revise. Salida en docs/figuras/ a 200 dpi (suficiente para impresión
a tamaño carta sin pixelado).

Todo texto dentro de una caja pasa por ajustar(), que primero intenta repartirlo
en varias líneas y después reduce el cuerpo hasta que cabe de verdad. Se mide
contra el renderer en lugar de estimar anchos: los nombres de clase tipo
MultiVehicleManager desbordan la caja con cualquier heurística de conteo.
"""

import os
import re
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figuras")
os.makedirs(OUT, exist_ok=True)

# Paleta institucional OTECH.
NAVY = "#0F1B3D"
NAVY_L = "#1B2A5C"
NAVY_M = "#33436F"
CYAN = "#1E98C1"
CYAN_L = "#E3F1F7"
GREY = "#5A6472"
GREY_M = "#7A8798"
GREY_L = "#F0F2F5"
WHITE = "#FFFFFF"
AMBER = "#B8860B"

plt.rcParams["font.family"] = "DejaVu Sans"


def _partir_camel(token):
    """MultiVehicleManager -> ['Multi', 'Vehicle', 'Manager'] para poder cortarlo."""
    piezas = re.split(r"(?<=[a-z0-9])(?=[A-Z])", token)
    return piezas if len(piezas) > 1 else [token]


def _candidatos(texto, max_lineas):
    """Reparticiones posibles del texto, de menos a más líneas."""
    yield texto
    for n in range(2, max_lineas + 1):
        ancho = max(4, int(len(texto) / n) + 3)
        # Nunca partir dentro de una palabra: "MAVLinkProtoc / ol v2.0" es peor que
        # una línea larga. Los identificadores CamelCase se resuelven más abajo.
        env = textwrap.fill(texto, ancho, break_long_words=False, break_on_hyphens=False)
        if env.count("\n") + 1 <= max_lineas:
            yield env
    # Último recurso: cortar también dentro de los nombres CamelCase.
    piezas = []
    for tok in texto.split():
        piezas.extend(_partir_camel(tok))
    if len(piezas) > len(texto.split()):
        for n in range(2, max_lineas + 1):
            corte = max(1, -(-len(piezas) // n))
            yield "\n".join("".join(piezas[i:i + corte]) for i in range(0, len(piezas), corte))


def ajustar(ax, x, y, texto, ancho_caja, alto_caja, fs, color, weight="normal",
            max_lineas=3, fs_min=4.6, ha="center", va="center"):
    """Coloca texto garantizando que cabe dentro de ancho_caja x alto_caja (datos)."""
    fig = ax.figure
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()

    limite_w = ancho_caja * 0.90
    limite_h = alto_caja * 0.86

    # El cuerpo manda sobre el reparto: se prueban todas las formas de partir el
    # texto a tamaño completo antes de bajar un punto. Al reves, un título largo se
    # queda en una sola línea diminuta mientras el de al lado conserva el tamaño
    # nominal, y las figuras salen con tipografías desparejas.
    variantes = list(_candidatos(texto, max_lineas))
    respaldo = None
    cuerpo = fs
    while cuerpo >= fs_min:
        for variante in variantes:
            t = ax.text(x, y, variante, ha=ha, va=va, fontsize=cuerpo, color=color,
                        weight=weight, zorder=6, linespacing=1.28)
            bb = t.get_window_extent(renderer=renderer).transformed(ax.transData.inverted())
            if bb.width <= limite_w and bb.height <= limite_h:
                if respaldo is not None:
                    respaldo.remove()
                return t
            if respaldo is not None:
                respaldo.remove()
            respaldo = t
        cuerpo -= 0.4
    return respaldo


def caja(ax, x, y, w, h, fc, ec=None, lw=1.1, radius=0.10, ls="solid"):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                boxstyle=f"round,pad=0,rounding_size={radius}",
                                fc=fc, ec=ec or fc, lw=lw, zorder=3, linestyle=ls))


def save(fig, name):
    path = os.path.join(OUT, name)
    fig.savefig(path, dpi=200, bbox_inches="tight", facecolor="white", pad_inches=0.18)
    plt.close(fig)
    print("->", path)


# ---------------------------------------------------------------------------
# Figura 1 - Modelo en V
# ---------------------------------------------------------------------------
def fig_modelo_v():
    fig, ax = plt.subplots(figsize=(15.0, 9.4))
    ax.set_xlim(-1.0, 20.0)
    ax.set_ylim(0.5, 11.0)
    ax.axis("off")

    BW, BH = 3.90, 1.30

    izq = [
        (2.60, 8.70, "Requisitos del sistema y ConOps",
         "Necesidad operacional, marco normativo\ny entorno de operación"),
        (3.90, 7.15, "Requisitos de alto nivel (HLR)",
         "Qué debe hacer el software\nOTECH-HLR-xxx-nnn"),
        (5.20, 5.60, "Diseño arquitectónico",
         "Descomposición en componentes\ne interfaces internas"),
        (6.50, 4.05, "Requisitos de bajo nivel (LLR)",
         "Diseño detallado por componente\nOTECH-LLR-xxx-nnn"),
    ]
    der = [
        (16.40, 8.70, "Validación operacional",
         "Aceptación en operación real con\nel explotador y la autoridad"),
        (15.10, 7.15, "Pruebas de sistema (SIL / HIL)",
         "Verificación de cada HLR sobre\nel software integrado"),
        (13.80, 5.60, "Pruebas de integración",
         "Interfaces entre componentes\ny con sistemas externos"),
        (12.50, 4.05, "Pruebas unitarias",
         "Verificación de cada LLR\ny cobertura estructural"),
    ]
    base_x, base_y = 9.50, 1.95
    base_w = 6.6

    enlaces = {
        8.70: "Validación: el sistema resuelve la necesidad operacional",
        7.15: "Verificación de los requisitos de alto nivel",
        5.60: "Verificación de la arquitectura y las interfaces",
        4.05: "Verificación de los requisitos de bajo nivel y del código",
    }

    # Trazos de la V, por detrás de las cajas.
    pl = [(x, y) for x, y, _, _ in izq] + [(base_x, base_y)]
    pr = [(base_x, base_y)] + [(x, y) for x, y, _, _ in der][::-1]
    ax.plot([p[0] for p in pl], [p[1] for p in pl], color=NAVY, lw=2.6, zorder=1, solid_capstyle="round")
    ax.plot([p[0] for p in pr], [p[1] for p in pr], color=CYAN, lw=2.6, zorder=1, solid_capstyle="round")

    for y, etiqueta in enlaces.items():
        xa = next(x for x, yy, _, _ in izq if yy == y) + BW / 2
        xb = next(x for x, yy, _, _ in der if yy == y) - BW / 2
        ax.annotate("", xy=(xb, y), xytext=(xa, y),
                    arrowprops=dict(arrowstyle="<->", color=GREY, lw=1.0,
                                    linestyle=(0, (5, 4)), shrinkA=5, shrinkB=5), zorder=2)
        # Fondo blanco: la etiqueta cruza los trazos de la V. En el nivel más bajo va
        # debajo de la flecha, porque arriba solo queda el hueco entre las dos cajas
        # del nivel anterior y el recuadro blanco las mordia.
        abajo = y == min(enlaces)
        ax.text((xa + xb) / 2, y - BH / 2 - 0.20 if abajo else y + BH / 2 + 0.20, etiqueta,
                ha="center", va="top" if abajo else "bottom",
                fontsize=8.2, color=GREY, style="italic", zorder=5,
                bbox=dict(fc="white", ec="none", pad=2.5))

    for x, y, titulo, sub in izq:
        caja(ax, x, y, BW, BH, NAVY, NAVY)
        ajustar(ax, x, y + 0.28, titulo, BW, 0.50, 10.0, WHITE, "bold", max_lineas=2)
        ajustar(ax, x, y - 0.30, sub, BW, 0.62, 7.8, "#C4D0E6", max_lineas=3)

    for x, y, titulo, sub in der:
        caja(ax, x, y, BW, BH, CYAN_L, CYAN, lw=1.5)
        ajustar(ax, x, y + 0.28, titulo, BW, 0.50, 10.0, NAVY, "bold", max_lineas=2)
        ajustar(ax, x, y - 0.30, sub, BW, 0.62, 7.8, GREY, max_lineas=3)

    caja(ax, base_x, base_y, base_w, BH, AMBER, "#8A6608", lw=1.3)
    ajustar(ax, base_x, base_y + 0.28, "Implementación y codificación", base_w, 0.50, 10.0, WHITE, "bold", max_lineas=2)
    ajustar(ax, base_x, base_y - 0.30,
            "C++17 / QML  ·  normas de codificación  ·  revisión por pares",
            base_w, 0.62, 7.8, "#FBF1D5", max_lineas=3)

    # Sentido de recorrido de cada rama.
    ax.annotate("", xy=(-0.55, 2.6), xytext=(-0.55, 9.5),
                arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=2.0))
    ax.text(-0.90, 6.05, "D E S C O M P O S I C I O N", rotation=90, ha="center", va="center",
            fontsize=8.6, color=NAVY, weight="bold")
    ax.annotate("", xy=(19.55, 9.5), xytext=(19.55, 2.6),
                arrowprops=dict(arrowstyle="-|>", color=CYAN, lw=2.0))
    ax.text(19.90, 6.05, "I N T E G R A C I O N   Y   V E R I F I C A C I O N", rotation=270,
            ha="center", va="center", fontsize=8.6, color=CYAN, weight="bold")

    ax.text(9.5, 10.70, "Ciclo de vida de desarrollo en modelo en V — OTECH-GroundStation",
            ha="center", va="center", fontsize=13.0, color=NAVY, weight="bold")
    ax.text(9.5, 10.25, "Cada actividad de definición (rama izquierda) tiene asociada una actividad de verificación (rama derecha).",
            ha="center", va="center", fontsize=9.0, color=GREY, style="italic")

    save(fig, "fig01_modelo_v.png")


# ---------------------------------------------------------------------------
# Figura 2 - Arquitectura de software
# ---------------------------------------------------------------------------
def fig_arquitectura():
    fig, ax = plt.subplots(figsize=(15.0, 9.8))
    ax.set_xlim(0, 17.4)
    ax.set_ylim(0.4, 11.3)
    ax.axis("off")

    capas = [
        (9.60, "Capa de presentación (HMI)", "QML / Qt Quick",
         ["Fly View", "Plan View", "Analyze View", "Vehicle Setup", "Consola MAVLink", "Viewer 3D", "Ajustes"],
         NAVY, WHITE),
        (8.00, "Capa de aplicación", "Lógica de misión y de vehículo",
         ["MultiVehicleManager", "MissionManager", "GeoFence / Rally", "VideoManager", "GimbalController",
          "RemoteIDManager", "UTMSP Adapter", "ADSBVehicleManager", "FollowMe"],
         NAVY_L, WHITE),
        (6.40, "Servicios comunes", "Transversales a la aplicación",
         ["FactSystem (parámetros)", "SettingsManager", "PositionManager", "TerrainQuery",
          "MAVLinkLogManager", "Joystick", "FirmwarePlugin"],
         NAVY_M, WHITE),
        (4.80, "Capa de comunicaciones", "Enlace C2 y protocolo",
         ["LinkManager", "MAVLinkProtocol v2.0", "SerialLink", "UDPLink", "TCPLink",
          "BluetoothLink", "LogReplayLink", "MockLink"],
         CYAN, WHITE),
        (3.20, "Plataforma y bibliotecas", "Base de ejecución",
         ["Qt 6.8.3", "GStreamer 1.0", "MAVLink c_library_v2", "Windows 11 x64", "Android 13 arm64-v8a"],
         GREY_M, WHITE),
    ]

    X0, XF = 4.55, 17.05
    HUECO = 0.18

    for y, titulo, sub, items, fc, tc in capas:
        ax.add_patch(FancyBboxPatch((0.35, y - 0.70), 16.75, 1.40,
                                    boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=GREY_L, ec="#D3D8E0", lw=1.0, zorder=1))
        ax.text(0.78, y + 0.30, titulo, ha="left", va="center", fontsize=10.0,
                color=NAVY, weight="bold", zorder=4)
        ax.text(0.78, y - 0.12, sub, ha="left", va="center", fontsize=7.8,
                color=GREY, style="italic", zorder=4)

        n = len(items)
        ancho = (XF - X0 - (n - 1) * HUECO) / n
        for i, it in enumerate(items):
            cx = X0 + ancho / 2 + i * (ancho + HUECO)
            caja(ax, cx, y, ancho, 0.96, fc, fc, radius=0.08)
            ajustar(ax, cx, y, it, ancho, 0.96, 7.4, tc, "bold", max_lineas=3)

    # Frontera del sistema.
    ax.add_patch(FancyBboxPatch((0.35, 0.80), 16.75, 1.40,
                                boxstyle="round,pad=0,rounding_size=0.12",
                                fc=WHITE, ec=CYAN, lw=1.5, zorder=1, linestyle=(0, (6, 3))))
    ax.text(0.78, 1.80, "Interfaces externas", ha="left", va="center", fontsize=10.0,
            color=CYAN, weight="bold", zorder=4)
    ax.text(0.78, 1.38, "Frontera del sistema", ha="left", va="center", fontsize=7.8,
            color=GREY, style="italic", zorder=4)

    ext = ["IF-01  RPA / enlace C2 (MAVLink 2.0)", "IF-02  GNSS y RTK", "IF-03  Servidor cartográfico",
           "IF-04  Video FPV (RTSP / UDP / UVC)", "IF-05  Proveedor USS / UTM",
           "IF-06  Receptor ADS-B", "IF-07  Mando (joystick / HID)"]
    n = len(ext)
    ancho = (XF - X0 - (n - 1) * HUECO) / n
    for i, it in enumerate(ext):
        cx = X0 + ancho / 2 + i * (ancho + HUECO)
        caja(ax, cx, 1.50, ancho, 1.00, CYAN_L, CYAN, radius=0.08)
        ajustar(ax, cx, 1.50, it, ancho, 1.00, 7.0, NAVY, max_lineas=4)

    for y in [8.80, 7.20, 5.60, 4.00, 2.40]:
        ax.annotate("", xy=(8.7, y - 0.28), xytext=(8.7, y + 0.28),
                    arrowprops=dict(arrowstyle="<->", color="#9AA4B2", lw=1.3), zorder=2)

    ax.text(8.7, 11.00, "Arquitectura lógica del software OTECH-GroundStation",
            ha="center", va="center", fontsize=13.0, color=NAVY, weight="bold")
    ax.text(8.7, 10.58, "Descomposición en capas empleada como base para la asignación de los requisitos de bajo nivel.",
            ha="center", va="center", fontsize=9.0, color=GREY, style="italic")

    save(fig, "fig02_arquitectura.png")


# ---------------------------------------------------------------------------
# Figura 3 - Cadena de trazabilidad
# ---------------------------------------------------------------------------
def fig_trazabilidad():
    fig, ax = plt.subplots(figsize=(15.0, 4.3))
    ax.set_xlim(0, 17.4)
    ax.set_ylim(0.5, 5.3)
    ax.axis("off")

    nodos = [
        ("Normativa y necesidad operacional", "NOM-107-SCT3-2019\nSORA / OSO\nDO-278A", NAVY),
        ("Requisitos de alto nivel (HLR)", "OTECH-HLR-xxx-nnn\n76 requisitos", NAVY_L),
        ("Requisitos de bajo nivel (LLR)", "OTECH-LLR-xxx-nnn\n124 requisitos", NAVY_M),
        ("Código fuente y componente", "src/<módulo>\n328 .cc · 384 .h · 422 .qml", CYAN),
        ("Casos de verificación", "OTECH-VER-nnn\nmétodo I / A / D / T", GREY_M),
        ("Evidencia objetiva", "Registros, .tlog\ne informes de prueba", AMBER),
    ]

    n = len(nodos)
    hueco = 0.62
    x0, xf = 0.35, 17.05
    w = (xf - x0 - (n - 1) * hueco) / n
    h = 1.72
    cy = 3.05

    for i, (titulo, sub, color) in enumerate(nodos):
        cx = x0 + w / 2 + i * (w + hueco)
        caja(ax, cx, cy, w, h, color, color, radius=0.12)
        ajustar(ax, cx, cy + 0.40, titulo, w, 0.72, 9.4, WHITE, "bold", max_lineas=3)
        ajustar(ax, cx, cy - 0.44, sub, w, 0.66, 7.2, "#DCE4F2", max_lineas=3)
        if i < n - 1:
            xa, xb = cx + w / 2, cx + w / 2 + hueco
            ax.annotate("", xy=(xb, cy + 0.42), xytext=(xa, cy + 0.42),
                        arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.8))
            ax.annotate("", xy=(xa, cy - 0.42), xytext=(xb, cy - 0.42),
                        arrowprops=dict(arrowstyle="-|>", color="#9AA4B2", lw=1.3,
                                        linestyle=(0, (4, 3))))

    ax.text(8.7, 5.05, "Cadena de trazabilidad bidireccional",
            ha="center", va="center", fontsize=13.0, color=NAVY, weight="bold")
    ax.text(8.7, 1.60, "Trazabilidad directa (flechas superiores): todo requisito se implementa y se verifica.",
            ha="center", va="center", fontsize=8.8, color=NAVY)
    ax.text(8.7, 1.16, "Trazabilidad inversa (flechas inferiores, discontinuas): no existe código ni función sin un requisito que lo justifique.",
            ha="center", va="center", fontsize=8.8, color=GREY, style="italic")

    save(fig, "fig03_trazabilidad.png")


if __name__ == "__main__":
    fig_modelo_v()
    fig_arquitectura()
    fig_trazabilidad()
