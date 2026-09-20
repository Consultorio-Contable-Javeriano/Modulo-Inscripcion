"""Catálogos y divisiones administrativas por ciudad.

El formulario usa "localidad" en Bogotá y Barranquilla, y "comuna" en Medellín, Tunja,
Cali y Soacha. En las demás ciudades el campo no se muestra.
"""

import unicodedata

LOCALIDAD = 'Localidad'
COMUNA = 'Comuna'

# Las claves están normalizadas (minúsculas, sin tildes ni puntos). Incluimos las variantes
# de escritura más comunes porque hoy "Ciudad" es un campo de texto libre; el día que sea
# una lista desplegable esto se puede simplificar.
ENTITIES = [
    'Parroquia de Villa Javier',
    'Colegio Arborizadora Alta IED',
    'Camara de Comercio de Armenia y el Quindio',
    'Colegio Nuestra Señora del Pilar Sur',
    'COLEGIO T.A.A.C. SAN GREGORIO HERNANDEZ',
    'Colegio Mayor de San Bartolomé',
    'Colegio El Ensueño IED',
    'Fundación Domus',
    'Vidas Móviles',
    'Banco de Alimentos',
    'Fundación Alianza Social Educativa',
    'Fuerza Verde Colombia - FFMM',
    'Opción Legal',
    'Colegios de la Compañía de Jesus (Federación Asofamilias Jesuitas)',
    'Servicios de Alimentación - Pontificia Universidad Javeriana',
    'Opción 17',
    'Juan Bosco Obrero Proyecto Zasca',
    'Colegio General Santander',
    'Colegio Darío Echandia IED',
    'Liceo Femenino de Cundinamarca Mercedes Nariño IED',
    'Colegio Cafam',
    'Colegio San Bernardo de la Salle',
    'Colegio Ave María',
    'Colegio de Nuestra Señora de la Sabiduría',
    'Fundación Matheu\'s',
    'CDJ Nacho Sanchez',
    'Empleados - Pontificia Universidad Javeriana',
    'Programa Paz Ambiente y Territorio',
    'Semillas de Transformación. (P.O.R . EJER):.',
    'Colegio San Juan de Dios',
    'Grupo Darbel BIC SAS',
    'Colegio Salesiano Juan del Rizo',
    'Colegio Bolivariano y GAE',
    'NEGOCIOS VERDES CAR.',
    'Cruz Roja Colombiana Seccional Cundinamarca y Bogotá',
    'Colegio Antonio Villavicencio - Institución Educativa Distrital',
    'ANASERTEC',
    'La Macarena (Meta)',
    'Campoguaviare',
    'Asmusepaz',
    'Red Juvenil Ignaciana',
    'ASOSANTALUISA',
    'ASOIGNACIANA',
    'ASOCLAVERIANA',
    'ASOBARTOLINA',
    'ASOBERCHMANS',
    'ASOSANJOSE',
    'ASOSANLUIS',
    'ASOMAYOR',
    'ASOJAVERIANA',
    'Otros',
]

CITIES = [
    'Leticia', 'Medellín', 'Arauca', 'Barranquilla', 'Bogotá D.C', 'Cartagena de Indias',
    'Tunja', 'Manizales', 'Florencia', 'Yopal', 'Popayán', 'Valledupar', 'Quibdó',
    'Montería', 'Inírida', 'San José del Guaviare', 'Neiva', 'Riohacha', 'Santa Marta',
    'Villavicencio', 'Pasto', 'San José de Cúcuta', 'Mocoa', 'Armenia', 'Pereira',
    'San Andrés', 'Bucaramanga', 'Sincelejo', 'La Macarena - Meta', 'Ibagué', 'Cali',
    'Mitú', 'Puerto Carreño', 'Soacha', 'Otras',
]

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

