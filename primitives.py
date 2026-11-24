"""Tamaño nativo para los objetos nuevos. Blender recuerda las últimas propiedades usadas por cada operador de creación (Shift+A), por eso un cubo de 2 mm hace que el siguiente salga de 0.002 m. Aquí se reponen esas propiedades al cambiar de unidad."""

from __future__ import annotations

import bpy

from . import units

# Operadores de creación fuera de los módulos mesh / curve / surface.
_EXTRA = (("object", "empty_add"), ("object", "text_add"),
          ("object", "metaball_add"), ("object", "armature_add"))
_MODULES = ("mesh", "curve", "surface")


def operators():
    """Lista (módulo, nombre) de los operadores de creación de primitivas disponibles en esta versión de Blender."""
    found = []
    for mod in _MODULES:
        for name in dir(getattr(bpy.ops, mod)):
            if name.startswith("primitive_") and name.endswith("_add"):
                found.append((mod, name))
    found.extend(_EXTRA)
    return found


def scene_factor(scene):
    """Cuántas unidades de Blender mide 1 unidad mostrada (1 mm, 1 m, 1 in...) en la escena."""
    us = scene.unit_settings
    unit = units.effective_unit(us.system, us.length_unit)
    return units.native_factor(unit, us.scale_length)


def apply(scene=None):
    """Reescribe las últimas propiedades de longitud (size, radius, depth...) de cada operador de creación con su valor por defecto convertido a la unidad actual. Devuelve la cantidad de operadores actualizados."""
    scene = scene or bpy.context.scene
    factor = scene_factor(scene)
    wm = bpy.context.window_manager
    count = 0
    for mod, name in operators():
        try:
            op = getattr(getattr(bpy.ops, mod), name)
            rna = op.get_rna_type()
            last = wm.operator_properties_last("%s.%s" % (mod, name))
        except (AttributeError, KeyError, RuntimeError, TypeError):
            continue
        if last is None:
            continue
        changed = False
        for prop in rna.properties:
            if (prop.type != 'FLOAT' or prop.subtype != 'DISTANCE'
                    or getattr(prop, "array_length", 0)):
                continue
            value = min(max(prop.default * factor, prop.hard_min),
                        prop.hard_max)
            try:
                setattr(last, prop.identifier, value)
                changed = True
            except (AttributeError, TypeError, ValueError):
                continue
        count += changed
    return count
