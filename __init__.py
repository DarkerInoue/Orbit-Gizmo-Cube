#Orbit Gizmo Cube Add-on
# Created by Darker Inoue

import importlib

# Lista de módulos del addon en orden de dependencia
modulesDI = (
    "constants", "cube_math", "layout", "icons", "units",
    "primitives", "clip", "actions", "grid", "settings",
    "hud", "ops", "unit_ops", "gizmo", "panels", "startup",
)

# Importa y recarga los módulos para aplicar los cambios realizados
# manteniendo los módulos disponibles en memoria
for name in modulesDI:
    module = importlib.import_module(f".{name}", __package__)
    globals()[name] = importlib.reload(module)

# Expone las funciones de registro y desregistro del addon
from .startup import register, unregister

bl_info = {
    "name": "Orbit Gizmo Cube",
    "author": "Darker Inoue",
    "version": (1, 5, 1),
    "blender": (5, 1, 0),
    "location": "3D View (top-right corner) / Sidebar N > Orbit Gizmo Cube",
    "description": "Orange orbit gizmo cube with a toolbar (home, zoom, pan, "
                   "camera, perspective), plus a units converter that keeps "
                   "the viewport grid in step with the scene units.",
    "category": "3D View",
}