DIVISION_OPTIONS = {
    LOCALIDAD: {
        'bogota': [
            'Usaquén Chapinero',
            'Santa Fe San Cristóbal',
            'Usme Tunjuelito',
            'Bosa Kennedy',
            'Fontibón Engativá',
            'Suba Barrios Unidos',
            'Teusaquillo Los Mártires',
            'Antonio Nariño Puente Aranda',
            'La Candelaria Rafael Uribe Uribe',
            'Ciudad Bolívar Sumapaz',
            'Suba',
            'Kennedy',
            'Bosa',
            'Engativá',
            'Usaquén',
            'Chapinero',
            'Fontibón',
            'Teusaquillo',
            'San Cristóbal',
            'Usme',
            'Tunjuelito',
            'Barrios Unidos',
            'Los Mártires',
            'Antonio Nariño',
            'Puente Aranda',
            'La Candelaria',
            'Rafael Uribe Uribe',
            'Ciudad Bolívar',
            'Sumapaz',
            'Santa Fe',
        ],
        'barranquilla': [
            'Riomar Barranquilla',
            'Norte-Centro Barranquilla',
            'Histórico Barranquilla',
            'Suroccidente Barranquilla',
            'Metropolitana Barranquilla',
            'Suroriente Barranquilla',
        ],
    },
    COMUNA: {
        'medellin': [
            'Comuna 1 - Popular Medellín',
            'Comuna 2 - Santa Cruz Medellín',
            'Comuna 3 - Manrique Medellín',
            'Comuna 4 - Aranjuez Medellín',
            'Comuna 5 - Castilla Medellín',
            'Comuna 6 - Doce de octubre Medellín',
            'Comuna 7 - Robledo Medellín',
            'Comuna 8 - Villa Hermosa Medellín',
            'Comuna 9 - Buenos Aires Medellín',
            'Comuna 10 - La Candelaria Medellín',
            'Comuna 11 - Laureles—Estadio Medellín',
            'Comuna 12 - La América Medellín',
            'Comuna 13 - San Javier Medellín',
            'Comuna 14 - Poblado Medellín',
            'Comuna 15 - Guayabal Medellín',
            'Comuna 16 - Belén Medellín',
        ],
        'tunja': [
            'Comuna 1 Norte -Tunja',
            'Comuna 2 Noroccidental -Tunja',
            'Comuna 3 Nororiental -Tunja',
            'Comuna 4 Occidental -Tunja',
            'Comuna 5 Centro Histórico -Tunja',
            'Comuna 6 Suroccidental -Tunja',
            'Comuna 7 Oriental -Tunja',
            'Comuna 8 Suroriental -Tunja',
        ],
        'cali': [
            'Comuna 1 (Cali)',
            'Comuna 2 (Cali)',
            'Comuna 3 (Cali)',
            'Comuna 4 (Cali)',
            'Comuna 5 (Cali)',
            'Comuna 6 (Cali)',
            'Comuna 7 (Cali)',
            'Comuna 8 (Cali)',
            'Comuna 9 (Cali)',
            'Comuna 10 (Cali)',
            'Comuna 11 (Cali)',
            'Comuna 12 (Cali)',
            'Comuna 13 (Cali)',
            'Comuna 14 (Cali)',
            'Comuna 15 (Cali)',
            'Comuna 16 (Cali)',
            'Comuna 17 (Cali)',
            'Comuna 18 (Cali)',
            'Comuna 19 (Cali)',
            'Comuna 20 (Cali)',
            'Comuna 21 (Cali)',
            'Comuna 22 (Cali)',
        ],
        'soacha': [
            'Comuna 1 Compartir',
            'Comuna 2 Soacha Central',
            'Comuna 3 La Despensa',
            'Comuna 4 Cazucá',
            'Comuna 5 San Mateo',
            'Comuna 6 San Humberto',
            'Otras',
        ],
    }
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
        return 'En tu ciudad la zona se llama "localidad". Elige de la lista.'
    if label == COMUNA:
        return 'En tu ciudad la zona se llama "comuna" (por ejemplo: Comuna 13).'
        return 'En tu ciudad la zona se llama "comuna". Elige de la lista.'
    return ''


def get_locality_options(city):
    """Retorna lista de opciones para localidad/comuna dada la ciudad."""
    norm = normalize_city(city)
    label = division_label(city)
    if not label:
        return []
    
    options_dict = DIVISION_OPTIONS.get(label, {})
    if 'bogota' in norm:
        return options_dict.get('bogota', [])
    if 'barranquilla' in norm:
        return options_dict.get('barranquilla', [])
    if 'medellin' in norm:
        return options_dict.get('medellin', [])
    if 'tunja' in norm:
        return options_dict.get('tunja', [])
    if 'cali' in norm:
        return options_dict.get('cali', [])
    if 'soacha' in norm:
        return options_dict.get('soacha', [])

    return []
