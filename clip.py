"""Ajuste automático de los planos de recorte (clip) de la vista 3D según la distancia de la vista. Evita que los objetos muy pequeños (mm, µm) o muy grandes se vean cortados al acercarse o alejarse."""

from __future__ import annotations

import bpy

from . import constants

INTERVAL = 0.05        # Segundos entre comprobaciones.
NEAR_RATIO = 1e-3      # Plano cercano = distancia de la vista x 0.001.
FAR_RATIO = 1e3        # Plano lejano = distancia de la vista x 1000.
NEAR_MIN = 1e-6        # Mínimo que admite Blender para clip_start.
FAR_MAX = 1e12
TOLERANCE = 0.05       # No se escribe si el cambio es menor al 5 %.


def compute_range(distance):
    """Calcula el plano de recorte cercano y lejano adecuados para una distancia de vista dada. Mantiene una proporción fija entre ambos para conservar la precisión de profundidad."""
    near = max(distance * NEAR_RATIO, NEAR_MIN)
    far = min(distance * FAR_RATIO, FAR_MAX)
    far = max(far, near * 10.0)
    return near, far


def _regions(space):
    """Devuelve los datos de región (RegionView3D) de un espacio 3D. En vista cuádruple devuelve las cuatro vistas; si no, la vista principal."""
    quad = list(getattr(space, "region_quadviews", []) or [])
    if quad:
        return quad
    return [getattr(space, "region_3d", None)]


def fit(space):
    """Ajusta clip_start y clip_end de un espacio 3D a su distancia de vista actual. Ignora la vista de cámara, que usa el recorte de la propia cámara. Devuelve True si hubo cambios."""
    dists = []
    for rv3d in _regions(space):
        if rv3d is None or rv3d.view_perspective == 'CAMERA':
            continue
        if rv3d.view_distance > 0.0:
            dists.append(rv3d.view_distance)
    if not dists:
        return False
    near, far = compute_range(min(dists))
    if (abs(space.clip_start - near) <= near * TOLERANCE
            and abs(space.clip_end - far) <= far * TOLERANCE):
        return False
    try:
        # El orden evita que, momentáneamente, el plano cercano supere al lejano.
        if far > space.clip_end:
            space.clip_end = far
            space.clip_start = near
        else:
            space.clip_start = near
            space.clip_end = far
    except (AttributeError, TypeError, ValueError):
        return False
    return True


def _tick():
    """Función del temporizador: revisa todas las vistas 3D abiertas y ajusta su recorte si la opción está activada. Nunca lanza errores para que el temporizador no se detenga."""
    try:
        wm = bpy.context.window_manager
        s = getattr(wm, constants.PROP, None)
        if s is not None and s.auto_clip:
            for win in wm.windows:
                for area in win.screen.areas:
                    if area.type != 'VIEW_3D':
                        continue
                    for space in area.spaces:
                        if space.type == 'VIEW_3D' and fit(space):
                            area.tag_redraw()
    except Exception:  
        pass
    return INTERVAL


def start():
    """Activa el temporizador que mantiene el recorte de la vista sincronizado con el zoom."""
    if not bpy.app.timers.is_registered(_tick):
        bpy.app.timers.register(_tick, first_interval=INTERVAL, persistent=True)


def stop():
    """Desactiva el temporizador de recorte automático."""
    try:
        if bpy.app.timers.is_registered(_tick):
            bpy.app.timers.unregister(_tick)
    except Exception:  
        pass
