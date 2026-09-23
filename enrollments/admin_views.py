from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from dateutil.relativedelta import relativedelta

from users.models import CustomUser

from .models import Enrollment, Module, Subgroup


class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


# ── CRUD de Módulos ──────────────────────────────────────────────────────────

class ModuleAdminListView(AdminRequiredMixin, ListView):
    model = Module
    template_name = 'enrollments/admin/module_list.html'
    context_object_name = 'modules'

    def get_queryset(self):
        return Module.objects.all().order_by('level', 'enrollment_start')


class ModuleTemplateCreateView(AdminRequiredMixin, CreateView):
    model = Module
    template_name = 'enrollments/admin/module_form.html'
    fields = [
        'name', 'level', 'semester', 'modality',
        'enrollment_start', 'enrollment_end',
        'class_start_date', 'class_end_date',
        'schedule_details', 'is_active',
    ]
    success_url = reverse_lazy('consultorio:admin_module_list')

    def get_initial(self):
        initial = super().get_initial()
        level = self.request.GET.get('level', '1')
        if level == '1':
            initial.update({'name': 'Nivel 1 – Básico', 'level': 1, 'modality': 'Virtual'})
        elif level == '2':
            initial.update({'name': 'Nivel 2 – Intermedio', 'level': 2, 'modality': 'Presencial'})
        elif level == '3':
            initial.update({'name': 'Nivel 3 – Avanzado', 'level': 3, 'modality': 'Ambas'})
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Crear Módulo'
        return ctx


class ModuleAdminUpdateView(AdminRequiredMixin, UpdateView):
    model = Module
    template_name = 'enrollments/admin/module_form.html'
    fields = [
        'name', 'level', 'semester', 'modality',
        'enrollment_start', 'enrollment_end',
        'class_start_date', 'class_end_date',
        'schedule_details', 'is_active',
    ]
    success_url = reverse_lazy('consultorio:admin_module_list')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = f'Editar módulo: {self.object.name}'
        return ctx


class ModuleAdminDeleteView(AdminRequiredMixin, DeleteView):
    model = Module
    template_name = 'enrollments/admin/module_confirm_delete.html'
    success_url = reverse_lazy('consultorio:admin_module_list')

    def form_valid(self, form):
        messages.success(self.request, f'Módulo "{self.object.name}" eliminado.')
        return super().form_valid(form)


# ── CRUD de Usuarios (solo lectura + búsqueda) ───────────────────────────────

class UserAdminListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'users/admin/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        qs = CustomUser.objects.filter(is_staff=False).select_related('profile').order_by('email')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(email__icontains=q) | qs.filter(profile__first_name__icontains=q) | qs.filter(profile__last_name__icontains=q)
        return qs

    def get_template_names(self):
        # Si la petición es HTMX devolvemos sólo el partial con la tabla
        if self.request.headers.get('HX-Request'):
            return ['users/admin/partials/user_rows.html']
        return ['users/admin/user_list.html']


# ── CRUD de Inscripciones ────────────────────────────────────────────────────

class EnrollmentListView(AdminRequiredMixin, ListView):
    model = Enrollment
    template_name = 'enrollments/admin/enrollment_list.html'
    context_object_name = 'enrollments'

    def get_queryset(self):
        return Enrollment.objects.all().select_related('user', 'module', 'user__profile').order_by('-enrolled_at')


class EnrollmentDeleteView(AdminRequiredMixin, DeleteView):
    model = Enrollment
    template_name = 'enrollments/admin/enrollment_confirm_delete.html'
    success_url = reverse_lazy('consultorio:admin_enrollment_list')

    def form_valid(self, form):
        messages.success(self.request, f'Inscripción de {self.object.user.email} eliminada.')
        return super().form_valid(form)


# ── Gestión de Subgrupos ─────────────────────────────────────────────────────

# Rangos de edad del formulario oficial (pregunta 5 del formulario de inscripción Nivel 1)
AGE_RANGES = [
    ('6-13',   'Entre 6 a 13 años',   6,  13),
    ('14-20',  'Entre 14 a 20 años',  14, 20),
    ('21-35',  'Entre 21 a 35 años',  21, 35),
    ('36-50',  'Entre 36 a 50 años',  36, 50),
    ('51-80',  'Entre 51 a 80 años',  51, 80),
]


class ManageSubgroupsView(AdminRequiredMixin, ListView):
    template_name = 'enrollments/admin/manage_subgroups.html'
    context_object_name = 'enrollments'

    def _get_module(self):
        if not hasattr(self, '_module'):
            self._module = get_object_or_404(Module, pk=self.kwargs['module_id'])
        return self._module

    def get_queryset(self):
        module = self._get_module()
        qs = Enrollment.objects.filter(module=module).select_related('user__profile').order_by(
            'user__profile__last_name', 'user__profile__first_name'
        )

        filter_type = self.request.GET.get('filter', 'all')

        if filter_type == 'has_business':
            qs = qs.filter(user__profile__has_business=True)
        elif filter_type in {r[0] for r in AGE_RANGES}:
            # Buscar el rango solicitado
            for slug, _label, age_min, age_max in AGE_RANGES:
                if slug == filter_type:
                    today = date.today()
                    date_max = today - relativedelta(years=age_min)  # nacidos hasta aquí tienen ≥ age_min
                    date_min = today - relativedelta(years=age_max + 1) + relativedelta(days=1)
                    qs = qs.filter(user__profile__birth_date__gte=date_min, user__profile__birth_date__lte=date_max)
                    break

        return qs

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['enrollments/admin/partials/enrollment_rows.html']
        return ['enrollments/admin/manage_subgroups.html']

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        module = self._get_module()
        ctx['module'] = module
        ctx['subgroups'] = module.subgroups.prefetch_related('enrollments').all()
        ctx['age_ranges'] = AGE_RANGES
        ctx['active_filter'] = self.request.GET.get('filter', 'all')
        return ctx

    def post(self, request, *args, **kwargs):
        module = self._get_module()
        subgroup_name = request.POST.get('subgroup_name', '').strip()
        selected_ids = request.POST.getlist('enrollment_ids')

        if subgroup_name and selected_ids:
            subgroup = Subgroup.objects.create(module=module, name=subgroup_name)
            subgroup.enrollments.set(selected_ids)
            messages.success(request, f"Subgrupo '{subgroup_name}' creado con {len(selected_ids)} participante(s).")
        elif not subgroup_name:
            messages.error(request, 'Debes escribir un nombre para el subgrupo.')
        else:
            messages.error(request, 'Selecciona al menos un participante.')

        return redirect('consultorio:manage_subgroups', module_id=module.id)