"""Funciones que realizan los movimientos y cambios de la vista 3D. Aquí se concentra la lógica para girar, acercar, desplazar, encuadrar y cambiar la proyección o la vista de cámara."""

from __future__ import annotations

import math

import bpy
from bpy_extras import view3d_utils
from mathutils import Quaternion


def current_rotation(context):
    """Devuelve la orientación actual de la vista 3D. Si la vista está mirando a través de una cámara, utiliza la orientación de esa cámara para que los cambios de vista partan de la posición correcta."""
    rv3d = context.region_data
    if rv3d.view_perspective == 'CAMERA':
        cam = context.space_data.camera
        if cam:
            return cam.matrix_world.to_quaternion()
    return rv3d.view_rotation.copy()


def redraw(context):
    """Solicita a Blender que vuelva a dibujar la vista 3D. Se utiliza después de modificar la orientación, la posición o la distancia de la vista para que los cambios se reflejen inmediatamente."""
    if context.area:
        context.area.tag_redraw()
    if context.region:
        context.region.tag_redraw()


def status(message):
    """Muestra un mensaje breve en la barra de estado de Blender y programa su eliminación unos segundos después, evitando que el aviso permanezca visible indefinidamente."""
    try:
        bpy.context.workspace.status_text_set(message)

        def _clear():
            """Limpia el mensaje temporal de la barra de estado. Esta función interna se ejecuta cuando termina el tiempo que se asignó al aviso."""
            try:
                bpy.context.workspace.status_text_set(None)
            except Exception:  
                pass
            return None
        bpy.app.timers.register(_clear, first_interval=3.0)
    except Exception:  
        pass


##------ CÁMARA Y TIPO DE PROYECCIÓN ------##
def leave_camera(context):
    """Sale de la vista de cámara y recupera una vista libre del espacio 3D. Conserva como referencia la posición y la orientación de la cámara para que la transición no produzca un salto inesperado."""
    rv3d = context.region_data
    if rv3d is None or rv3d.view_perspective != 'CAMERA':
        return
    view = context.preferences.view
    old = view.smooth_view
    try:
        view.smooth_view = 0
        bpy.ops.view3d.view_camera()
    except RuntimeError:
        rv3d.view_perspective = 'PERSP'
    finally:
        view.smooth_view = old


def toggle_camera(context):
    """Alterna entre la vista de cámara y la vista libre. Cuando entra en cámara, Blender muestra la cámara activa; cuando sale, vuelve a la navegación normal del usuario."""
    try:
        bpy.ops.view3d.view_camera()
    except RuntimeError:
        status("Orbit Gizmo Cube: the scene has no camera")


def toggle_projection(context):
    """Cambia el tipo de proyección de la vista entre perspectiva y ortográfica. Si se está mirando a través de una cámara, respeta la proyección que controla esa cámara."""
    rv3d = context.region_data
    if rv3d is None:
        return
    if rv3d.view_perspective == 'CAMERA':
        status("Orbit Gizmo Cube: the camera decides the projection")
        return
    rv3d.view_perspective = 'ORTHO' if rv3d.view_perspective == 'PERSP' else 'PERSP'
    redraw(context)


##------ ENCUADRE DE LA ESCENA ------##
def compute_frame(context, rot):
    """Calcula la posición y la distancia necesarias para encuadrar los objetos seleccionados desde la orientación indicada. Tiene en cuenta sus límites visibles y el margen configurado para que no queden demasiado pegados a los bordes."""
    rv3d = context.region_data
    if context.mode == 'OBJECT' and not context.selected_objects:
        return None
    saved = (rv3d.view_rotation.copy(), rv3d.view_location.copy(),
             rv3d.view_distance)
    view = context.preferences.view
    old_smooth = view.smooth_view
    result = None
    try:
        view.smooth_view = 0
        rv3d.view_rotation = rot
        r = bpy.ops.view3d.view_selected(use_all_regions=False)
        if 'FINISHED' in r:
            result = (rv3d.view_location.copy(), rv3d.view_distance)
    except RuntimeError:
        pass
    finally:
        view.smooth_view = old_smooth
        rv3d.view_rotation, rv3d.view_location, rv3d.view_distance = saved
    return result


##------ ACCIONES CON EL ARRASTRE DEL RATÓN ------##
def arrow_rotation(q, name, step):
    """Calcula la nueva orientación de la vista al pulsar una de las flechas de giro. Usa el nombre de la dirección y el ángulo indicado para construir la rotación correspondiente."""
    if name == 'LEFT':
        return Quaternion((0, 0, 1), step) @ q
    if name == 'RIGHT':
        return Quaternion((0, 0, 1), -step) @ q
    if name == 'UP':
        return q @ Quaternion((1, 0, 0), step)
    if name == 'DOWN':
        return q @ Quaternion((1, 0, 0), -step)
    if name == 'ROLL_R':
        return q @ Quaternion((0, 0, 1), step)
    return q @ Quaternion((0, 0, 1), -step)          # ROLL_L


def rotate_drag(context, dx, dy, k=0.012):
    """Gira la vista 3D según el desplazamiento horizontal y vertical del ratón. La cantidad de movimiento se convierte en un cambio de orientación suave y proporcional al arrastre."""
    rv3d = context.region_data
    q = rv3d.view_rotation
    q = Quaternion((0, 0, 1), -dx * k) @ q
    q = q @ Quaternion((1, 0, 0), dy * k)
    rv3d.view_rotation = q.normalized()
    redraw(context)


def zoom_drag(context, dy):
    """Acerca o aleja la vista según el movimiento vertical del ratón. Arrastrar hacia arriba acerca la escena y arrastrar hacia abajo la aleja."""
    rv3d = context.region_data
    if rv3d.view_perspective == 'CAMERA':
        rv3d.view_camera_zoom = max(-30.0, min(600.0,
                                               rv3d.view_camera_zoom + dy * 0.3))
    else:
        rv3d.view_distance = max(1e-5, min(1e7,
                                           rv3d.view_distance * math.exp(-dy * 0.01)))
    redraw(context)


def pan_drag(context, p0, p1):
    """Desplaza la vista para que el punto de la escena situado bajo la posición inicial del ratón siga el movimiento hasta la posición final. Así se puede mover el encuadre sin cambiar la orientación."""
    region, rv3d = context.region, context.region_data
    if rv3d.view_perspective == 'CAMERA':
        # Se utiliza el mismo cálculo que Blender aplica al desplazar la vista de cámara.
        zoomfac = ((math.sqrt(2.0) + rv3d.view_camera_zoom / 50.0) ** 2) / 4.0 * 2.0
        off = rv3d.view_camera_offset
        rv3d.view_camera_offset = (
            off[0] - (p1[0] - p0[0]) / (region.width * zoomfac),
            off[1] - (p1[1] - p0[1]) / (region.height * zoomfac))
    else:
        depth = rv3d.view_location
        a = view3d_utils.region_2d_to_location_3d(region, rv3d, p0, depth)
        b = view3d_utils.region_2d_to_location_3d(region, rv3d, p1, depth)
        rv3d.view_location = rv3d.view_location + (a - b)
    redraw(context)
