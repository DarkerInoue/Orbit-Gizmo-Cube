"""Paneles de la barra lateral de la vista 3D. Desde aquí se muestran y organizan los ajustes del cubo, las unidades y la cuadrícula."""

from __future__ import annotations

import bpy

from . import constants, grid, units

CATEGORY = "Orbit Gizmo Cube"


class VC_PT_panel(bpy.types.Panel):
    """Panel principal del complemento en la barra lateral de la vista 3D. Muestra los controles generales para activar el cubo y ajustar su apariencia."""
    bl_label = "Navigation"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = CATEGORY

    def draw(self, context):
        """Construye los controles del panel principal para activar el complemento y ajustar su apariencia."""
        s = getattr(context.window_manager, constants.PROP)
        col = self.layout.column()
        col.prop(s, "enabled")
        col.prop(s, "show_navbar")
        col.prop(s, "show_tooltips")
        col.prop(s, "hide_native")
        col.separator()
        col.prop(s, "size")
        col.prop(s, "opacity")
        col.prop(s, "anim_time")
        col.prop(s, "frame_margin")
        col.prop(s, "step_angle")
        col.prop(s, "auto_clip")


def _unit_button(row, uid, active):
    """Añade a la fila un botón para elegir la unidad indicada. Marca visualmente la unidad activa y contempla versiones de Blender que no admiten el parámetro visual depress."""
    try:
        op = row.operator("viewcube_nav.set_units", text=units.symbol(uid),
                          depress=active)
    except TypeError:              
        op = row.operator("viewcube_nav.set_units", text=units.symbol(uid))
    op.unit = uid


class VC_PT_units(bpy.types.Panel):
    """Panel de herramientas de unidades y cuadrícula. Permite cambiar la unidad de la escena, ajustar el tamaño de la cuadrícula y convertir valores de longitud."""
    bl_label = "Units & Grid"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = CATEGORY

    def draw(self, context):
        """Construye la interfaz de unidades y cuadrícula: muestra la unidad actual, los botones de cambio, los ajustes de la cuadrícula y los resultados del conversor."""
        layout = self.layout
        scene = context.scene
        us = scene.unit_settings
        u = grid.settings_for(scene)
        if u is None:
            layout.label(text="Units settings unavailable", icon='ERROR')
            return
        unit = units.effective_unit(us.system, us.length_unit)

        ##------ ESTADO ACTUAL DE LAS UNIDADES ------##
        box = layout.box()
        col = box.column(align=True)
        if unit:
            col.label(text="Shown in: %s (%s)" % (units.label(unit),
                                                  units.symbol(unit)))
            col.label(text="Unit Scale: %s" % units.fmt(us.scale_length))
        else:
            col.label(text="Unit system: None")
        cell, fine = units.describe_grid(u.grid_step, unit,
                                         u.grid_subdivisions, us.system)
        col.label(text="Grid cell: %s" % cell)
        col.label(text="Finest line: %s" % fine)

        ##------ CAMBIO RÁPIDO DE UNIDADES ------##
        layout.label(text="Switch units")
        for ids in (units.QUICK_UNITS[:4], units.QUICK_UNITS[4:]):
            row = layout.row(align=True)
            for uid in ids:
                _unit_button(row, uid, uid == unit)
        layout.prop(u, "scale_mode", text="")
        layout.prop(u, "native_primitives")

        ##------ CONFIGURACIÓN DE LA CUADRÍCULA ------##
        layout.separator()
        layout.label(text="Grid")
        layout.prop(u, "auto_grid")
        col = layout.column(align=True)
        label = "Cell (%s)" % units.symbol(unit) if unit else "Cell (BU)"
        col.prop(u, "grid_step", text=label)
        col.prop(u, "grid_subdivisions")
        row = layout.row(align=True)
        op = row.operator("viewcube_nav.grid_step", text="\u00f710")
        op.factor = 0.1
        op = row.operator("viewcube_nav.grid_step", text="\u00d710")
        op.factor = 10.0
        if not u.auto_grid:
            layout.operator("viewcube_nav.apply_grid", icon='MESH_GRID')
        space = context.space_data
        if space and space.type == 'VIEW_3D':
            layout.prop(space.overlay, "show_floor")

        ##------ CONVERSOR DE UNIDADES ------##
        layout.separator()
        layout.label(text="Converter")
        col = layout.column(align=True)
        col.prop(u, "convert_value")
        col.prop(u, "convert_from", text="")
        col = layout.column(align=True)
        for uid, _label, symbol, value in units.all_conversions(
                u.convert_value, u.convert_from):
            if uid == u.convert_from:
                continue
            row = col.row(align=True)
            row.label(text="%s %s" % (units.fmt(value), symbol))
            op = row.operator("viewcube_nav.copy_value", text="",
                              icon='COPYDOWN')
            op.text = units.fmt(value)


classes = (VC_PT_panel, VC_PT_units)
