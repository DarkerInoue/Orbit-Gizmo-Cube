"""Construcción de la geometría de los iconos de la barra de herramientas mediante puntos, líneas y triángulos."""

from __future__ import annotations

import math


def stroke(points, w, closed=False):
    """Convierte una línea formada por varios puntos en una lista de triángulos con el grosor indicado. Puede cerrar el recorrido para formar un contorno completo."""
    tris = []
    n = len(points)
    for i in range(n if closed else n - 1):
        a, b = points[i], points[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        if length < 1e-9:
            continue
        ux, uy = dx / length, dy / length
        nx, ny = -uy * w / 2, ux * w / 2        
        ex, ey = ux * w / 2, uy * w / 2         
        p0 = (a[0] - ex + nx, a[1] - ey + ny)
        p1 = (b[0] + ex + nx, b[1] + ey + ny)
        p2 = (b[0] + ex - nx, b[1] + ey - ny)
        p3 = (a[0] - ex - nx, a[1] - ey - ny)
        tris += [p0, p1, p2, p0, p2, p3]
    return tris


def fill(points):
    """Triangula un polígono convexo usando su primer punto como vértice común. Devuelve los vértices preparados para dibujar el relleno del icono."""
    out = []
    for i in range(1, len(points) - 1):
        out += [points[0], points[i], points[i + 1]]
    return out


def circle(cx, cy, r, n=22):
    """Genera los puntos que aproximan una circunferencia. La cantidad de segmentos controla la suavidad del círculo que se utilizará en el icono."""
    return [(cx + r * math.cos(2 * math.pi * i / n),
             cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def arrowhead(tip, direction, size):
    """Calcula los triángulos que forman la punta de una flecha según su posición, dirección y tamaño."""
    dx, dy = direction
    px, py = -dy, dx
    bx, by = tip[0] - dx * size, tip[1] - dy * size
    return [tip, (bx + px * size * 0.7, by + py * size * 0.7),
            (bx - px * size * 0.7, by - py * size * 0.7)]


def _home(w, _state):
    """Construye la geometría del icono de inicio, que representa la acción para volver a una vista de referencia."""
    return (stroke([(-0.92, 0.05), (0.0, 0.92), (0.92, 0.05)], w)
            + stroke([(-0.62, 0.18), (-0.62, -0.82), (0.62, -0.82),
                      (0.62, 0.18)], w)
            + stroke([(-0.2, -0.82), (-0.2, -0.28), (0.2, -0.28),
                      (0.2, -0.82)], w))


def _zoom(w, _state):
    """Construye la geometría del icono de acercamiento y alejamiento, representado mediante una lupa."""
    return (stroke(circle(-0.15, 0.15, 0.62), w, closed=True)
            + stroke([(0.3, -0.3), (0.92, -0.92)], w * 1.6))


def _pan(w, _state):
    """Construye la geometría del icono de desplazamiento de vista, que indica que se puede mover el encuadre."""
    out = stroke([(-0.7, 0.0), (0.7, 0.0)], w) + stroke([(0.0, -0.7), (0.0, 0.7)], w)
    for tip, d in (((0.98, 0.0), (1, 0)), ((-0.98, 0.0), (-1, 0)),
                   ((0.0, 0.98), (0, 1)), ((0.0, -0.98), (0, -1))):
        out += arrowhead(tip, d, 0.34)
    return out


def _camera(w, _state):
    """Construye la geometría del icono de cámara para identificar el control que alterna la vista de cámara."""
    body = stroke([(-0.92, -0.5), (0.3, -0.5), (0.3, 0.5), (-0.92, 0.5)], w,
                  closed=True)
    lens = fill([(0.3, 0.16), (0.96, 0.58), (0.96, -0.58), (0.3, -0.16)])
    return body + lens


def _projection(w, perspective):
    """Construye el icono que representa el cambio entre perspectiva y proyección ortográfica. Su aspecto depende del modo activo."""
    if perspective:     
        return (stroke([(-0.95, -0.72), (0.95, -0.72), (0.45, 0.72),
                        (-0.45, 0.72)], w, closed=True)
                + stroke([(-0.32, -0.72), (-0.15, 0.72)], w * 0.8)
                + stroke([(0.32, -0.72), (0.15, 0.72)], w * 0.8)
                + stroke([(-0.7, 0.0), (0.7, 0.0)], w * 0.8))
    return (stroke([(-0.76, -0.76), (0.76, -0.76), (0.76, 0.76),
                    (-0.76, 0.76)], w, closed=True)
            + stroke([(-0.25, -0.76), (-0.25, 0.76)], w * 0.8)
            + stroke([(0.25, -0.76), (0.25, 0.76)], w * 0.8)
            + stroke([(-0.76, -0.25), (0.76, -0.25)], w * 0.8)
            + stroke([(-0.76, 0.25), (0.76, 0.25)], w * 0.8))


_BUILDERS = {"HOME": _home, "ZOOM": _zoom, "PAN": _pan,
             "CAMERA": _camera, "PROJECTION": _projection}


def build_icon(name, cx, cy, k, state=False, line=0.2):
    """Genera los vértices del icono solicitado y los coloca en el centro indicado. Ajusta su escala, grosor y estado visual antes de devolver la geometría lista para dibujar."""
    tris = _BUILDERS[name](line, state)
    return [(cx + x * k, cy + y * k) for x, y in tris]
