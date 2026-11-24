"""Dibujo de los elementos que aparecen encima de la vista 3D: cubo, caras, etiquetas, flechas de giro, barra de herramientas e indicaciones emergentes."""

from __future__ import annotations

import math

import blf
import bpy
import gpu
from gpu_extras.batch import batch_for_shader

from . import actions, constants, cube_math, icons, layout

_state = {}          
_shader = None
_handle = None

FACE, EDGE, CORNER = (1.00, 0.42, 0.06), (0.88, 0.29, 0.025), (0.68, 0.19, 0.015)
HOVER = (0.20, 0.52, 0.96)
LINE = (0.10, 0.11, 0.13, 0.9)
ICON = (0.88, 0.90, 0.93, 1.0)
ICON_ACTIVE = (1.00, 0.55, 0.15, 1.0)
PANEL_FILL = (0.075, 0.085, 0.105)
PANEL_LINE = (0.24, 0.26, 0.29)


def st(region):
    """Devuelve el espacio de almacenamiento de datos temporales asociado a la región de la vista. Se utiliza para conservar información de dibujo entre llamadas."""
    return _state.setdefault(region.as_pointer(), {})


##------ GPU HELPERS ------##
def get_shader():
    """Obtiene o prepara el shader de GPU que necesita el complemento para dibujar sus elementos en pantalla. Reutiliza el recurso cuando ya está creado."""
    global _shader
    if _shader is None:
        for name in ("UNIFORM_COLOR", "2D_UNIFORM_COLOR"):
            try:
                _shader = gpu.shader.from_builtin(name)
                break
            except Exception:  
                continue
    return _shader


def set_font_size(px):
    """Configura el tamaño de fuente utilizado por Blender para dibujar textos del HUD, teniendo en cuenta la escala de interfaz correspondiente."""
    try:
        blf.size(0, px)
    except TypeError:
        blf.size(0, px, 72)


def _draw_batch(shader, mode, pts, color, indices=None):
    """Envía a la GPU un conjunto de vértices para dibujarlos con el modo, color y posibles índices indicados. Es la función común que utilizan las rutinas de dibujo."""
    if not pts:
        return
    verts = [(p[0], p[1], 0.0) for p in pts]
    shader.bind()
    shader.uniform_float("color", color)
    if indices:
        batch = batch_for_shader(shader, mode, {"pos": verts}, indices=indices)
    else:
        batch = batch_for_shader(shader, mode, {"pos": verts})
    batch.draw(shader)


def fill_poly(shader, pts, color):
    """Dibuja un polígono relleno con el color indicado. Convierte sus puntos en una figura que la GPU puede representar."""
    _draw_batch(shader, 'TRIS', pts, color,
                [(0, i, i + 1) for i in range(1, len(pts) - 1)])


def line_loop(shader, pts, color):
    """Dibuja una línea que conecta todos los puntos y cierra el contorno uniendo el último con el primero."""
    _draw_batch(shader, 'LINE_LOOP', pts, color)


def line_strip(shader, pts, color):
    """Dibuja una línea continua que conecta los puntos en el orden recibido, sin cerrar automáticamente el recorrido."""
    _draw_batch(shader, 'LINE_STRIP', pts, color)


def rounded_rect_points(cx, cy, width, height, radius, segments=8):
    """Calcula los vértices que forman el contorno de un rectángulo con esquinas redondeadas. El número de segmentos determina qué tan suave se ve cada curva."""
    radius = min(radius, width / 2, height / 2)
    pts = []
    corners = (
        (cx + width / 2 - radius, cy + height / 2 - radius, 0, 90),
        (cx - width / 2 + radius, cy + height / 2 - radius, 90, 180),
        (cx - width / 2 + radius, cy - height / 2 + radius, 180, 270),
        (cx + width / 2 - radius, cy - height / 2 + radius, 270, 360),
    )
    for x, y, a0, a1 in corners:
        for i in range(segments + 1):
            a = math.radians(a0 + (a1 - a0) * i / segments)
            pts.append((x + radius * math.cos(a), y + radius * math.sin(a)))
    return pts


def _tri_arrow(c, d, a):
    """Calcula los tres vértices de una flecha triangular a partir de su centro, dirección y tamaño. El resultado se utiliza para dibujar indicadores de navegación."""
    dx, dy = d
    px, py = -dy, dx
    return [(c[0] + dx * a, c[1] + dy * a),
            (c[0] - dx * a * 0.6 + px * a, c[1] - dy * a * 0.6 + py * a),
            (c[0] - dx * a * 0.6 - px * a, c[1] - dy * a * 0.6 - py * a)]


