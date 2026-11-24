"""Operaciones numéricas para trabajar con unidades de longitud. No depende directamente de Blender: contiene equivalencias, conversiones y formatos de valores."""

from __future__ import annotations

import math

# Identificador de Blender: (nombre visible, símbolo, equivalencia en metros, sistema al que pertenece).
UNITS = {
    'KILOMETERS': ("Kilometers", "km", 1000.0, 'METRIC'),
    'METERS': ("Meters", "m", 1.0, 'METRIC'),
    'CENTIMETERS': ("Centimeters", "cm", 0.01, 'METRIC'),
    'MILLIMETERS': ("Millimeters", "mm", 0.001, 'METRIC'),
    'MICROMETERS': ("Micrometers", "\u00b5m", 1e-6, 'METRIC'),
    'MILES': ("Miles", "mi", 1609.344, 'IMPERIAL'),
    'FEET': ("Feet", "ft", 0.3048, 'IMPERIAL'),
    'INCHES': ("Inches", "in", 0.0254, 'IMPERIAL'),
    'THOU': ("Thou", "thou", 0.0000254, 'IMPERIAL'),
}

# Unidad base utilizada para medir la cuadrícula de cada sistema. Cuando Blender usa
# la opción ADAPTIVE, este complemento toma esta unidad como referencia.
SYSTEM_BASE_UNIT = {'METRIC': 'METERS', 'IMPERIAL': 'FEET'}

# Unidades que aparecen como botones de cambio rápido, en el orden en que se muestran.
QUICK_UNITS = ('MILLIMETERS', 'CENTIMETERS', 'METERS', 'KILOMETERS',
               'INCHES', 'FEET', 'MILES')


def label(unit):
    """Devuelve el nombre legible de la unidad indicada, tal como se muestra en la interfaz."""
    return UNITS[unit][0]


def symbol(unit):
    """Devuelve la abreviatura o símbolo correspondiente a la unidad indicada, por ejemplo m, cm o ft."""
    return UNITS[unit][1]


def meters(unit):
    """Devuelve cuántos metros representa una unidad de la unidad indicada. Este factor sirve como base para realizar conversiones."""
    return UNITS[unit][2]


def system_of(unit):
    """Indica a qué sistema pertenece la unidad: métrico o imperial."""
    return UNITS[unit][3]


def to_meters(value, unit):
    """Convierte una cantidad expresada en la unidad indicada a su equivalente en metros."""
    return value * UNITS[unit][2]


def convert(value, src, dst):
    """Convierte un valor desde la unidad de origen hasta la unidad de destino utilizando los factores de equivalencia definidos en la tabla de unidades."""
    return value * UNITS[src][2] / UNITS[dst][2]


def effective_unit(system, length_unit):
    """Determina qué unidad utiliza realmente la escena para mostrar longitudes. Si Blender está en modo adaptable, utiliza aquí la unidad base del sistema correspondiente."""
    if system not in SYSTEM_BASE_UNIT:
        return None
    if length_unit in UNITS and UNITS[length_unit][3] == system:
        return length_unit
    return SYSTEM_BASE_UNIT[system]


def grid_scale_for(step, unit, system):
    """Calcula el valor que debe asignarse a la escala de cuadrícula de Blender para que cada celda represente el tamaño solicitado en la unidad elegida. Sin sistema de unidades, conserva el tamaño en unidades de Blender."""
    if system not in SYSTEM_BASE_UNIT or unit is None:
        return step
    return to_meters(step, unit) / UNITS[SYSTEM_BASE_UNIT[system]][2]


def unit_scale_for(unit):
    """Devuelve el factor de escala que hace que una unidad de Blender represente exactamente una unidad de la unidad seleccionada."""
    return UNITS[unit][2]


def native_factor(unit, scale_length):
    """Devuelve cuántas unidades de Blender mide 1 unidad mostrada. Sirve para crear objetos con su tamaño nativo: un cubo de 2 mm mide 2 * native_factor('MILLIMETERS', escala) unidades de Blender. Sin sistema de unidades devuelve 1."""
    if unit is None or unit not in UNITS:
        return 1.0
    return UNITS[unit][2] / (scale_length or 1.0)


def fmt(value):
    """Formatea un número para mostrarlo de manera clara: conserva una precisión útil, elimina ceros innecesarios y evita la notación científica en cantidades habituales."""
    if value == 0:
        return "0"
    mag = abs(value)
    if mag >= 1e12 or mag < 1e-9:
        return "%.6g" % value
    text = "%.7g" % value
    if "e" in text:
        decimals = min(15, 6 - int(math.floor(math.log10(mag))))
        text = ("%." + str(decimals) + "f") % value
        text = text.rstrip("0").rstrip(".")
    return text


def all_conversions(value, src):
    """Genera una lista con el valor indicado convertido a cada unidad disponible. Cada elemento incluye el identificador, nombre, símbolo y resultado de la conversión."""
    return [(u, UNITS[u][0], UNITS[u][1], convert(value, src, u))
            for u in UNITS]


def describe_grid(step, unit, subdivisions, system):
    """Prepara dos textos para mostrar el tamaño de una celda y el tamaño de la línea más fina de la cuadrícula, teniendo en cuenta las subdivisiones y el sistema de unidades."""
    if system not in SYSTEM_BASE_UNIT or unit is None:
        return fmt(step) + " BU", fmt(step / max(subdivisions, 1)) + " BU"
    sym = UNITS[unit][1]
    return (fmt(step) + " " + sym,
            fmt(step / max(subdivisions, 1)) + " " + sym)
