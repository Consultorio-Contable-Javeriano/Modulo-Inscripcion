from django.db import models
from django.utils import timezone
from users.models import CustomUser

class Module(models.Model):
    MODALITY_CHOICES = [
        ('Presencial', 'Presencial'),
        ('Virtual', 'Virtual'),
        ('Ambas', 'Ambas'),
    ]

    name = models.CharField('Nombre', max_length=200) # Ej: Nivel 1[cite: 2]
    semester = models.CharField('Semestre', max_length=100) # Ej: Segundo Semestre de 2026[cite: 2]
    modality = models.CharField('Modalidad', max_length=20, choices=MODALITY_CHOICES) #[cite: 3]

    # Rango horario estricto para recibir inscripciones
    enrollment_start = models.DateTimeField('Inicio de inscripciones')
    enrollment_end = models.DateTimeField('Fin de inscripciones') #[cite: 1, 2]

    class_start_date = models.DateField('Fecha de inicio de clases') #[cite: 1, 2]
    class_end_date = models.DateField('Fecha de fin de clases', blank=True, null=True)
    schedule_details = models.CharField('Horario', max_length=255) # Ej: sábados de 2:00 p.m. a 5:00 p.m.[cite: 2]

    is_active = models.BooleanField('Activo', default=True) #[cite: 3]

    def is_enrollment_open(self):
        # Valida dinámicamente si el formulario debe mostrarse
        now = timezone.now()
        return self.enrollment_start <= now <= self.enrollment_end

    def allowed_modalities(self):
        if self.modality == 'Ambas':
            return [c for c in Enrollment.MODALITY_CHOICES]
        return [c for c in Enrollment.MODALITY_CHOICES if c[0] == self.modality]

    class Meta:
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'

    def __str__(self):
        return f"{self.name} - {self.semester}"

class Enrollment(models.Model):
    MODALITY_CHOICES = [
        ('Presencial', 'Presencial'),
        ('Virtual', 'Virtual'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Usuario')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='enrollments', verbose_name='Módulo')
    enrolled_at = models.DateTimeField('Fecha de inscripción', auto_now_add=True)

    data_treatment_accepted = models.BooleanField('Autorización de tratamiento de datos', default=False) #[cite: 1, 2]
    entity = models.CharField('Entidad', max_length=255) #[cite: 1, 2]
    chosen_modality = models.CharField('Modalidad elegida', max_length=50, choices=MODALITY_CHOICES) #[cite: 1, 2]

    city = models.CharField('Ciudad', max_length=100) #[cite: 1, 2]
    neighborhood = models.CharField('Barrio', max_length=100) #[cite: 1, 2]

    attendance_commitment = models.BooleanField('Compromiso de asistencia', default=False) #[cite: 1, 2]

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        constraints = [
            models.UniqueConstraint(fields=['user', 'module'], name='unique_enrollment_per_user_module'),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.module.name}"
