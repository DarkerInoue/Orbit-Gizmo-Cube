"""Definición y actualización de las propiedades del complemento. Incluye los ajustes visuales del cubo y las opciones de unidades y cuadrícula que se guardan por escena."""

from __future__ import annotations

import math

import bpy
from bpy.props import (BoolProperty, EnumProperty, FloatProperty,
                       IntProperty)

from . import constants, primitives, units


def redraw_all(self=None, context=None):
    """Solicita que todas las áreas de vista 3D abiertas se vuelvan a dibujar. Se ejecuta cuando cambia una propiedad visual para que el usuario vea el ajuste sin tener que mover la vista."""
    wm = bpy.context.window_manager
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def apply_native(self=None, context=None):
    """Sincroniza la visibilidad del gizmo de navegación nativo de Blender con la opción del complemento. También actualiza las áreas 3D para reflejar el cambio."""
    try:
        wm = bpy.context.window_manager
        s = getattr(wm, constants.PROP)
    except Exception:  
        return
    hide = s.enabled and s.hide_native
    for win in wm.windows:
        for area in win.screen.areas:
            if area.type != 'VIEW_3D':
                continue
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.show_gizmo_navigate = not hide
            area.tag_redraw()


class VC_Settings(bpy.types.PropertyGroup):
    """Grupo de propiedades que almacena los ajustes generales del cubo de navegación, como activación, visibilidad de la barra, tamaño, opacidad y duración de la animación."""
    enabled: BoolProperty(name="Enable ViewCube", default=True,
                          update=apply_native)
    show_navbar: BoolProperty(name="Show Navigation Bar", default=True,
                              update=redraw_all)
    show_tooltips: BoolProperty(name="Show Button Names", default=True,
                                description="Name the toolbar button under the pointer",
                                update=redraw_all)
    hide_native: BoolProperty(name="Hide Blender Navigation Gizmo",
                              default=True, update=apply_native)
    size: IntProperty(name="Size", default=150, min=90, max=320,
                      update=redraw_all)
    opacity: FloatProperty(name="Opacity", default=0.9, min=0.2, max=1.0,
                           update=redraw_all)
    anim_time: FloatProperty(name="Animation Duration (s)", default=0.3,
                             min=0.0, max=2.0)
    frame_margin: FloatProperty(
        name="Framing Margin", default=1.15, min=0.8, max=4.0,
        description="Multiplies the distance to the object (1 = tight fit)")
    auto_clip: BoolProperty(
        name="Auto Clip Distance", default=True,
        description="Adjust the viewport clip start / end to the zoom level, "
                    "so very small or very large objects are not cut off",
        update=redraw_all)
    step_angle: FloatProperty(name="Arrow Step", default=math.pi / 2,
                              min=math.radians(5), max=math.radians(90),
                              subtype='ANGLE')


##------ PROPIEDADES DE UNIDADES Y CUADRÍCULA ------##
UNIT_ITEMS = [(uid, "%s (%s)" % (data[0], data[1]), "")
              for uid, data in units.UNITS.items()]


def _on_grid_changed(self, context):
    """Se ejecuta cuando cambia una propiedad relacionada con la cuadrícula. Si el modo automático está activo, vuelve a aplicar el tamaño de cuadrícula a la escena propietaria."""
    if self.auto_grid:
        from . import grid
        grid.apply(self.id_data)


def _on_native_changed(self, context):
    """Se ejecuta al activar el tamaño nativo de objetos nuevos: aplica de inmediato la unidad actual."""
    if self.native_primitives:
        primitives.apply(self.id_data)


class VC_UnitSettings(bpy.types.PropertyGroup):
    """Grupo de propiedades guardado dentro de cada escena. Contiene las opciones de sincronización de cuadrícula, tamaño de celda, subdivisiones y conversión de unidades."""
    auto_grid: BoolProperty(
        name="Keep Grid in Step with Units", default=True,
        description="Whenever the scene's unit system, length unit or unit "
                    "scale changes - here or in Scene Properties - resize "
                    "the viewport grid to match",
        update=_on_grid_changed)
    grid_step: FloatProperty(
        name="Grid Cell", default=1.0, min=1e-6, soft_max=1000.0,
        precision=4,
        description="Size of one grid cell, in the scene's display unit",
        update=_on_grid_changed)
    grid_subdivisions: IntProperty(
        name="Subdivisions", default=10, min=1, max=100,
        description="Lines drawn inside each grid cell",
        update=_on_grid_changed)
    scale_mode: EnumProperty(
        name="When Switching Units",
        items=[('KEEP', "Keep Real Size",
                "Only change how lengths are shown. Unit Scale is left "
                "alone, so every object keeps its real-world size"),
               ('MATCH', "1 Blender Unit = 1 Unit",
                "Also set Unit Scale so one Blender unit equals one of the "
                "chosen unit (1 BU = 1 mm in millimetres). Existing objects "
                "keep their Blender-unit size, so they change real size")],
        default='KEEP')
    native_primitives: BoolProperty(
        name="Native Size for New Objects", default=True,
        description="Shift+A creates objects at their default size in the "
                    "current unit (2 mm cube in mm, 2 m cube in m...) "
                    "instead of repeating the size used in the previous unit",
        update=_on_native_changed)
    convert_value: FloatProperty(name="Value", default=1.0, precision=6,
                                 description="The length to convert")
    convert_from: EnumProperty(name="From", items=UNIT_ITEMS,
                               default='METERS')
