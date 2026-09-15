from django.db import models
from django.utils import timezone
from users.models import CustomUser

class Module(models.Model):
    MODALITY_CHOICES = [
        ('Presencial', 'Presencial'),
        ('Virtual', 'Virtual'),
        ('Ambas', 'Ambas'),
    ]

    name = models.CharField(max_length=200) # Ej: Nivel 1[cite: 2]
    semester = models.CharField(max_length=100) # Ej: Segundo Semestre de 2026[cite: 2]
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES) #[cite: 3]
    
    # Rango horario estricto para recibir inscripciones
    enrollment_start = models.DateTimeField()
    enrollment_end = models.DateTimeField() #[cite: 1, 2]
    
    class_start_date = models.DateField() #[cite: 1, 2]
    class_end_date = models.DateField(blank=True, null=True)
    schedule_details = models.CharField(max_length=255) # Ej: sábados de 2:00 p.m. a 5:00 p.m.[cite: 2]
    
    is_active = models.BooleanField(default=True) #[cite: 3]

    def is_enrollment_open(self):
        # Valida dinámicamente si el formulario debe mostrarse
        now = timezone.now()
        return self.enrollment_start <= now <= self.enrollment_end

    def __str__(self):
        return f"{self.name} - {self.semester}"

class Enrollment(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments')
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    data_treatment_accepted = models.BooleanField(default=False) #[cite: 1, 2]
    entity = models.CharField(max_length=255) #[cite: 1, 2]
    chosen_modality = models.CharField(max_length=50) #[cite: 1, 2]
    
    city = models.CharField(max_length=100) #[cite: 1, 2]
    neighborhood = models.CharField(max_length=100) #[cite: 1, 2]
    
    attendance_commitment = models.BooleanField(default=False) #[cite: 1, 2]

    def __str__(self):
        return f"{self.user.email} -> {self.module.name}"