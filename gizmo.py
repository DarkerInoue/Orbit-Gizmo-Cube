"""Control de interacción del cubo dentro de Blender. Este archivo recibe los clics y arrastres del ratón y los convierte en acciones de navegación."""

from __future__ import annotations

import bpy
from mathutils import Vector

from . import actions, constants, cube_math, hud


class VC_GT_cube(bpy.types.Gizmo):
    """Gizmo principal que recibe la interacción del ratón sobre el cubo de navegación. Se encarga de detectar la zona pulsada y mantener el seguimiento mientras el usuario hace clic o arrastra."""
    bl_idname = "VIEW3D_GT_viewcube_nav_cube"

    def draw(self, context):
        """Dibuja el gizmo en la vista 3D. La parte visual del cubo y sus controles se delega al sistema HUD para mantener separadas la interacción y la representación."""
        pass                       

    def test_select(self, context, location):
        """Determina si el cursor está encima de alguna zona interactiva del gizmo. Devuelve el identificador de selección correspondiente para que Blender sepa cuándo puede activarse."""
        try:
            hit = hud.pick(context, location)
        except Exception:  
            hit = None
        state = hud.st(context.region)
        if state.get("hit") != hit:
            state["hit"] = hit
            context.region.tag_redraw()
        return 0 if hit else -1

    def invoke(self, context, event):
        """Inicia la interacción cuando el usuario pulsa sobre el gizmo. Vuelve a calcular qué zona está debajo del cursor en ese mismo instante, evitando depender de un resultado de selección anterior."""
        state = hud.st(context.region)
        press = (event.mouse_region_x, event.mouse_region_y)
        # Se vuelve a identificar la zona justo al pulsar, en lugar de confiar en la selección del último movimiento del cursor.
        state.update(press=press, last=press, dragging=False,
                     press_hit=hud.pick(context, press), left_camera=False)
        return {'RUNNING_MODAL'}

    def modal(self, context, event, tweak):
        """Gestiona la interacción mientras el botón del ratón sigue activo. Según la zona seleccionada, permite girar, acercar, desplazar o activar una acción del cubo, y termina cuando se suelta el botón o se cancela la operación."""
        if event.type not in {'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'}:
            return {'RUNNING_MODAL'}
        state = hud.st(context.region)
        x, y = event.mouse_region_x, event.mouse_region_y
        last = state["last"]
        hit = state.get("press_hit")
        if hit:
            kind, val = hit
            if kind == "CELL":
                if (not state["dragging"]
                        and (Vector((x, y)) - Vector(state["press"])).length
                        > constants.DRAG_START_PX):
                    state["dragging"] = True
                if state["dragging"]:
                    if not state["left_camera"]:
                        actions.leave_camera(context)
                        state["left_camera"] = True
                    actions.rotate_drag(context, x - last[0], y - last[1])
            elif kind == "BUTTON" and val == "ZOOM":
                if (x, y) != tuple(last):
                    state["dragging"] = True
                    actions.zoom_drag(context, y - last[1])
            elif kind == "BUTTON" and val == "PAN":
                if (x, y) != tuple(last):
                    state["dragging"] = True
                    actions.pan_drag(context, last, (x, y))
        state["last"] = (x, y)
        return {'RUNNING_MODAL'}

    def exit(self, context, cancel):
        """Finaliza la interacción con el gizmo y limpia el estado temporal. Si el usuario soltó el ratón fuera de la zona válida, descarta la acción como un clic abandonado."""
        state = hud.st(context.region)
        if cancel or state.get("dragging"):
            return
        hit = state.get("press_hit")
        if not hit:
            return
        # Si se suelta el botón fuera de la zona, se considera que el clic fue abandonado y no se ejecuta la acción.
        if hud.pick(context, state.get("last", state["press"])) != hit:
            return
        kind, val = hit
        s = getattr(context.window_manager, constants.PROP)
        if kind == "CELL":
            q = cube_math.rotation_from_dir(val)
            bpy.ops.viewcube_nav.set_view('INVOKE_DEFAULT', rotation=q,
                                          frame=True)
        elif kind == "ARROW":
            q = actions.arrow_rotation(actions.current_rotation(context), val,
                                       s.step_angle)
            bpy.ops.viewcube_nav.set_view('INVOKE_DEFAULT', rotation=tuple(q),
                                          frame=False)
        elif kind == "BUTTON":
            if val == "HOME":
                q = cube_math.rotation_from_dir(constants.HOME_DIRECTION)
                bpy.ops.viewcube_nav.set_view('INVOKE_DEFAULT', rotation=q,
                                              frame=True)
            elif val == "CAMERA":
                actions.toggle_camera(context)
            elif val == "PROJECTION":
                actions.toggle_projection(context)
        actions.redraw(context)


class VC_GGT_nav(bpy.types.GizmoGroup):
    """Grupo de gizmos que instala el cubo de navegación en las vistas 3D compatibles. Controla cuándo debe aparecer y crea el gizmo que recibe los eventos del usuario."""
    bl_idname = "VIEW3D_GGT_viewcube_nav"
    bl_label = "Orbit Gizmo Cube"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        """Comprueba si el contexto actual corresponde a una vista 3D en la que se puede mostrar el cubo. Blender utiliza esta comprobación antes de activar el grupo."""
        s = getattr(context.window_manager, constants.PROP, None)
        return bool(s and s.enabled and context.region_data)

    def setup(self, context):
        """Crea e inicializa el gizmo principal dentro del grupo. Aquí se configura el elemento que recibirá los clics y arrastres del usuario."""
        self.cube = self.gizmos.new(VC_GT_cube.bl_idname)


classes = (VC_GT_cube, VC_GGT_nav)
