from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile, UserSavedDefaults

class CustomUserAdmin(UserAdmin):
    # Sobrescribimos el ordenamiento y las columnas para usar el email
    ordering = ('email',)
    list_display = ('email', 'is_staff', 'is_active')
    search_fields = ('email',)
    
    # Quitamos el 'username' de los formularios de edición y creación
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Fechas importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password'),
        }),
    )

# Registramos el usuario con nuestra configuración personalizada
admin.site.register(CustomUser, CustomUserAdmin)

# --- Deja el resto del archivo exactamente igual (UserProfileAdmin, etc.) ---
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'id_number', 'has_business', 'age')
    list_filter = ('has_business', 'gender', 'education_level')
    search_fields = ('full_name', 'id_number', 'user__email')

@admin.register(UserSavedDefaults)
class UserSavedDefaultsAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_entity', 'last_city')