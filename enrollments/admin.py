from django.contrib import admin
from .models import Module, Enrollment

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('name', 'semester', 'modality', 'enrollment_start', 'enrollment_end', 'is_active')
    list_filter = ('is_active', 'modality', 'semester') # Filtros de módulos[cite: 3]
    search_fields = ('name', 'semester')
    list_editable = ('is_active',) # Permite activar/desactivar módulos con un clic

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'module', 'chosen_modality', 'entity', 'enrolled_at')
    
    # Filtro crucial: Permite agrupar usuarios por modalidad del módulo[cite: 3]
    list_filter = ('module', 'chosen_modality', 'city')
    
    search_fields = ('user__email', 'user__profile__full_name')