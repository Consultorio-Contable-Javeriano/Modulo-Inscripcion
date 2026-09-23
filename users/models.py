from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from datetime import date


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El Email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None
    email = models.EmailField('Correo electrónico', unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    ID_TYPE_CHOICES = [
        ('CC', 'Cédula de ciudadanía'),
        ('CE', 'Cédula de extranjería'),
        ('TI', 'Tarjeta de identidad'),
        ('PA', 'Pasaporte'),
    ]
    GENDER_CHOICES = [
        ('Femenino', 'Femenino'),
        ('Masculino', 'Masculino'),
        ('Otro', 'Otro'),
        ('Prefiero no decirlo', 'Prefiero no decirlo'),
    ]
    EDUCATION_LEVEL_CHOICES = [
        ('Primaria', 'Primaria'),
        ('Secundaria', 'Secundaria'),
        ('Técnico', 'Técnico'),
        ('Tecnólogo', 'Tecnólogo'),
        ('Profesional', 'Profesional'),
        ('Especialización', 'Especialización'),
        ('Maestría', 'Maestría'),
        ('Doctorado', 'Doctorado'),
        ('Ninguna de las anteriores', 'Ninguna de las anteriores'),
    ]

    # Rangos de edad del formulario oficial (pregunta 5)
    AGE_RANGE_CHOICES = [
        ('6-13', 'Entre 6 a 13 años'),
        ('14-20', 'Entre 14 a 20 años'),
        ('21-35', 'Entre 21 a 35 años'),
        ('36-50', 'Entre 36 a 50 años'),
        ('51-80', 'Entre 51 a 80 años'),
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile', verbose_name='Usuario')
    first_name = models.CharField('Nombres', max_length=150, default='')
    last_name = models.CharField('Apellidos', max_length=150, default='')
    id_type = models.CharField('Tipo de documento', max_length=50, choices=ID_TYPE_CHOICES)
    id_number = models.CharField('Número de documento', max_length=50, unique=True)
    birth_date = models.DateField('Fecha de nacimiento')
    gender = models.CharField('Género', max_length=50, choices=GENDER_CHOICES)
    phone = models.CharField('Teléfono celular', max_length=50)
    alternate_email = models.EmailField('Correo electrónico alternativo', blank=True, null=True)
    education_level = models.CharField('Nivel educativo', max_length=100, choices=EDUCATION_LEVEL_CHOICES, blank=True, null=True)
    has_business = models.BooleanField('Tiene negocio propio', default=False)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - (
            (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        )

    @property
    def age_range(self):
        """Devuelve el rango de edad del formulario oficial que corresponde a la edad actual."""
        a = self.age
        if a <= 13:
            return '6-13'
        elif a <= 20:
            return '14-20'
        elif a <= 35:
            return '21-35'
        elif a <= 50:
            return '36-50'
        else:
            return '51-80'

    @property
    def age_range_display(self):
        """Etiqueta legible del rango de edad."""
        mapping = dict(self.AGE_RANGE_CHOICES)
        return mapping.get(self.age_range, '')

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return self.full_name


class UserSavedDefaults(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='saved_defaults', verbose_name='Usuario')
    last_entity = models.CharField('Última entidad', max_length=255, blank=True, null=True)
    last_city = models.CharField('Última ciudad', max_length=100, blank=True, null=True)
    last_locality = models.CharField('Última localidad o comuna', max_length=100, blank=True, null=True)
    last_neighborhood = models.CharField('Último barrio', max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Valores predeterminados de usuario'
        verbose_name_plural = 'Valores predeterminados de usuario'

    def __str__(self):
        return f"Valores predeterminados de {self.user.email}"
