"""Cálculos matemáticos del cubo de navegación. Este archivo genera sus zonas seleccionables y realiza las operaciones de vectores, matrices, cuaterniones y proyección en pantalla."""

from __future__ import annotations

import math

# Cada cara se divide en una cuadrícula de 3 × 3: el centro representa la cara,
# los lados representan las aristas y las esquinas representan los vértices. En total hay 26 direcciones.
_E = 0.72
_RANGES = {-1: (-1.0, -_E), 0: (-_E, _E), 1: (_E, 1.0)}
_FACES = (
    # nombre, normal de la zona, eje local horizontal (texto hacia la derecha) y eje local vertical (texto hacia arriba)
    ("FRONT",  (0, -1, 0), (1, 0, 0),   (0, 0, 1)),
    ("BACK",   (0, 1, 0),  (-1, 0, 0),  (0, 0, 1)),
    ("RIGHT",  (1, 0, 0),  (0, 1, 0),   (0, 0, 1)),
    ("LEFT",   (-1, 0, 0), (0, -1, 0),  (0, 0, 1)),
    ("TOP",    (0, 0, 1),  (1, 0, 0),   (0, 1, 0)),
    ("BOTTOM", (0, 0, -1), (1, 0, 0),   (0, -1, 0)),
)


def _comb(n, a, u, b, v):
    """Construye una dirección combinando dos ejes de una cara del cubo. Se usa para obtener las normales de las caras, aristas y esquinas a partir de sus componentes."""
    return tuple(n[k] + a * u[k] + b * v[k] for k in range(3))


def _build_cells():
    """Genera las 26 zonas seleccionables del cubo: seis caras, doce aristas y ocho esquinas. Para cada zona calcula su dirección y los ejes locales que permiten dibujarla correctamente."""
    cells = []
    for name, n, u, v in _FACES:
        for i in (-1, 0, 1):
            for j in (-1, 0, 1):
                a0, a1 = _RANGES[i]
                b0, b1 = _RANGES[j]
                pts = [_comb(n, a, u, b, v)
                       for a, b in ((a0, b0), (a1, b0), (a1, b1), (a0, b1))]
                d = _comb(n, i, u, j, v)
                direction = tuple(int(round(c)) for c in d)
                cat = sum(1 for c in direction if c != 0)   # 1 face, 2 edge, 3 vertex
                cells.append({"n": n, "u": u, "pts": pts, "dir": direction,
                              "cat": cat, "label": name if cat == 1 else None})
    return cells


CELLS = _build_cells()


##------ OPERACIONES MATEMÁTICAS BÁSICAS ------##
def normalize(v):
    """Normaliza un vector para que tenga longitud uno. Si el vector no tiene longitud válida, evita dividir entre cero y devuelve un resultado seguro."""
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v) if length > 1e-12 else tuple(v)


def cross(a, b):
    """Calcula el producto vectorial entre dos vectores. El resultado es perpendicular a ambos y se utiliza para construir ejes y orientaciones en el espacio 3D."""
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def mul_mv(m, v):
    """Multiplica una matriz por un vector y devuelve el vector transformado. Esta operación permite pasar direcciones entre distintos sistemas de coordenadas."""
    return tuple(m[r][0] * v[0] + m[r][1] * v[1] + m[r][2] * v[2]
                 for r in range(3))


def transpose(m):
    """Devuelve la matriz transpuesta, intercambiando filas por columnas. Se utiliza para invertir transformaciones de rotación cuando la matriz es ortogonal."""
    return tuple(tuple(m[r][c] for r in range(3)) for c in range(3))


def quat_to_matrix(q):
    """Convierte un cuaternión de rotación en una matriz 3×3. Primero normaliza el cuaternión para evitar que una magnitud incorrecta altere la orientación resultante."""
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    w, x, y, z = w / n, x / n, y / n, z / n
    return ((1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)),
            (2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)),
            (2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)))


def matrix_to_quat(m):
    """Convierte una matriz de rotación 3×3 en un cuaternión (w, x, y, z). Selecciona el cálculo adecuado según los valores de la diagonal para mantener estabilidad numérica."""
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0.0:
        s = math.sqrt(tr + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        w = (m[2][1] - m[1][2]) / s
        x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s
        z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        w = (m[0][2] - m[2][0]) / s
        x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s
        z = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        w = (m[1][0] - m[0][1]) / s
        x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s
        z = 0.25 * s
    return (w, x, y, z)


def rotation_from_dir(d):
    """Calcula el cuaternión que orienta la vista hacia el origen desde una dirección determinada. También establece una referencia vertical para evitar giros inesperados alrededor de la mirada."""
    z = normalize(d)
    if abs(z[2]) > 0.999:
        up = (0.0, 1.0, 0.0) if z[2] > 0 else (0.0, -1.0, 0.0)
        x = cross(up, z)
    else:
        x = cross((0.0, 0.0, 1.0), z)
    x = normalize(x)
    y = cross(z, x)
    # Las columnas representan los ejes X, Y y Z.
    m = ((x[0], y[0], z[0]), (x[1], y[1], z[1]), (x[2], y[2], z[2]))
    return matrix_to_quat(m)


def world_to_view(view_quat):
    """Construye la matriz que transforma direcciones del mundo al espacio de la vista a partir del cuaternión de orientación actual."""
    return transpose(quat_to_matrix(view_quat))


def project_cells(view_quat, cx, cy, scale):
    """Proyecta sobre la pantalla las zonas del cubo que miran hacia el usuario y calcula los polígonos que se dibujarán. También descarta caras prácticamente de canto para que no intercepten clics destinados a otras zonas."""
    r = world_to_view(view_quat)
    out = []
    for cell in CELLS:
        facing = mul_mv(r, cell["n"])[2]
        # Evita que las caras sin área válida intercepten clics.
        # Cuando una cara se observa exactamente de perfil, los errores de
        # precisión pueden generar un área prácticamente nula (1e-17).
        # En estos casos, point_in_convex puede detectar puntos dentro de
        # un polígono plano y bloquear los clics destinados a otras celdas.
        # Solo se permiten interacciones con caras que tengan un área real.
        if facing <= 1e-6:
            continue
        poly = []
        for p in cell["pts"]:
            v = mul_mv(r, p)
            poly.append((cx + v[0] * scale, cy + v[1] * scale))
        out.append((cell, poly, facing))
    return r, out


def point_in_convex(p, poly):
    """Comprueba si un punto de la pantalla está dentro de un polígono convexo. Admite polígonos con cualquiera de los dos sentidos de recorrido de sus vértices."""
    sign = 0
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        cr = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
        if cr != 0:
            s = 1 if cr > 0 else -1
            if sign == 0:
                sign = s
            elif sign != s:
                return False
    return True
