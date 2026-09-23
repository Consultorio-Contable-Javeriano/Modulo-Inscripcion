from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Module, Enrollment, Subgroup
from users.models import CustomUser
from django.utils.dateparse import parse_date
from datetime import date
from dateutil.relativedelta import relativedelta

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

# --- CRUD DE MÓDULOS ---
class ModuleAdminListView(AdminRequiredMixin, ListView):
    model = Module
    template_name = 'enrollments/admin/module_list.html'
    context_object_name = 'modules'

class ModuleTemplateCreateView(AdminRequiredMixin, CreateView):
    model = Module
    template_name = 'enrollments/admin/module_form.html'
    fields = ['name', 'level', 'semester', 'modality', 'enrollment_start', 'enrollment_end', 'class_start_date', 'class_end_date', 'schedule_details', 'is_active']
    success_url = reverse_lazy('admin_module_list')

    def get_initial(self):
        initial = super().get_initial()
        # Plantillas basadas en el parámetro de la URL (?level=1, 2 o 3)
        level = self.request.GET.get('level', '1')
        if level == '1':
            initial.update({'name': 'Nivel 1 - Básico', 'level': 1, 'modality': 'Virtual'})
        elif level == '2':
            initial.update({'name': 'Nivel 2 - Intermedio', 'level': 2, 'modality': 'Presencial'})
        elif level == '3':
            initial.update({'name': 'Nivel 3 - Avanzado', 'level': 3, 'modality': 'Ambas'})
        return initial

# --- CRUD DE USUARIOS (Solo lectura y edición básica) ---
class UserAdminListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/admin/user_list.html'
    context_object_name = 'users'
    
    def get_queryset(self):
        return CustomUser.objects.filter(is_staff=False).select_related('profile')
    
class ManageSubgroupsView(AdminRequiredMixin, ListView):
    template_name = 'enrollments/admin/manage_subgroups.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        self.module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        qs = Enrollment.objects.filter(module=self.module).select_related('user__profile')
        
        # Filtros por defecto (HTMX puede recargar esta tabla pasando el parámetro ?filter=)
        filter_type = self.request.GET.get('filter')
        
        if filter_type == 'has_business':
            qs = qs.filter(user__profile__has_business=True)
        elif filter_type == 'adults':
            # Ejemplo: Agrupar mayores de 30 años (calculado desde la base de datos)
            threshold_date = date.today() - relativedelta(years=30)
            qs = qs.filter(user__profile__birth_date__lte=threshold_date)
            
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['module'] = self.module
        context['subgroups'] = self.module.subgroups.all()
        return context

    def post(self, request, *args, **kwargs):
        self.module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        subgroup_name = request.POST.get('subgroup_name')
        selected_enrollments = request.POST.getlist('enrollment_ids') # Array de IDs de los checkboxes

        if subgroup_name and selected_enrollments:
            subgroup = Subgroup.objects.create(module=self.module, name=subgroup_name)
            subgroup.enrollments.add(*selected_enrollments)
            messages.success(request, f"Subgrupo '{subgroup_name}' creado con {len(selected_enrollments)} usuarios.")
        
        return redirect('manage_subgroups', module_id=self.module.id)