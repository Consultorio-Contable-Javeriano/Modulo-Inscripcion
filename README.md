# Consultorio Contable Javeriano — Módulo de Inscripción

Aplicación Django + HTMX para que usuarios que necesitan asesoría en temas económicos y tributarios se
inscriban a los módulos del Consultorio Contable Javeriano.

## Stack

- Django 5.x (`django>=4.2,<5.2`)
- HTMX 1.9 (vía CDN) + [django-htmx](https://django-htmx.readthedocs.io/) para detectar peticiones parciales
- Tailwind CSS (vía CDN)
- SQLite en desarrollo

## Instalación (primera vez)

```bash
# 1. Crear y activar el entorno virtual
python -m venv venv
venv\Scripts\activate          # Windows (PowerShell o cmd)
# source venv/bin/activate     # macOS/Linux

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno (opcional en desarrollo: sin .env, arranca con
#    valores por defecto seguros para local)
copy .env.example .env         # Windows
# cp .env.example .env         # macOS/Linux

# 4. Aplicar migraciones y crear un usuario administrador
python manage.py migrate
python manage.py createsuperuser
```

Variables de entorno disponibles en `.env` (ver `.env.example`): `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`,
`DJANGO_ALLOWED_HOSTS`, `DJANGO_EMAIL_BACKEND`, `DJANGO_DEFAULT_FROM_EMAIL`, `DJANGO_SECURE_SSL_REDIRECT`,
`DJANGO_LOGIN_MAX_FAILED_ATTEMPTS`, `DJANGO_LOGIN_LOCKOUT_SECONDS`, `DJANGO_SESSION_COOKIE_AGE`.

## Levantar el servidor

Cada vez que quieras correr el proyecto (después de la instalación inicial):

```bash
venv\Scripts\activate          # Windows — activa el entorno virtual si no está activo
# source venv/bin/activate     # macOS/Linux

python manage.py runserver
```

Deja la terminal abierta mientras trabajas: el servidor queda corriendo ahí. Con `Ctrl+C` lo detienes.

Con la configuración por defecto, la aplicación queda disponible en:

- **App**: http://127.0.0.1:8000/usuarios/login/
- **Admin de Django**: http://127.0.0.1:8000/admin/ (usa el usuario creado con `createsuperuser`)

Si necesitas exponerlo en otro puerto o en la red local: `python manage.py runserver 0.0.0.0:8000`.

## Correr los tests

```bash
python manage.py test
```

33 tests cubren autenticación (login, logout, registro, bloqueo por intentos fallidos, expiración de
sesión), perfil de usuario y todo el flujo de inscripción.

## Estructura

- `users/` — autenticación, perfil de usuario (`UserProfile`) y valores guardados (`UserSavedDefaults`).
- `enrollments/` — módulos (`Module`), inscripciones (`Enrollment`), portal del usuario y panel de staff.

---

## Cambios de esta rama (`Cambios-Tom`) respecto a `main`

Este trabajo partió de un bug puntual (`portal_home` no existía como URL, por lo que el login exitoso
crasheaba con `NoReverseMatch`) y se amplió para completar las partes del módulo de inscripciones,
autenticación e infraestructura que faltaban. Detalle completo, sección por sección:

### 1. Fix original: `portal_home`

- `enrollments/views.py`: nueva vista `portal_home` (con `@login_required`) que lista los módulos activos.
- `enrollments/urls.py` (archivo nuevo): registra `path('', views.portal_home, name='portal_home')`.
- `config/urls.py`: agrega `path('portal/', include('enrollments.urls'))`, que es la URL que el
  `redirect('portal_home')` de `users/views.py` esperaba y que antes no existía.
- `templates/enrollments/portal_home.html` (archivo nuevo): plantilla que antes tampoco existía.

### 2. Estética Javeriana

- `templates/base.html`: se agregó un tema de Tailwind inline (`tailwind.config`) con la paleta navy/azul/
  dorado (`#173268` / `#195cab` / `#dbbe16`) extraída visualmente de
  [javeriana.edu.co/consultorio-contable](https://www.javeriana.edu.co/consultorio-contable); header con
  navegación (Portal, Mis inscripciones, Panel administrativo, Mi perfil, Cerrar sesión) visible solo si
  hay sesión iniciada; bloque de `messages` de Django con colores por tipo (éxito/error/info); footer.
- `templates/users/login.html`, `templates/users/components/login_form.html`: rediseño con la misma
  paleta, tarjeta con borde superior dorado, enlaces a "Crear una cuenta" y "¿Olvidaste tu contraseña?",
  soporte para el campo oculto `next` (ver sección 5).
- `templates/users/signup.html`, `templates/users/profile_form.html` (archivos nuevos): mismo lenguaje
  visual.
- `templates/enrollments/portal_home.html`, `enroll_form.html`, `my_enrollments.html`,
  `cancel_confirm.html`, `staff_dashboard.html` (todos nuevos): mismo lenguaje visual, con tarjetas
  blancas sobre fondo gris claro y bloques navy/dorado para encabezados de sección.
- `templates/users/password_reset*.html` (4 archivos nuevos): mismo lenguaje visual para todo el flujo
  de recuperación de contraseña.

### 3. Labels en español

- `enrollments/models.py`: se agregó `verbose_name` en español a **todos** los campos de `Module` y
  `Enrollment` (`Nombre`, `Semestre`, `Modalidad`, `Inicio de inscripciones`, `Fin de inscripciones`,
  `Fecha de inicio/fin de clases`, `Horario`, `Activo`, `Usuario`, `Módulo`, `Fecha de inscripción`,
  `Autorización de tratamiento de datos`, `Entidad`, `Modalidad elegida`, `Ciudad`, `Barrio`,
  `Compromiso de asistencia`), más `Meta.verbose_name`/`verbose_name_plural` ("Módulo"/"Módulos",
  "Inscripción"/"Inscripciones").
- `users/models.py`: mismo tratamiento en `CustomUser` (`Correo electrónico`), `UserProfile` (`Nombre
  completo`, `Tipo de documento`, `Número de documento`, `Fecha de nacimiento`, `Género`, `Teléfono`,
  `Nivel educativo`, `Tiene negocio propio`) y `UserSavedDefaults` (`Última entidad`, `Última ciudad`,
  `Último barrio`), más sus `Meta.verbose_name`/`verbose_name_plural`.
- Como los `ModelForm` y el admin de Django derivan sus etiquetas del modelo, esto corrigió de raíz las
  etiquetas que antes aparecían en inglés (`Entity`, `Chosen modality`, etc.) sin duplicar `labels=` en
  cada formulario.
- Migraciones generadas: `enrollments/migrations/0003_alter_enrollment_options_alter_module_options_and_more.py`
  y `users/migrations/0002_alter_customuser_options_alter_userprofile_options_and_more.py`; son cambios
  de metadatos (más el `UniqueConstraint` de la sección 4), no alteran datos existentes.

### 4. Módulo de inscripciones — funcionalidad que faltaba

- **Coherencia de modalidad**: `enrollments/models.py` agrega `Enrollment.MODALITY_CHOICES`
  (`Presencial`/`Virtual`) y el método `Module.allowed_modalities()`. `enrollments/forms.py`
  (`EnrollmentForm.__init__`) restringe las opciones de `chosen_modality` a las permitidas por el módulo,
  y `clean_chosen_modality()` lo revalida en el servidor; así no se puede elegir "Virtual" en un módulo
  100% presencial.
- **Perfil obligatorio**: `enrollments/views.py: enroll()` exige `hasattr(request.user, 'profile')` antes
  de mostrar el formulario de inscripción; si falta, redirige a `complete_profile` con un mensaje. La
  vista/plantilla de perfil (`users/views.py: profile_view`, `templates/users/profile_form.html`) es
  nueva (ver sección 5).
- **Autocompletado ("Lazy Loading")**: `UserSavedDefaults` existía en el modelo pero no se usaba en
  ningún lado; ahora `enroll()` la lee para precargar `entity`/`city`/`neighborhood` como `initial=` del
  formulario, y hace `update_or_create` sobre ella después de cada inscripción exitosa.
- **"Mis inscripciones"**: `enrollments/views.py: my_enrollments` y `cancel_enrollment` (nuevas), con
  `templates/enrollments/my_enrollments.html` y `cancel_confirm.html` (nuevas) y las rutas
  `mis-inscripciones/` y `mis-inscripciones/<id>/cancelar/` en `enrollments/urls.py`. `cancel_enrollment`
  verifica que la inscripción pertenezca al usuario (`get_object_or_404(..., user=request.user)`, 404 si
  no) y que el módulo siga con inscripciones abiertas antes de borrar el registro.
- **Panel de staff**: `enrollments/views.py: staff_dashboard` (nueva, ruta `administrar/`), fuera del
  admin de Django, protegida con `if not request.user.is_staff: raise PermissionDenied(...)`. Lista cada
  módulo con su conteo de inscritos y el detalle (usuario, correo, modalidad, entidad, ciudad) vía
  `templates/enrollments/staff_dashboard.html` (nueva).
- **Robustez**: `enrollments/models.py: Enrollment.Meta.constraints` agrega
  `UniqueConstraint(fields=['user', 'module'], name='unique_enrollment_per_user_module')`, y
  `enroll()` captura `IntegrityError` por si dos peticiones concurrentes pasan la validación de vista a
  la vez (antes la única protección era una consulta previa en la vista, sin garantía a nivel de base de
  datos).

### 5. Autenticación y cuenta — lo que no existía

- **Registro**: `users/forms.py: SignupForm` (nuevo, basado en `UserCreationForm`), `users/views.py:
  signup_view` (nueva) y ruta `usuarios/registro/`; antes solo se podían crear usuarios desde el admin.
  Al registrarse, inicia sesión automáticamente y redirige a completar el perfil.
- **Perfil de usuario**: `users/forms.py: UserProfileForm` (nuevo) y `users/views.py: profile_view`
  (nueva) en la ruta `usuarios/perfil/`; crea o edita el `UserProfile` del usuario autenticado.
- **Logout**: `users/urls.py` agrega `path('logout/', auth_views.LogoutView.as_view(), name='logout')`
  (vista estándar de Django); botón visible en el header de `base.html` cuando hay sesión iniciada.
- **Recuperación de contraseña**: `users/urls.py` agrega las 4 rutas de
  `django.contrib.auth.views` (`PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`,
  `PasswordResetCompleteView`) con templates propios (`templates/users/password_reset*.html`, 4 archivos
  nuevos) y correo en texto plano (`password_reset_email.txt`, `password_reset_subject.txt`, nuevos); en
  desarrollo el correo se imprime en consola (ver sección 6).
- **Parámetro `next`**: `users/views.py: login_view` ahora calcula `_safe_next_url()` (nueva función,
  usa `url_has_allowed_host_and_scheme` para evitar open redirects) y respeta `?next=`, tanto en la
  respuesta normal como en el `HX-Redirect` de HTMX. `templates/users/components/login_form.html` agrega
  un campo oculto `next` para que sobreviva al POST.
- **Configuración asociada**: `config/settings.py` agrega `LOGIN_URL = 'login'`,
  `LOGIN_REDIRECT_URL = 'portal_home'`, `LOGOUT_REDIRECT_URL = 'login'`.

### 6. Infraestructura y calidad

- **Configuración por entorno**: `config/settings.py` agrega un loader propio de `.env` (función
  `_load_dotenv`, sin dependencias nuevas) y lee `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `EMAIL_BACKEND` y
  `DEFAULT_FROM_EMAIL` desde variables de entorno con valores por defecto seguros para desarrollo.
  `.env.example` (archivo nuevo) documenta todas las variables. Antes `SECRET_KEY` estaba hardcodeada y
  `DEBUG=True` fijo en el código.
- **Bug de configuración corregido**: el proyecto tenía un setting `MAILERS` que Django nunca lee (el
  nombre correcto es `EMAIL_BACKEND`), por lo que el envío de correo en consola nunca estaba realmente
  configurado. Se reemplazó por `EMAIL_BACKEND` real (`django.core.mail.backends.console.EmailBackend`
  por defecto en desarrollo).
- **`django-htmx` sin usar**: la dependencia estaba declarada en `requirements.txt` e instalada, pero su
  middleware nunca se registraba y las vistas comprobaban `request.headers.get('HX-Request')` a mano.
  `config/settings.py: MIDDLEWARE` agrega `django_htmx.middleware.HtmxMiddleware`, y
  `users/views.py: login_view` se migró a usar `request.htmx` de forma idiomática.
- **Seguridad en producción**: `config/settings.py` agrega un bloque `if not DEBUG:` que activa
  `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS` (1 semana),
  `SECURE_HSTS_INCLUDE_SUBDOMAINS` y `SECURE_HSTS_PRELOAD`; en desarrollo (`DEBUG=True`) quedan
  desactivados para no romper HTTP local. Verificado con `manage.py check --deploy`.
- **Localización**: `config/settings.py` cambia `LANGUAGE_CODE` de `en-us` a `es-co` y `TIME_ZONE` de
  `UTC` a `America/Bogota`, coherente con una app en español para una universidad colombiana (afecta
  formatos de fecha, el idioma del admin de Django y la interpretación de
  `enrollment_start`/`enrollment_end`).
- **Elecciones controladas en los modelos**: además de los `choices` de modalidad (sección 4),
  `users/models.py: UserProfile` agrega `ID_TYPE_CHOICES` (Cédula de ciudadanía/extranjería, Tarjeta de
  identidad, Pasaporte) y `GENDER_CHOICES` (Femenino/Masculino/Otro/Prefiero no decirlo), reemplazando
  los antiguos `CharField` de texto libre para `id_type` y `gender`.
- **Tests**: `enrollments/tests.py` pasó de 7 a 14 tests (perfil obligatorio, coherencia de modalidad,
  autocompletado con `UserSavedDefaults`, aislamiento entre usuarios en "Mis inscripciones", cancelación,
  panel de staff con y sin permisos) y `users/tests.py` pasó de 0 a 10 tests (registro y sus validaciones,
  login, login por HTMX, credenciales inválidas, logout, creación/edición de perfil) — 24 tests tras esta
sección; ver sección 7 para los 9 restantes.

### 7. Seguridad del inicio de sesión y de la sesión (requisitos del documento de login)

- **Bloqueo tras 5 intentos fallidos**: `users/security.py` (archivo nuevo) lleva la cuenta de intentos
  fallidos en la caché de Django y bloquea la cuenta durante 15 minutos al llegar al límite;
  `users/views.py: login_view` lo consulta *antes* de autenticar, así que mientras dure el bloqueo ni
  siquiera una contraseña correcta abre sesión. Se implementó a mano en vez de con `django-axes` para no
  agregar dependencias: son ~90 líneas y `requirements.txt` sigue con dos paquetes.
  - El conteo va por **correo escrito en el formulario**, exista o no esa cuenta, para no revelar qué
    correos están registrados; el correo se guarda hasheado (SHA-256) en la caché.
  - A falta de 2 intentos o menos, el formulario avisa cuántos quedan
    (`security.WARN_WHEN_REMAINING`); avisar desde el primer error sería ruido para un simple dedazo.
  - Límite y duración configurables vía `DJANGO_LOGIN_MAX_FAILED_ATTEMPTS` y
    `DJANGO_LOGIN_LOCKOUT_SECONDS` (`config/settings.py`, documentadas en `.env.example`).
  - `config/settings.py` declara `CACHES` explícitamente (`LocMemCache`). **Ojo en despliegue**: al ser
    memoria por proceso, con varios workers cada uno llevaría su propio conteo; en producción hay que
    apuntar la caché a Redis/Memcached o a la caché en base de datos para que el bloqueo sea real.
  - Tratamiento del riesgo conocido: al ser un bloqueo *por cuenta*, un atacante puede dejar fuera a un
    usuario legítimo a propósito. Es lo que pide el documento; si molesta en la práctica, la variante
    habitual es combinar la clave con la IP de origen.
- **Cierre de sesión por inactividad**: `config/settings.py` agrega `SESSION_COOKIE_AGE` (30 minutos por
  defecto, configurable con `DJANGO_SESSION_COOKIE_AGE`) y `SESSION_SAVE_EVERY_REQUEST = True`, que
  renueva la cookie en cada petición para que el plazo cuente desde la última actividad y no sea una
  duración fija desde el login. Antes regía el default de Django: 2 semanas fijas.
  - Queda a criterio del equipo añadir también `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`; tiene sentido
    para los computadores compartidos del consultorio, pero el documento no lo pedía.
- **Tests**: `users/tests.py` suma `LoginLockoutTests` (7 tests: bloqueo al quinto fallo, contraseña
  correcta rechazada durante el bloqueo, reinicio del contador tras un login exitoso, aislamiento entre
  cuentas, aviso previo, aviso por HTMX, vencimiento del bloqueo) y `SessionExpirationSettingsTests`
  (2 tests) — **33 tests en total**.

---

## Cambios pendientes

Ítems generales fuera del alcance de esta rama:

- No hay un archivo de licencia ni CI configurado.
- `requirements.txt` fija rangos de versión (`>=`, `<`) en vez de versiones exactas; para despliegues
  reproducibles conviene generar un lockfile (`pip freeze` o `pip-tools`).
- El admin de Django sigue siendo el único lugar para dar de alta `Module`s; no hay UI para que el staff
  los cree/edite fuera del admin.

### Brechas frente a "Requerimientos para módulo de login" (tareas para Samuel y Tom)

El documento `Requerimientos para módulo de login.pdf` (levantamiento de requerimientos del módulo de
autenticación) es, en general, muy coherente con lo implementado: el modelo de datos (`UserProfile` /
`UserSavedDefaults` / `Module` / `Enrollment`), la estrategia de autocompletado ("Lazy Loading": no pedir
entidad/ubicación al registrarse, solo en la primera inscripción, y precargarla editable después) y el
"Plan de Acción con Samuel y Tom" (registro único → panel de control → inscripción a un clic) ya están
cubiertos. Quedan pendientes estos puntos explícitos del documento que no se implementaron en esta rama:

**Formulario intuitivo (usabilidad para usuarios con dificultad para insertar información):**
- **Campo dinámico Localidad/Comuna según ciudad**: el documento pide un tercer campo de ubicación
  condicional (Localidad si es Bogotá/Barranquilla, Comuna si es Medellín/Tunja/Cali/Soacha, Barrio/Vereda
  en el resto). Hoy `Enrollment`/`UserSavedDefaults` solo tienen `city` y `neighborhood`; falta ese tercer
  campo condicional pensado para que el usuario no tenga que adivinar qué término administrativo usar.
- **Entidad como lista desplegable con opción "Otra"**: el documento especifica una lista curada de
  entidades (fundaciones, colegios, parroquias, etc.) con una opción "Otra" de texto libre solo como
  fallback. Hoy `entity` es siempre un campo de texto libre, lo que es más difícil de usar para alguien
  con baja alfabetización digital que elegir de una lista.

**Modelo de datos incompleto:**
- **Correo electrónico alternativo (opcional)** en `UserProfile`: el documento lo pide explícitamente
  junto al correo principal; no existe ese campo hoy (`CustomUser.email` es el único correo almacenado).

**Nota (menor prioridad, no era un requisito firme):** el documento también exploró verificar
correo/teléfono una vez durante el registro, pero el propio stakeholder reconoció la barrera tecnológica
de los usuarios como razón para no exigirlo — queda a criterio del equipo si vale la pena implementarlo.
