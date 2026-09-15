from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import date

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager # Importamos BaseUserManager
from datetime import date

# 1. Creamos el Manager personalizado
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

# 2. Conectamos el Manager a nuestro CustomUser
class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Le decimos a Django que use el nuevo gestor
    objects = CustomUserManager()

    def __str__(self):
        return self.email

# ... (El resto de tus modelos UserProfile y UserSavedDefaults quedan exactamente igual)

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255) #[cite: 1, 2]
    id_type = models.CharField(max_length=50) #[cite: 1, 2]
    id_number = models.CharField(max_length=50, unique=True) #[cite: 1, 2]
    birth_date = models.DateField()
    gender = models.CharField(max_length=50) #[cite: 1, 2]
    phone = models.CharField(max_length=50) #[cite: 1, 2]
    education_level = models.CharField(max_length=100, blank=True, null=True) #[cite: 1, 2]
    has_business = models.BooleanField(default=False) #[cite: 1, 2]

    @property
    def age(self):
        # Cálculo dinámico de la edad para evitar datos obsoletos
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

    def __str__(self):
        return self.full_name

class UserSavedDefaults(models.Model):
    # Tabla invisible para autocompletar formularios futuros
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='saved_defaults')
    last_entity = models.CharField(max_length=255, blank=True, null=True) #[cite: 1, 2]
    last_city = models.CharField(max_length=100, blank=True, null=True) #[cite: 1, 2]
    last_neighborhood = models.CharField(max_length=100, blank=True, null=True) #[cite: 1, 2]