def _arc_arrow(c, r, deg0, deg1, n=14):
    """Genera los puntos de un arco con forma de flecha entre dos ángulos. Sirve para representar visualmente las direcciones de giro alrededor del cubo."""
    t0, t1 = math.radians(deg0), math.radians(deg1)
    pts = [(c[0] + r * math.cos(t0 + (t1 - t0) * k / n),
            c[1] + r * math.sin(t0 + (t1 - t0) * k / n)) for k in range(n + 1)]
    sgn = 1 if t1 > t0 else -1
    tan = (-math.sin(t1) * sgn, math.cos(t1) * sgn)
    return pts, _tri_arrow(pts[-1], tan, r * 0.7)


##------ DISTRIBUCIÓN Y DETECCIÓN DE CLICS ------##
def get_layout(context):
    """Calcula y devuelve la distribución de los elementos del HUD para la región actual. Incluye las posiciones del cubo, las flechas y la barra de herramientas."""
    region, area = context.region, context.area
    s = getattr(context.window_manager, constants.PROP)
    right, top = region.width, region.height
    if area:
        own = region.as_pointer()
        for r in area.regions:
            if r.as_pointer() == own:
                continue
            if r.type == 'UI' and r.width > 1 and r.alignment == 'RIGHT':
                right = min(right, r.x - region.x)
            elif r.type in {'HEADER', 'TOOL_HEADER'} and r.alignment == 'TOP':
                top = min(top, r.y - region.y)
    return layout.build(right, top, context.preferences.system.ui_scale,
                        s.size, s.show_navbar)


def pick(context, loc):
    """Identifica qué elemento interactivo está debajo de una coordenada de la región. Puede devolver un botón, una flecha de giro o indicar que no hay ningún elemento seleccionado."""
    L = get_layout(context)
    _, cells = cube_math.project_cells(tuple(actions.current_rotation(context)),
                                       L.cx, L.cy, L.s)
    return layout.hit_test(L, loc[0], loc[1], cells)


##------ DIBUJO DE LOS ELEMENTOS EN PANTALLA ------##
def _tooltip_text(name, perspective):
    """Prepara el texto que debe mostrarse como ayuda emergente para el elemento indicado. Tiene en cuenta el estado de la proyección para mostrar el nombre correcto de la acción."""
    if name == "PROJECTION":
        return ("Perspective - click for Orthographic" if perspective
                else "Orthographic - click for Perspective")
    return constants.TOOLTIPS.get(name, "")


def _draw_navbar(shader, ctx, L, alpha, hit, s):
    """Dibuja la barra de herramientas situada debajo del cubo. Representa cada botón, su estado visual y la zona que se utiliza para detectar el cursor y mostrar su ayuda."""
    sc = L.sc
    pcx, pcy, pw, ph = L.panel
    outline = rounded_rect_points(pcx, pcy, pw, ph, 13 * sc)
    fill_poly(shader, outline, (*PANEL_FILL, 0.88 * alpha))
    line_loop(shader, outline, (*PANEL_LINE, 0.72 * alpha))

    rv3d = ctx.region_data
    in_camera = rv3d.view_perspective == 'CAMERA'
    perspective = bool(rv3d.is_perspective)
    hovered_name = None
    for name, (bx, by) in L.buttons:
        hovered = hit == ("BUTTON", name)
        if hovered:
            hovered_name = name
            rect = rounded_rect_points(bx, by, L.btn_hw * 2 - 4 * sc,
                                       L.btn_hh * 2 - 4 * sc, 8 * sc)
            fill_poly(shader, rect, (*HOVER, 0.95))
        active = ((name == "CAMERA" and in_camera)
                  or (name == "PROJECTION" and perspective))
        color = (1.0, 1.0, 1.0, 1.0) if hovered else (
            ICON_ACTIVE if active else ICON)
        _draw_batch(shader, 'TRIS',
                    icons.build_icon(name, bx, by, L.icon_k, perspective),
                    color)

    if hovered_name and s.show_tooltips:
        text = _tooltip_text(hovered_name, perspective)
        set_font_size(11 * sc)
        w, h = blf.dimensions(0, text)
        by = dict(L.buttons)[hovered_name][1]
        right_edge = pcx - pw / 2 - 8 * sc
        box_w, box_h = w + 16 * sc, h + 12 * sc
        box = rounded_rect_points(right_edge - box_w / 2, by, box_w, box_h, 6 * sc)
        fill_poly(shader, box, (*PANEL_FILL, 0.95))
        line_loop(shader, box, (*PANEL_LINE, 0.9))
        blf.color(0, 0.92, 0.94, 0.97, 1.0)
        blf.position(0, right_edge - box_w + 8 * sc, by - h * 0.35, 0)
        blf.draw(0, text)


