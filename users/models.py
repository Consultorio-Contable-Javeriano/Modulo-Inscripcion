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

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile', verbose_name='Usuario')
    full_name = models.CharField('Nombre completo', max_length=255) #[cite: 1, 2]
    id_type = models.CharField('Tipo de documento', max_length=50, choices=ID_TYPE_CHOICES) #[cite: 1, 2]
    id_number = models.CharField('Número de documento', max_length=50, unique=True) #[cite: 1, 2]
    first_name = models.CharField('Nombres', max_length=150, default='')
    last_name = models.CharField('Apellidos', max_length=150, default='')
    id_type = models.CharField('Tipo de documento', max_length=50, choices=ID_TYPE_CHOICES)
    id_number = models.CharField('Número de documento', max_length=50, unique=True)
    birth_date = models.DateField('Fecha de nacimiento')
    gender = models.CharField('Género', max_length=50, choices=GENDER_CHOICES) #[cite: 1, 2]
    phone = models.CharField('Teléfono', max_length=50) #[cite: 1, 2]
    gender = models.CharField('Género', max_length=50, choices=GENDER_CHOICES)
    phone = models.CharField('Teléfono celular', max_length=50)
    # Correo secundario opcional, pedido en el documento de levantamiento: sirve de
    # respaldo para contactar al usuario sin reemplazar al correo de la cuenta.
    alternate_email = models.EmailField('Correo electrónico alternativo', blank=True, null=True)
    education_level = models.CharField('Nivel educativo', max_length=100, blank=True, null=True) #[cite: 1, 2]
    has_business = models.BooleanField('Tiene negocio propio', default=False) #[cite: 1, 2]
    education_level = models.CharField('Nivel educativo', max_length=100, choices=EDUCATION_LEVEL_CHOICES, blank=True, null=True)
    has_business = models.BooleanField('Tiene negocio propio', default=False)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def age(self):
        # Cálculo dinámico de la edad para evitar datos obsoletos
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    class Meta:
        verbose_name = 'Perfil de usuario'
        verbose_name_plural = 'Perfiles de usuario'

    def __str__(self):
        return self.full_name


class UserSavedDefaults(models.Model):
    # Tabla invisible para autocompletar formularios futuros
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='saved_defaults', verbose_name='Usuario')
    last_entity = models.CharField('Última entidad', max_length=255, blank=True, null=True) #[cite: 1, 2]
    last_city = models.CharField('Última ciudad', max_length=100, blank=True, null=True) #[cite: 1, 2]
    last_locality = models.CharField('Última localidad o comuna', max_length=100, blank=True, null=True)
    last_neighborhood = models.CharField('Último barrio', max_length=100, blank=True, null=True) #[cite: 1, 2]

    class Meta:
        verbose_name = 'Valores predeterminados de usuario'
        verbose_name_plural = 'Valores predeterminados de usuario'

    def __str__(self):
        return f"Valores predeterminados de {self.user.email}"
