"""Cálculo de posiciones y zonas seleccionables de los elementos del cubo. Aquí se determina dónde se dibuja cada control y qué elemento corresponde a cada clic."""

from __future__ import annotations

from . import constants
from .cube_math import point_in_convex


class Layout:
    """Contenedor sencillo que guarda las posiciones, dimensiones y zonas de interacción calculadas para el cubo, las flechas y la barra de herramientas."""


def build(right, top, ui_scale, size, show_navbar=True,
          buttons=constants.BUTTONS):
    """Calcula la distribución completa del cubo de navegación dentro de la región. Tiene en cuenta el espacio disponible, la escala de interfaz, el tamaño configurado y si la barra de herramientas está visible."""
    sc = ui_scale
    S = size * sc                       # tamaño nominal del widget del cubo
    H = S * 0.56                        # mitad del área que ocupa el cubo
    cx = right - 10 * sc - H
    cy = top - 10 * sc - H
    d = 34 * sc                         # una celda de la barra de herramientas, casi cuadrada

    L = Layout()
    L.sc, L.S, L.H = sc, S, H
    L.cx, L.cy = cx, cy
    L.s = S * 0.25                      # unidades del cubo -> píxeles
    L.arrow_size = 0.06 * S
    L.arrow_hit = 0.09 * S
    L.arrows = {
        "UP": (cx, cy + 0.5 * S), "DOWN": (cx, cy - 0.5 * S),
        "LEFT": (cx - 0.5 * S, cy), "RIGHT": (cx + 0.5 * S, cy),
        "ROLL_L": (cx - 0.46 * S, cy + 0.46 * S),
        "ROLL_R": (cx + 0.46 * S, cy + 0.46 * S),
    }

    # Barra de herramientas: un único panel redondeado con N celdas iguales apiladas debajo del cubo.
    # El área de interacción de cada celda coincide exactamente con su área dibujada.
    L.show_navbar = bool(show_navbar)
    L.btn_d = d
    L.btn_hw = d * 0.61                 # mitad del ancho de una celda
    L.btn_hh = d * 0.5                  # mitad de la altura de una celda
    y0 = cy - H - 8 * sc - d / 2        # centro de la primera celda
    L.buttons = [(name, (cx, y0 - k * d)) for k, name in enumerate(buttons)]
    n = len(buttons)
    pad = 5 * sc
    L.panel = (cx, y0 - (n - 1) * d / 2.0,      # centro X, centro Y
               L.btn_hw * 2, n * d + 2 * pad)   # ancho, alto
    L.icon_k = d * 0.30                 # mitad del tamaño del icono en píxeles
    return L


def button_at(L, x, y):
    """Comprueba qué botón de la barra de herramientas ocupa la coordenada indicada. Devuelve su nombre si el punto cae dentro de una celda o None si no coincide con ninguna."""
    if not L.show_navbar:
        return None
    for name, (bx, by) in L.buttons:
        if abs(x - bx) <= L.btn_hw and abs(y - by) <= L.btn_hh:
            return name
    return None


def arrow_at(L, x, y):
    """Comprueba si la coordenada indicada está dentro de alguna zona de las flechas de giro y devuelve la dirección correspondiente cuando encuentra una."""
    for name, (ax, ay) in L.arrows.items():
        if (x - ax) ** 2 + (y - ay) ** 2 < L.arrow_hit ** 2:
            return name
    return None


def hit_test(L, x, y, cells):
    """Realiza la comprobación completa de selección: primero identifica botones o flechas y después las zonas del cubo. Devuelve el tipo y nombre del elemento que está debajo del cursor."""
    name = button_at(L, x, y)
    if name:
        return ("BUTTON", name)
    name = arrow_at(L, x, y)
    if name:
        return ("ARROW", name)
    for cell, poly, _facing in cells:
        if point_in_convex((x, y), poly):
            return ("CELL", cell["dir"])
    return None
