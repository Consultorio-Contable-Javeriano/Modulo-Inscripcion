from django.test import TestCase
from django.urls import reverse

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
