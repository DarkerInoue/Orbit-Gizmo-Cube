"""Nombres, identificadores y valores compartidos por los distintos archivos del complemento. Mantenerlos aquí evita repetir cadenas y números en varias partes del código."""

# Aquí se guardan las propiedades: la apariencia del cubo pertenece a la sesión de Blender
# (WindowManager), mientras que las unidades y la cuadrícula se guardan dentro del archivo .blend (Scene).
PROP = "viewcube_nav"
UNITS_PROP = "viewcube_units"

# Orden de los botones de la barra situada debajo del cubo, de arriba hacia abajo.
# El último botón siempre permite cambiar entre perspectiva y ortográfica.
BUTTONS = ("HOME", "ZOOM", "PAN", "CAMERA", "PROJECTION")

# Estos botones se activan con un clic; ZOOM y PAN funcionan mientras se arrastra el ratón.
CLICK_BUTTONS = ("HOME", "CAMERA", "PROJECTION")
DRAG_BUTTONS = ("ZOOM", "PAN")

# Distancia mínima, en píxeles, que debe recorrer el cursor para considerar que se está arrastrando.
DRAG_START_PX = 6

# Dirección isométrica inicial (x, y, z) desde la que se observa la escena al usar la vista de inicio.
HOME_DIRECTION = (1.0, -1.0, 1.0)

TOOLTIPS = {
    "HOME": "Home view (isometric, frames the selection)",
    "ZOOM": "Zoom: drag up / down",
    "PAN": "Pan: drag",
    "CAMERA": "Camera view",
}
