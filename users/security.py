"""Control de intentos fallidos de inicio de sesión.

El documento de levantamiento de requerimientos pide bloquear la cuenta tras 5 intentos
fallidos. El conteo vive en la caché de Django (ver `CACHES` en `config/settings.py`) y no
en la base de datos: son datos efímeros, caducan solos y así no hacen falta migraciones ni
una tarea de limpieza.

El conteo se lleva por correo escrito en el formulario, exista o no una cuenta con ese
correo, para no revelar qué correos están registrados.
"""

import hashlib
import math
import time

from django.conf import settings
from django.core.cache import cache

_FAILURES_PREFIX = 'login-failures:'
_LOCKOUT_PREFIX = 'login-lockout:'

# A partir de cuántos intentos restantes le avisamos al usuario. Avisar desde el primer
# error sería ruido para un simple dedazo.
WARN_WHEN_REMAINING = 2


def _key(prefix, username):
    # Hasheamos el correo para no dejar datos personales en claro en la caché.
    digest = hashlib.sha256(username.strip().lower().encode('utf-8')).hexdigest()
    return f'{prefix}{digest}'


def register_failed_attempt(username):
    """Registra un intento fallido y devuelve cuántos intentos quedan antes del bloqueo."""
    if not username:
        return settings.LOGIN_MAX_FAILED_ATTEMPTS

    key = _key(_FAILURES_PREFIX, username)
    timeout = settings.LOGIN_LOCKOUT_SECONDS

    cache.add(key, 0, timeout)
    try:
        failures = cache.incr(key)
    except ValueError:
        # La clave caducó entre el add() y el incr(); contamos este intento como el primero.
        cache.set(key, 1, timeout)
        failures = 1

    remaining = max(settings.LOGIN_MAX_FAILED_ATTEMPTS - failures, 0)
    if remaining == 0:
        cache.set(_key(_LOCKOUT_PREFIX, username), time.time() + timeout, timeout)
        # Ya no necesitamos el contador: al vencer el bloqueo se empieza de cero.
        cache.delete(key)
    return remaining


def lockout_remaining_seconds(username):
    """Segundos que faltan para que se libere la cuenta (0 si no está bloqueada)."""
    if not username:
        return 0
    unlock_at = cache.get(_key(_LOCKOUT_PREFIX, username))
    if not unlock_at:
        return 0
    return max(int(unlock_at - time.time()), 0)


def reset_attempts(username):
    """Limpia el historial de intentos: se llama tras un inicio de sesión exitoso."""
    if not username:
        return
    cache.delete_many([_key(_FAILURES_PREFIX, username), _key(_LOCKOUT_PREFIX, username)])


def lockout_notice(seconds):
    """Mensaje de cuenta bloqueada, redondeado a minutos para que sea legible."""
    minutes = max(1, math.ceil(seconds / 60))
    unidad = 'minuto' if minutes == 1 else 'minutos'
    return (
        'Por seguridad bloqueamos temporalmente el acceso a esta cuenta tras '
        f'{settings.LOGIN_MAX_FAILED_ATTEMPTS} intentos fallidos. '
        f'Vuelve a intentarlo en {minutes} {unidad}, o restablece tu contraseña.'
    )


def remaining_attempts_notice(remaining):
    """Aviso de cuántos intentos le quedan al usuario antes del bloqueo."""
    unidad = 'intento' if remaining == 1 else 'intentos'
    return f'Te {"queda" if remaining == 1 else "quedan"} {remaining} {unidad} antes de que la cuenta se bloquee temporalmente.'
