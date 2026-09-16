"""Divisiones administrativas por ciudad.

El documento de levantamiento pide que el formulario no obligue al usuario a adivinar qué
término administrativo usa su ciudad: en Bogotá y Barranquilla se dice "localidad", en
Medellín, Tunja, Cali y Soacha se dice "comuna".

En las ciudades que no usan ninguno de los dos, el campo no se muestra: el formulario ya
tiene "Barrio", y repetirlo como "Barrio o vereda" solo confundiría a quien lo llena.
"""

import unicodedata

LOCALIDAD = 'Localidad'
COMUNA = 'Comuna'

# Las claves están normalizadas (minúsculas, sin tildes ni puntos). Incluimos las variantes
# de escritura más comunes porque hoy "Ciudad" es un campo de texto libre; el día que sea
# una lista desplegable esto se puede simplificar.
_CITY_DIVISIONS = {
    'bogota': LOCALIDAD,
    'bogota dc': LOCALIDAD,
    'bogota d c': LOCALIDAD,
    'santafe de bogota': LOCALIDAD,
    'barranquilla': LOCALIDAD,
    'medellin': COMUNA,
    'tunja': COMUNA,
    'cali': COMUNA,
    'santiago de cali': COMUNA,
    'soacha': COMUNA,
}


# Ciudades que ofrece el buscador del formulario: las capitales de departamento mas los
# municipios que el documento de levantamiento menciona por nombre. NO es una lista cerrada:
# el campo sigue aceptando cualquier municipio escrito a mano, para no dejar por fuera a
# quien vive en uno pequeno.
CITIES = [
    'Arauca', 'Armenia', 'Barranquilla', 'Bogotá', 'Bucaramanga', 'Cali', 'Cartagena',
    'Cúcuta', 'Florencia', 'Ibagué', 'Inírida', 'Leticia', 'Manizales', 'Medellín',
    'Mitú', 'Mocoa', 'Montería', 'Neiva', 'Pasto', 'Pereira', 'Popayán', 'Puerto Carreño',
    'Quibdó', 'Riohacha', 'San Andrés', 'San José del Guaviare', 'Santa Marta', 'Sincelejo',
    'Soacha', 'Sogamoso', 'Tunja', 'Valledupar', 'Villavicencio', 'Yopal',
]


def normalize_city(city):
    """Minúsculas, sin tildes ni puntos, para comparar lo que el usuario escribió."""
    if not city:
        return ''
    sin_tildes = ''.join(
        c for c in unicodedata.normalize('NFD', str(city)) if unicodedata.category(c) != 'Mn'
    )
    return ' '.join(sin_tildes.replace('.', ' ').lower().split())


def division_label(city):
    """'Localidad', 'Comuna' o None si la ciudad no usa ninguna de las dos."""
    return _CITY_DIVISIONS.get(normalize_city(city))


def division_help_text(city):
    label = division_label(city)
    if label == LOCALIDAD:
        return 'En tu ciudad la zona se llama "localidad" (por ejemplo: Suba, Kennedy, Chapinero).'
    if label == COMUNA:
        return 'En tu ciudad la zona se llama "comuna" (por ejemplo: Comuna 13).'
    return ''
