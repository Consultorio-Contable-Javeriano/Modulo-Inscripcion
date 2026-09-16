from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from . import security
from .models import CustomUser, UserProfile


class SignupTests(TestCase):
    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(reverse('signup'), {
            'email': 'nuevo@example.com',
            'password1': 'contrasena-segura-123',
            'password2': 'contrasena-segura-123',
        }, follow=True)

        self.assertRedirects(response, reverse('complete_profile'))
        self.assertTrue(CustomUser.objects.filter(email='nuevo@example.com').exists())
        self.assertTrue(response.context['user'].is_authenticated)

    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(reverse('signup'), {
            'email': 'nuevo@example.com',
            'password1': 'contrasena-segura-123',
            'password2': 'otra-contrasena-456',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(CustomUser.objects.filter(email='nuevo@example.com').exists())

    def test_signup_rejects_duplicate_email(self):
        CustomUser.objects.create_user(email='existente@example.com', password='clave-segura123')
        response = self.client.post(reverse('signup'), {
            'email': 'existente@example.com',
            'password1': 'contrasena-segura-123',
            'password2': 'contrasena-segura-123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CustomUser.objects.filter(email='existente@example.com').count(), 1)


class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email='usuario@example.com', password='clave-segura123')

    def test_login_redirects_to_portal(self):
        response = self.client.post(reverse('login'), {
            'username': 'usuario@example.com',
            'password': 'clave-segura123',
        })
        self.assertRedirects(response, reverse('portal_home'))

    def test_login_htmx_returns_redirect_header(self):
        response = self.client.post(reverse('login'), {
            'username': 'usuario@example.com',
            'password': 'clave-segura123',
        }, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['HX-Redirect'], '/portal/')

    def test_htmx_login_form_target_survives_the_swap(self):
        # El formulario apunta a #login-form-wrapper y la respuesta de error es solo el <form>.
        # Con hx-swap="outerHTML" el primer error borraba ese contenedor, y desde el segundo
        # intento HTMX ya no enviaba nada: ni con la contrasena correcta se podia entrar sin
        # recargar, y los avisos y el bloqueo nunca llegaban al usuario. El cliente de pruebas
        # no ejecuta HTMX, asi que se protege el invariante de estructura.
        page = self.client.get(reverse('login')).content.decode()
        self.assertIn('id="login-form-wrapper"', page)
        self.assertIn('hx-target="#login-form-wrapper"', page)

        partial = self.client.post(reverse('login'), {
            'username': 'usuario@example.com',
            'password': 'incorrecta',
        }, HTTP_HX_REQUEST='true').content.decode()
        self.assertIn('hx-swap="innerHTML"', partial)
        # El parcial no repite el contenedor: con innerHTML quedaria anidado dentro de si mismo.
        self.assertNotIn('id="login-form-wrapper"', partial)

    def test_login_invalid_credentials_shows_form_again(self):
        response = self.client.post(reverse('login'), {
            'username': 'usuario@example.com',
            'password': 'incorrecta',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_logout_ends_session(self):
        self.client.login(email='usuario@example.com', password='clave-segura123')
        response = self.client.post(reverse('logout'), follow=True)
        self.assertRedirects(response, reverse('login'))
        self.assertFalse(response.context['user'].is_authenticated)


class ProfileTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email='usuario@example.com', password='clave-segura123')
        self.client.login(email='usuario@example.com', password='clave-segura123')

    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('complete_profile'))
        self.assertEqual(response.status_code, 302)

    def test_create_profile(self):
        response = self.client.post(reverse('complete_profile'), {
            'full_name': 'Usuario de Prueba',
            'id_type': 'CC',
            'id_number': '123456789',
            'birth_date': '2000-01-01',
            'gender': 'Otro',
            'phone': '3000000000',
            'education_level': 'Universitario',
        }, follow=True)

        self.assertRedirects(response, reverse('portal_home'))
        self.assertTrue(UserProfile.objects.filter(user=self.user, full_name='Usuario de Prueba').exists())

    def test_alternate_email_is_optional(self):
        response = self.client.post(reverse('complete_profile'), {
            'full_name': 'Usuario de Prueba', 'id_type': 'CC', 'id_number': '123456789',
            'birth_date': '2000-01-01', 'gender': 'Otro', 'phone': '3000000000',
            'education_level': 'Universitario', 'alternate_email': '',
        }, follow=True)

        self.assertRedirects(response, reverse('portal_home'))
        self.assertFalse(UserProfile.objects.get(user=self.user).alternate_email)

    def test_alternate_email_is_saved_when_provided(self):
        self.client.post(reverse('complete_profile'), {
            'full_name': 'Usuario de Prueba', 'id_type': 'CC', 'id_number': '123456789',
            'birth_date': '2000-01-01', 'gender': 'Otro', 'phone': '3000000000',
            'education_level': 'Universitario', 'alternate_email': 'respaldo@example.com',
        })
        self.assertEqual(UserProfile.objects.get(user=self.user).alternate_email, 'respaldo@example.com')

    def test_alternate_email_must_be_a_valid_address(self):
        response = self.client.post(reverse('complete_profile'), {
            'full_name': 'Usuario de Prueba', 'id_type': 'CC', 'id_number': '123456789',
            'birth_date': '2000-01-01', 'gender': 'Otro', 'phone': '3000000000',
            'education_level': 'Universitario', 'alternate_email': 'esto-no-es-un-correo',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(UserProfile.objects.filter(user=self.user).exists())

    def test_edit_existing_profile(self):
        UserProfile.objects.create(
            user=self.user, full_name='Nombre Viejo', id_type='CC', id_number='987654321',
            birth_date='1999-05-05', gender='Otro', phone='3000000000',
        )
        response = self.client.post(reverse('complete_profile'), {
            'full_name': 'Nombre Nuevo',
            'id_type': 'CC',
            'id_number': '987654321',
            'birth_date': '1999-05-05',
            'gender': 'Otro',
            'phone': '3000000000',
            'education_level': '',
        }, follow=True)

        self.assertRedirects(response, reverse('portal_home'))
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.full_name, 'Nombre Nuevo')


class LoginLockoutTests(TestCase):
    """Bloqueo de la cuenta tras 5 intentos fallidos (requisito del documento)."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(email='usuario@example.com', password='clave-segura123')
        cache.clear()
        self.addCleanup(cache.clear)

    def _fail_login(self, email='usuario@example.com', **extra):
        return self.client.post(reverse('login'), {
            'username': email,
            'password': 'incorrecta',
        }, **extra)

    def test_lockout_after_five_failed_attempts(self):
        # Los primeros cuatro fallos todavía dejan intentar.
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS - 1):
            response = self._fail_login()
            self.assertIsNone(response.context['lockout_notice'])

        # El quinto fallo es el que bloquea la cuenta.
        response = self._fail_login()
        self.assertIsNotNone(response.context['lockout_notice'])
        self.assertContains(response, 'bloqueamos temporalmente')

        # Y a partir de ahí ya ni siquiera se intenta autenticar.
        response = self._fail_login()
        self.assertIsNotNone(response.context['lockout_notice'])

    def test_correct_password_rejected_while_locked_out(self):
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS):
            self._fail_login()

        response = self.client.post(reverse('login'), {
            'username': 'usuario@example.com',
            'password': 'clave-segura123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.context['lockout_notice'])
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_successful_login_resets_the_counter(self):
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS - 1):
            self._fail_login()

        self.client.post(reverse('login'), {
            'username': 'usuario@example.com',
            'password': 'clave-segura123',
        })
        self.client.post(reverse('logout'))

        # Tras el acierto el contador vuelve a cero: estos fallos no deben bloquear.
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS - 1):
            response = self._fail_login()
        self.assertIsNone(response.context['lockout_notice'])

    def test_lockout_is_per_account(self):
        otro = CustomUser.objects.create_user(email='otro@example.com', password='clave-segura123')
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS + 1):
            self._fail_login()

        # La cuenta bloqueada no debe afectar a las demás.
        response = self.client.post(reverse('login'), {
            'username': otro.email,
            'password': 'clave-segura123',
        })
        self.assertRedirects(response, reverse('portal_home'))

    def test_warns_before_locking_out(self):
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS - security.WARN_WHEN_REMAINING):
            response = self._fail_login()
        self.assertContains(response, 'antes de que la cuenta se bloquee')

    def test_lockout_notice_shown_in_htmx_partial(self):
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS + 1):
            response = self._fail_login(HTTP_HX_REQUEST='true')

        self.assertTemplateUsed(response, 'users/components/login_form.html')
        self.assertContains(response, 'bloqueamos temporalmente')

    @override_settings(LOGIN_LOCKOUT_SECONDS=0)
    def test_lockout_expires(self):
        for _ in range(settings.LOGIN_MAX_FAILED_ATTEMPTS + 1):
            self._fail_login()

        # Con un bloqueo de duración cero, la cuenta queda libre de inmediato.
        response = self.client.post(reverse('login'), {
            'username': 'usuario@example.com',
            'password': 'clave-segura123',
        })
        self.assertRedirects(response, reverse('portal_home'))


class SessionExpirationSettingsTests(TestCase):
    """Cierre de sesión por inactividad (requisito del documento)."""

    def test_session_expires_after_inactivity_window(self):
        self.assertLessEqual(settings.SESSION_COOKIE_AGE, 60 * 60)
        # Sin esto el plazo sería fijo desde el login, no por inactividad.
        self.assertTrue(settings.SESSION_SAVE_EVERY_REQUEST)

    def test_session_cookie_is_refreshed_on_each_request(self):
        CustomUser.objects.create_user(email='usuario@example.com', password='clave-segura123')
        self.client.login(email='usuario@example.com', password='clave-segura123')

        response = self.client.get(reverse('portal_home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies['sessionid']['max-age'], settings.SESSION_COOKIE_AGE)


class ProfileValidationTests(TestCase):
    """Validacion estricta de documento y telefono (usabilidad del formulario)."""

    def setUp(self):
        self.user = CustomUser.objects.create_user(email='usuario@example.com', password='clave-segura123')
        self.client.login(email='usuario@example.com', password='clave-segura123')

    def _payload(self, **overrides):
        data = {
            'full_name': 'Usuario de Prueba', 'id_type': 'CC', 'id_number': '1098765432',
            'birth_date': '1990-05-20', 'gender': 'Otro', 'phone': '3001234567',
            'education_level': 'Técnico', 'alternate_email': '',
        }
        data.update(overrides)
        return data

    def test_document_rejects_letters(self):
        response = self.client.post(reverse('complete_profile'), self._payload(id_number='10A98765'))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'id_number',
                             'El número de documento debe tener solo dígitos, sin puntos ni espacios.')

    def test_document_rejects_too_short(self):
        response = self.client.post(reverse('complete_profile'), self._payload(id_number='12345'))
        self.assertFormError(response.context['form'], 'id_number',
                             'El número de documento debe tener entre 6 y 10 dígitos; escribiste 5.')

    def test_passport_allows_letters(self):
        self.client.post(reverse('complete_profile'), self._payload(id_type='PA', id_number='AX1234567'))
        self.assertEqual(UserProfile.objects.get(user=self.user).id_number, 'AX1234567')

    def test_phone_accepts_spaces_and_country_code(self):
        self.client.post(reverse('complete_profile'), self._payload(phone='+57 300 123 4567'))
        # Se guarda normalizado: el usuario puede escribirlo como le resulte natural.
        self.assertEqual(UserProfile.objects.get(user=self.user).phone, '3001234567')

    def test_phone_rejects_ten_digits_not_starting_with_three(self):
        response = self.client.post(reverse('complete_profile'), self._payload(phone='6011234567'))
        self.assertFormError(response.context['form'], 'phone',
                             'Un número de 10 dígitos es un celular y debe empezar por 3. Si es un fijo, escribe sus 7 dígitos.')

    def test_phone_accepts_landline(self):
        self.client.post(reverse('complete_profile'), self._payload(phone='245-6789'))
        self.assertEqual(UserProfile.objects.get(user=self.user).phone, '2456789')

    def test_phone_rejects_wrong_length(self):
        response = self.client.post(reverse('complete_profile'), self._payload(phone='30012'))
        self.assertFormError(response.context['form'], 'phone',
                             'Escribe un celular de 10 dígitos o un fijo de 7; escribiste 5 dígitos.')
