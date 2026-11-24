"""Registro y limpieza del complemento. Se encarga de instalar sus clases, propiedades y controladores al activarlo, y de retirar todo correctamente al desactivarlo."""

from __future__ import annotations

import bpy
from bpy.app.handlers import persistent
from bpy.props import PointerProperty

from . import (clip, constants, grid, gizmo, hud, ops, panels, primitives,
               settings, unit_ops)

# Primero se registran los grupos de propiedades, ya que los operadores y paneles necesitan acceder a ellos.
_CLASSES = ((settings.VC_Settings, settings.VC_UnitSettings)
            + ops.classes + unit_ops.classes + gizmo.classes + panels.classes)


def _after_load():
    """Realiza los ajustes que deben aplicarse después de cargar un archivo de Blender. Recupera la visibilidad del gizmo nativo y vuelve a activar el seguimiento de la cuadrícula."""
    settings.apply_native()
    grid.watch()
    clip.start()
    try:
        u = grid.settings_for(bpy.context.scene)
        if u is not None and u.native_primitives:
            primitives.apply(bpy.context.scene)
    except Exception as exc:  # noqa: BLE001
        print("%s: native primitives not applied: %s" % (__package__, exc))
    return None


@persistent
def _on_load(_dummy):
    """Función persistente que se ejecuta después de cargar un archivo .blend. Programa los ajustes posteriores para dar tiempo a Blender a terminar la carga."""
    bpy.app.timers.register(_after_load, first_interval=0.5)


def register():
    """Registra las clases, propiedades, controladores de dibujo y manejadores que necesita el complemento. Comprueba primero que no esté registrado para evitar duplicar elementos."""
    if hasattr(bpy.types.WindowManager, constants.PROP):
        return                                  # El complemento ya está registrado.
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    setattr(bpy.types.WindowManager, constants.PROP,
            PointerProperty(type=settings.VC_Settings))
    setattr(bpy.types.Scene, constants.UNITS_PROP,
            PointerProperty(type=settings.VC_UnitSettings))
    hud.install()
    if _on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_on_load)
    bpy.app.timers.register(_after_load, first_interval=0.5)


def unregister():
    """Desregistra el complemento de forma ordenada. Restaura el gizmo nativo de Blender, elimina manejadores y controladores, borra las propiedades añadidas y retira las clases registradas."""
    try:
        getattr(bpy.context.window_manager, constants.PROP).enabled = False
        settings.apply_native()                 # Se devuelve a Blender la visibilidad de su gizmo nativo.
    except Exception:  # noqa: BLE001
        pass
    if _on_load in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(_on_load)
    grid.unwatch()
    clip.stop()
    hud.remove()
    for prop, owner in ((constants.PROP, bpy.types.WindowManager),
                        (constants.UNITS_PROP, bpy.types.Scene)):
        if hasattr(owner, prop):
            delattr(owner, prop)
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
