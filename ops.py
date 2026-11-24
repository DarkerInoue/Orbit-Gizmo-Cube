"""Operadores de Blender que realizan los cambios de orientación con animación y alternan el tipo de proyección de la vista."""

from __future__ import annotations

import time

import bpy
from bpy.props import BoolProperty, FloatVectorProperty
from mathutils import Quaternion

from . import actions, constants


class VC_OT_set_view(bpy.types.Operator):
    """Operador encargado de cambiar la orientación de la vista hacia una cara, arista o esquina del cubo. Puede animar la transición para que el movimiento no sea brusco."""
    bl_idname = "viewcube_nav.set_view"
    bl_label = "Set View"
    bl_description = "Turn the view to a direction, optionally framing the selection"
    bl_options = {'INTERNAL'}

    rotation: FloatVectorProperty(size=4, subtype='QUATERNION',
                                  default=(1, 0, 0, 0))
    frame: BoolProperty(default=True)

    @classmethod
    def poll(cls, context):
        """Comprueba que el operador se esté ejecutando desde una vista 3D válida y que exista la información de región necesaria para modificar la orientación."""
        return bool(context.space_data and context.space_data.type == 'VIEW_3D'
                    and context.region_data)

    def invoke(self, context, event):
        """Inicia el cambio de vista solicitado. Guarda la orientación, el centro y la distancia actuales, prepara el temporizador de animación y determina el destino de la transición."""
        rv3d = context.region_data
        s = getattr(context.window_manager, constants.PROP)
        # A camera view has no rotation of its own to animate from.
        actions.leave_camera(context)
        self.q0 = actions.current_rotation(context)
        self.q1 = Quaternion(self.rotation).normalized()
        if self.q0.dot(self.q1) < 0:
            self.q1 = Quaternion([-c for c in self.q1])
        # The projection - perspective or orthographic - is left as it is.
        self.l0, self.d0 = rv3d.view_location.copy(), rv3d.view_distance
        self.l1, self.d1 = self.l0.copy(), self.d0
        if self.frame:
            res = actions.compute_frame(context, self.q1)
            if res:
                self.l1, self.d1 = res[0], res[1] * s.frame_margin
        self.dur = s.anim_time
        if self.dur <= 0.001:
            self._apply(context, 1.0)
            return {'FINISHED'}
        self.t0 = time.time()
        wm = context.window_manager
        self._timer = wm.event_timer_add(1 / 90, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def _apply(self, context, e):
        """Aplica un punto intermedio de la animación. Interpola la orientación y la distancia entre el estado inicial y el destino para producir un movimiento progresivo."""
        rv3d = context.region_data
        if rv3d is None:
            return
        rv3d.view_rotation = self.q0.slerp(self.q1, e)
        rv3d.view_location = self.l0.lerp(self.l1, e)
        rv3d.view_distance = self.d0 + (self.d1 - self.d0) * e
        actions.redraw(context)

    def _end(self, context):
        """Detiene la animación y elimina el temporizador que se había registrado para actualizar la vista."""
        context.window_manager.event_timer_remove(self._timer)

    def modal(self, context, event):
        """Recibe los eventos mientras se reproduce la animación. Actualiza la vista en cada intervalo, termina al llegar al destino y permite cancelar o interrumpir el movimiento con la entrada del usuario."""
        if event.type == 'TIMER':
            t = min((time.time() - self.t0) / self.dur, 1.0)
            self._apply(context, 1 - (1 - t) ** 3)
            if t >= 1.0:
                self._end(context)
                return {'FINISHED'}
            return {'RUNNING_MODAL'}
        if event.value == 'PRESS' and event.type in {
                'ESC', 'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE',
                'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            self._end(context)
            return {'FINISHED', 'PASS_THROUGH'}
        return {'PASS_THROUGH'}

    def cancel(self, context):
        """Limpia los recursos de la animación cuando Blender cancela el operador. Comprueba que el temporizador pueda retirarse sin provocar un error adicional."""
        try:
            self._end(context)
        except Exception:  # noqa: BLE001
            pass


class VC_OT_toggle_projection(bpy.types.Operator):
    """Operador que alterna la proyección de la vista 3D entre perspectiva y ortográfica mediante la función central de acciones."""
    bl_idname = "viewcube_nav.toggle_projection"
    bl_label = "Perspective / Orthographic"
    bl_description = "Switch the 3D view between perspective and orthographic"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        """Comprueba que el operador se esté ejecutando desde una vista 3D válida y que exista la información de región necesaria para modificar la orientación."""
        return bool(context.space_data and context.space_data.type == 'VIEW_3D'
                    and context.region_data)

    def execute(self, context):
        """Ejecuta el cambio de proyección y comunica a Blender que la operación terminó correctamente."""
        actions.toggle_projection(context)
        return {'FINISHED'}


classes = (VC_OT_set_view, VC_OT_toggle_projection)
