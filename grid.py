"""Funciones que mantienen el tamaño de la cuadrícula de la vista 3D sincronizado con las unidades configuradas en cada escena."""

from __future__ import annotations

import bpy

from . import constants, primitives, units

_owner = object()


def settings_for(scene):
    """Obtiene las propiedades de unidades y cuadrícula asociadas a la escena indicada. Si la escena todavía no tiene esas propiedades disponibles, devuelve None."""
    return getattr(scene, constants.UNITS_PROP, None)


def view3d_spaces(scene):
    """Recorre las áreas de pantalla y devuelve cada espacio de vista 3D que está mostrando la escena indicada. Esto permite actualizar todas las vistas que comparten esa escena."""
    wm = bpy.context.window_manager
    for win in wm.windows:
        if win.scene != scene:
            continue
        for area in win.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    yield area, space


def scene_unit(scene):
    """Devuelve la unidad de longitud efectiva de la escena, teniendo en cuenta el sistema de unidades y la unidad elegida en sus propiedades."""
    us = scene.unit_settings
    return units.effective_unit(us.system, us.length_unit)


def grid_scale(scene):
    """Calcula el valor que Blender necesita para representar el tamaño de celda configurado en la cuadrícula de la vista."""
    u = settings_for(scene)
    return units.grid_scale_for(u.grid_step, scene_unit(scene),
                                scene.unit_settings.system)


def apply(scene=None):
    """Aplica el tamaño de celda y las subdivisiones configuradas a todas las vistas 3D de la escena. Devuelve la cantidad de vistas que se actualizaron correctamente."""
    scene = scene or bpy.context.scene
    u = settings_for(scene)
    if u is None:
        return 0
    value = grid_scale(scene)
    count = 0
    for area, space in view3d_spaces(scene):
        overlay = space.overlay
        try:
            overlay.grid_scale = value
            overlay.grid_subdivisions = int(u.grid_subdivisions)
        except (AttributeError, TypeError, ValueError):
            continue
        area.tag_redraw()
        count += 1
    return count


def _notify(scene_name):
    """Recibe el nombre de una escena que cambió sus unidades y actualiza su cuadrícula y el tamaño de los objetos nuevos si corresponde. Se utiliza como aviso interno desde el sistema de seguimiento."""
    scene = bpy.data.scenes.get(scene_name)
    if scene is None:
        return
    u = settings_for(scene)
    if u is None:
        return
    if u.auto_grid:
        apply(scene)
    if u.native_primitives and scene == bpy.context.scene:
        primitives.apply(scene)


def watch():
    """Activa el seguimiento de cambios en las unidades de las escenas. Registra el mecanismo necesario para detectar modificaciones y mantener la cuadrícula sincronizada."""
    try:
        bpy.msgbus.clear_by_owner(_owner)
        for scene in bpy.data.scenes:
            bpy.msgbus.subscribe_rna(key=scene.unit_settings, owner=_owner,
                                     args=(scene.name,), notify=_notify)
    except Exception as exc:  
        print("%s: units watcher not started: %s" % (__package__, exc))
    return None


def unwatch():
    """Desactiva el seguimiento de cambios de unidades y retira los mecanismos registrados para que no sigan ejecutándose cuando el complemento se deshabilite."""
    try:
        bpy.msgbus.clear_by_owner(_owner)
    except Exception:  
        pass