def draw_viewcube():
    """Dibuja todos los componentes del sistema de navegación en la vista 3D: caras del cubo, etiquetas, flechas de giro, barra de herramientas y ayudas emergentes."""
    ctx = bpy.context
    s = getattr(ctx.window_manager, constants.PROP, None)
    region, rv3d = ctx.region, ctx.region_data
    if s is None or not s.enabled or region is None or rv3d is None:
        return
    shader = get_shader()
    if shader is None:
        return

    L = get_layout(ctx)
    hit = st(region).get("hit")
    alpha = s.opacity
    sc = L.sc

    try:
        gpu.state.blend_set('ALPHA')
    except (AttributeError, TypeError, RuntimeError):
        return
    R, cells = cube_math.project_cells(tuple(actions.current_rotation(ctx)),
                                       L.cx, L.cy, L.s)

    ##------ CARAS, ARISTAS Y ESQUINAS DEL CUBO ------##
    for c, poly, facing in cells:
        base = FACE if c["cat"] == 1 else (EDGE if c["cat"] == 2 else CORNER)
        if hit and hit[0] == "CELL" and hit[1] == c["dir"]:
            col = (*HOVER, alpha)
        else:
            f = 0.75 + 0.25 * facing
            col = (base[0] * f, base[1] * f, base[2] * f, alpha)
        fill_poly(shader, poly, col)
        line_loop(shader, poly, LINE)

    ##------ ETIQUETAS DE LAS CARAS ------##
    for c, poly, facing in cells:
        if c["label"] is None or facing < 0.3:
            continue
        center = (sum(p[0] for p in poly) / 4, sum(p[1] for p in poly) / 4)
        uv = cube_math.mul_mv(R, c["u"])
        ang = math.atan2(uv[1], uv[0])
        du, dv = (math.cos(ang), math.sin(ang)), (-math.sin(ang), math.cos(ang))
        set_font_size(10 * sc)
        w, _h = blf.dimensions(0, c["label"])
        target = 1.44 * L.s * 0.9
        size = max(5.0, min(16.0 * sc, 10 * sc * target / max(w, 1)))
        set_font_size(size)
        w, h = blf.dimensions(0, c["label"])
        pos = (center[0] - du[0] * w / 2 - dv[0] * h * 0.38,
               center[1] - du[1] * w / 2 - dv[1] * h * 0.38)
        fade = max(0.0, min(1.0, (facing - 0.25) / 0.4))
        rotated = False
        try:
            blf.enable(0, blf.ROTATION)
            blf.rotation(0, ang)
            rotated = True
        except (AttributeError, TypeError, RuntimeError):
            pass
        blf.color(0, 0.92, 0.94, 0.97, fade)
        blf.position(0, pos[0], pos[1], 0)
        blf.draw(0, c["label"])
        if rotated:
            try:
                blf.disable(0, blf.ROTATION)
            except (AttributeError, TypeError, RuntimeError):
                pass

    ##------ FLECHAS PARA GIRAR LA VISTA ------##
    dirs = {"UP": (0, 1), "DOWN": (0, -1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
    a = L.arrow_size
    for name, pos in L.arrows.items():
        col = (*HOVER, 1.0) if hit == ("ARROW", name) else (0.75, 0.78, 0.82, alpha)
        if name in dirs:
            fill_poly(shader, _tri_arrow(pos, dirs[name], a), col)
        else:
            pts, head = (_arc_arrow(pos, a * 0.9, 150, 30) if name == "ROLL_R"
                         else _arc_arrow(pos, a * 0.9, 30, 150))
            line_strip(shader, pts, col)
            fill_poly(shader, head, col)

    ##------ BARRA DE HERRAMIENTAS (SE DIBUJA AL FINAL PARA QUE SU AYUDA QUEDE ENCIMA) ------##
    if L.show_navbar:
        _draw_navbar(shader, ctx, L, alpha, hit, s)

    try:
        gpu.state.blend_set('NONE')
    except (AttributeError, TypeError, RuntimeError):
        pass


##------ REGISTRO DEL CONTROLADOR DE DIBUJO ------##
def install():
    """Registra el controlador de dibujo del HUD en Blender para que el cubo y sus controles aparezcan sobre la vista 3D."""
    global _handle
    if _handle is None:
        _handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_viewcube, (), 'WINDOW', 'POST_PIXEL')


def remove():
    """Retira el controlador de dibujo del HUD y libera su registro cuando el complemento se desactiva."""
    global _handle
    if _handle is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        except Exception:  
            pass
        _handle = None
    _state.clear()
