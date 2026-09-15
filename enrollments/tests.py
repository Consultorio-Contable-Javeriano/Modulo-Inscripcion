from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from users.models import CustomUser, UserProfile, UserSavedDefaults

from .models import Enrollment, Module


class EnrollmentFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(email='estudiante@example.com', password='clave-segura123')
        UserProfile.objects.create(
            user=self.user,
            full_name='Estudiante de Prueba',
            id_type='CC',
            id_number='123456789',
            birth_date=date(2000, 1, 1),
            gender='Otro',
            phone='3000000000',
        )
        now = timezone.now()
        self.open_module = Module.objects.create(
            name='Nivel 1',
            semester='Segundo Semestre de 2026',
            modality='Virtual',
            enrollment_start=now - timedelta(days=1),
            enrollment_end=now + timedelta(days=1),
            class_start_date=now.date() + timedelta(days=10),
            schedule_details='Sábados de 2:00 p.m. a 5:00 p.m.',
            is_active=True,
        )
        self.closed_module = Module.objects.create(
            name='Nivel 2',
            semester='Segundo Semestre de 2026',
            modality='Presencial',
            enrollment_start=now - timedelta(days=10),
            enrollment_end=now - timedelta(days=5),
            class_start_date=now.date() + timedelta(days=10),
            schedule_details='Domingos de 9:00 a.m. a 12:00 p.m.',
            is_active=True,
        )
        self.client.login(email='estudiante@example.com', password='clave-segura123')

    def test_portal_home_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('portal_home'))
        self.assertEqual(response.status_code, 302)

    def test_portal_home_lists_active_modules(self):
        response = self.client.get(reverse('portal_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nivel 1')
        self.assertContains(response, 'Nivel 2')

    def test_enroll_requires_completed_profile(self):
        self.user.profile.delete()
        response = self.client.get(reverse('enroll', args=[self.open_module.id]), follow=True)
        self.assertRedirects(response, reverse('complete_profile'))
        self.assertEqual(Enrollment.objects.count(), 0)

    def test_enroll_form_renders_for_open_module(self):
        response = self.client.get(reverse('enroll', args=[self.open_module.id]))
        self.assertEqual(response.status_code, 200)

    def test_enroll_rejected_when_module_closed(self):
        response = self.client.get(reverse('enroll', args=[self.closed_module.id]), follow=True)
        self.assertRedirects(response, reverse('portal_home'))
        self.assertEqual(Enrollment.objects.count(), 0)

    def test_chosen_modality_must_match_module_modality(self):
        response = self.client.post(reverse('enroll', args=[self.open_module.id]), {
            'entity': 'Empresa X',
            'chosen_modality': 'Presencial',  # el módulo solo permite Virtual
            'city': 'Bogotá',
            'neighborhood': 'Chapinero',
            'data_treatment_accepted': 'on',
            'attendance_commitment': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Enrollment.objects.count(), 0)

    def test_successful_enrollment_creates_record_and_saves_defaults(self):
        response = self.client.post(reverse('enroll', args=[self.open_module.id]), {
            'entity': 'Empresa X',
            'chosen_modality': 'Virtual',
            'city': 'Bogotá',
            'neighborhood': 'Chapinero',
            'data_treatment_accepted': 'on',
            'attendance_commitment': 'on',
        }, follow=True)

        self.assertRedirects(response, reverse('portal_home'))
        self.assertEqual(Enrollment.objects.count(), 1)
        enrollment = Enrollment.objects.get()
        self.assertEqual(enrollment.user, self.user)
        self.assertEqual(enrollment.module, self.open_module)
        self.assertContains(response, 'Inscripción a')

        defaults = UserSavedDefaults.objects.get(user=self.user)
        self.assertEqual(defaults.last_entity, 'Empresa X')
        self.assertEqual(defaults.last_city, 'Bogotá')

    def test_cannot_enroll_twice_in_same_module(self):
        Enrollment.objects.create(
            user=self.user,
            module=self.open_module,
            entity='Empresa X',
            chosen_modality='Virtual',
            city='Bogotá',
            neighborhood='Chapinero',
            data_treatment_accepted=True,
            attendance_commitment=True,
        )

        response = self.client.get(reverse('enroll', args=[self.open_module.id]), follow=True)
        self.assertRedirects(response, reverse('portal_home'))
        self.assertEqual(Enrollment.objects.count(), 1)

    def test_enrollment_requires_accepting_data_treatment(self):
        response = self.client.post(reverse('enroll', args=[self.open_module.id]), {
            'entity': 'Empresa X',
            'chosen_modality': 'Virtual',
            'city': 'Bogotá',
            'neighborhood': 'Chapinero',
            'attendance_commitment': 'on',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Enrollment.objects.count(), 0)
        self.assertFormError(response.context['form'], 'data_treatment_accepted', 'Debes aceptar el tratamiento de datos para inscribirte.')

    def test_my_enrollments_lists_only_own_enrollments(self):
        other_user = CustomUser.objects.create_user(email='otro@example.com', password='clave-segura123')
        Enrollment.objects.create(
            user=other_user, module=self.open_module, entity='Otra', chosen_modality='Virtual',
            city='Cali', neighborhood='Centro', data_treatment_accepted=True, attendance_commitment=True,
        )
        Enrollment.objects.create(
            user=self.user, module=self.open_module, entity='Empresa X', chosen_modality='Virtual',
            city='Bogotá', neighborhood='Chapinero', data_treatment_accepted=True, attendance_commitment=True,
        )

        response = self.client.get(reverse('my_enrollments'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Empresa X')
        self.assertNotContains(response, 'Otra')

    def test_cancel_enrollment_removes_record(self):
        enrollment = Enrollment.objects.create(
            user=self.user, module=self.open_module, entity='Empresa X', chosen_modality='Virtual',
            city='Bogotá', neighborhood='Chapinero', data_treatment_accepted=True, attendance_commitment=True,
        )

        response = self.client.post(reverse('cancel_enrollment', args=[enrollment.id]), follow=True)
        self.assertRedirects(response, reverse('my_enrollments'))
        self.assertEqual(Enrollment.objects.count(), 0)

    def test_cannot_cancel_other_users_enrollment(self):
        other_user = CustomUser.objects.create_user(email='otro@example.com', password='clave-segura123')
        enrollment = Enrollment.objects.create(
            user=other_user, module=self.open_module, entity='Otra', chosen_modality='Virtual',
            city='Cali', neighborhood='Centro', data_treatment_accepted=True, attendance_commitment=True,
        )

        response = self.client.post(reverse('cancel_enrollment', args=[enrollment.id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Enrollment.objects.count(), 1)

    def test_staff_dashboard_requires_staff(self):
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_staff_dashboard_accessible_to_staff(self):
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nivel 1')
