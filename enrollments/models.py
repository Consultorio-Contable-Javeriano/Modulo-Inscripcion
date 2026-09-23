from django.db import models
from django.utils import timezone
from users.models import CustomUser


class Module(models.Model):
    MODALITY_CHOICES = [
        ('Presencial', 'Presencial'),
        ('Virtual', 'Virtual'),
        ('Ambas', 'Ambas'),
    ]

    name = models.CharField('Nombre', max_length=200)
    level = models.PositiveIntegerField('Nivel del módulo', default=1)
    semester = models.CharField('Semestre', max_length=100)
    modality = models.CharField('Modalidad', max_length=20, choices=MODALITY_CHOICES)

    enrollment_start = models.DateTimeField('Inicio de inscripciones')
    enrollment_end = models.DateTimeField('Fin de inscripciones')

    class_start_date = models.DateField('Fecha de inicio de clases')
    class_end_date = models.DateField('Fecha de fin de clases', blank=True, null=True)
    schedule_details = models.CharField('Horario', max_length=255)

    is_active = models.BooleanField('Activo', default=True)

    def is_enrollment_open(self):
        now = timezone.now()
        return self.enrollment_start <= now <= self.enrollment_end

    def allowed_modalities(self):
        if self.modality == 'Ambas':
            return [c for c in Enrollment.MODALITY_CHOICES]
        return [c for c in Enrollment.MODALITY_CHOICES if c[0] == self.modality]

    def can_user_enroll(self, user):
        """Verifica la regla de progresión lineal (Nivel N requiere haber estado en Nivel N-1)."""
        if self.level <= 1:
            return True, ""

        prev_level = self.level - 1
        has_prev = Enrollment.objects.filter(user=user, module__level=prev_level).exists()
        if not has_prev:
            return False, f"Debes estar inscrito previamente en un módulo de Nivel {prev_level} para inscribirte a este nivel."
        return True, ""

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

    data_treatment_accepted = models.BooleanField('Autorización de tratamiento de datos', default=False)
    entity = models.CharField('Entidad', max_length=255)
    other_entity = models.CharField('Otra entidad', max_length=255, blank=True, null=True)
    chosen_modality = models.CharField('Modalidad elegida', max_length=50, choices=MODALITY_CHOICES)

    city = models.CharField('Ciudad', max_length=100)
    locality = models.CharField('Localidad o comuna', max_length=100, blank=True)
    neighborhood = models.CharField('Barrio', max_length=100)

    attendance_commitment = models.BooleanField('Compromiso de asistencia', default=False)

    class Meta:
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        constraints = [
            models.UniqueConstraint(fields=['user', 'module'], name='unique_enrollment_per_user_module'),
        ]

    def __str__(self):
        return f"{self.user.email} -> {self.module.name}"


class Subgroup(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='subgroups', verbose_name='Módulo')
    name = models.CharField('Nombre del Subgrupo', max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    # Relación ManyToMany para agrupar inscripciones
    enrollments = models.ManyToManyField('Enrollment', related_name='subgroups', blank=True)

    class Meta:
        verbose_name = 'Subgrupo'
        verbose_name_plural = 'Subgrupos'

    def __str__(self):
        return f"{self.name} - {self.module.name}"
