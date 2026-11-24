"""Operadores de Blender para las herramientas de unidades y cuadrícula: cambiar unidades, aplicar la cuadrícula, ajustar el tamaño de celda y copiar conversiones."""

from __future__ import annotations

import bpy
from bpy.props import EnumProperty, FloatProperty, StringProperty

from . import constants, grid, primitives, settings, units


class VC_OT_set_units(bpy.types.Operator):
    """Operador que cambia la unidad de longitud de la escena. También ajusta la escala de unidades si el usuario eligió ese comportamiento y actualiza la cuadrícula cuando está en modo automático."""
    bl_idname = "viewcube_nav.set_units"
    bl_label = "Set Units"
    bl_description = ("Show lengths in this unit and resize the viewport "
                      "grid to match")
    bl_options = {'REGISTER', 'UNDO'}

    unit: EnumProperty(name="Unit", items=settings.UNIT_ITEMS,
                       default='METERS')

    def execute(self, context):
        """Realiza la acción solicitada por el operador y devuelve a Blender el resultado correspondiente. En cada operador, esta función aplica el cambio, actualiza la interfaz o copia el valor indicado."""
        scene = context.scene
        us = scene.unit_settings
        u = grid.settings_for(scene)
        try:
            # cambia el sistema de unidades, porque las unidades de longitud disponibles dependen de esta opción.
            us.system = units.system_of(self.unit)
            us.length_unit = self.unit
        except (TypeError, ValueError) as exc:
            self.report({'ERROR'}, "Could not set %s: %s" % (self.unit, exc))
            return {'CANCELLED'}
        if u is not None and u.scale_mode == 'MATCH':
            us.scale_length = units.unit_scale_for(self.unit)
        if u is not None and u.auto_grid:
            grid.apply(scene)
        if u is not None and u.native_primitives:
            primitives.apply(scene)
        self.report({'INFO'}, "Units: %s" % units.label(self.unit))
        return {'FINISHED'}


class VC_OT_apply_grid(bpy.types.Operator):
    """Operador que aplica manualmente a las vistas 3D el tamaño de cuadrícula configurado en el panel."""
    bl_idname = "viewcube_nav.apply_grid"
    bl_label = "Apply Grid"
    bl_description = "Resize the viewport grid to the cell size set here"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        """Realiza la acción solicitada por el operador y devuelve a Blender el resultado correspondiente. En cada operador, esta función aplica el cambio, actualiza la interfaz o copia el valor indicado."""
        count = grid.apply(context.scene)
        self.report({'INFO'}, "Grid updated in %d view%s"
                    % (count, "" if count == 1 else "s"))
        return {'FINISHED'}


class VC_OT_grid_step(bpy.types.Operator):
    """Operador que multiplica el tamaño actual de la celda de cuadrícula por un factor. Se utiliza para los botones de aumentar o reducir el tamaño."""
    bl_idname = "viewcube_nav.grid_step"
    bl_label = "Scale Grid Cell"
    bl_description = "Multiply the grid cell size"
    bl_options = {'INTERNAL'}

    factor: FloatProperty(default=10.0)

    def execute(self, context):
        """Realiza la acción solicitada por el operador y devuelve a Blender el resultado correspondiente. En cada operador, esta función aplica el cambio, actualiza la interfaz o copia el valor indicado."""
        u = grid.settings_for(context.scene)
        if u is None:
            return {'CANCELLED'}
        u.grid_step = max(1e-6, u.grid_step * self.factor)
        return {'FINISHED'}


class VC_OT_copy_value(bpy.types.Operator):
    """Operador que copia al portapapeles el valor de conversión seleccionado para que el usuario pueda pegarlo en otro campo o aplicación."""
    bl_idname = "viewcube_nav.copy_value"
    bl_label = "Copy Value"
    bl_description = "Copy this converted value to the clipboard"
    bl_options = {'INTERNAL'}

    text: StringProperty()

    def execute(self, context):
        """Realiza la acción solicitada por el operador y devuelve a Blender el resultado correspondiente. En cada operador, esta función aplica el cambio, actualiza la interfaz o copia el valor indicado."""
        context.window_manager.clipboard = self.text
        self.report({'INFO'}, "Copied %s" % self.text)
        return {'FINISHED'}


classes = (VC_OT_set_units, VC_OT_apply_grid, VC_OT_grid_step,
           VC_OT_copy_value)
