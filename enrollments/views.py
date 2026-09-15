from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render

from users.models import UserSavedDefaults

from .forms import EnrollmentForm
from .models import Enrollment, Module


@login_required
def portal_home(request):
    modules = Module.objects.filter(is_active=True).order_by('enrollment_start')
    enrolled_module_ids = set(
        Enrollment.objects.filter(user=request.user, module__in=modules).values_list('module_id', flat=True)
    )
    return render(request, 'enrollments/portal_home.html', {
        'modules': modules,
        'enrolled_module_ids': enrolled_module_ids,
        'profile_incomplete': not hasattr(request.user, 'profile'),
    })


@login_required
def enroll(request, module_id):
    module = get_object_or_404(Module, pk=module_id, is_active=True)

    if not hasattr(request.user, 'profile'):
        messages.info(request, 'Completa tu perfil antes de inscribirte a un módulo.')
        return redirect('complete_profile')

    if not module.is_enrollment_open():
        messages.error(request, 'Las inscripciones para este módulo no están abiertas.')
        return redirect('portal_home')

    if Enrollment.objects.filter(user=request.user, module=module).exists():
        messages.info(request, 'Ya estás inscrito en este módulo.')
        return redirect('portal_home')

    defaults = UserSavedDefaults.objects.filter(user=request.user).first()
    initial = {}
    if defaults:
        initial = {
            'entity': defaults.last_entity,
            'city': defaults.last_city,
            'neighborhood': defaults.last_neighborhood,
        }

    if request.method == 'POST':
        form = EnrollmentForm(request.POST, module=module)
        if form.is_valid():
            enrollment = form.save(commit=False)
            enrollment.user = request.user
            enrollment.module = module
            try:
                enrollment.save()
            except IntegrityError:
                messages.info(request, 'Ya estás inscrito en este módulo.')
                return redirect('portal_home')

            UserSavedDefaults.objects.update_or_create(
                user=request.user,
                defaults={
                    'last_entity': enrollment.entity,
                    'last_city': enrollment.city,
                    'last_neighborhood': enrollment.neighborhood,
                },
            )

            messages.success(request, f'Inscripción a "{module.name}" realizada con éxito.')
            return redirect('portal_home')
    else:
        form = EnrollmentForm(module=module, initial=initial)

    return render(request, 'enrollments/enroll_form.html', {'form': form, 'module': module})


@login_required
def my_enrollments(request):
    enrollments = Enrollment.objects.filter(user=request.user).select_related('module').order_by('-enrolled_at')
    return render(request, 'enrollments/my_enrollments.html', {'enrollments': enrollments})


@login_required
def cancel_enrollment(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, pk=enrollment_id, user=request.user)

    if request.method == 'POST':
        if not enrollment.module.is_enrollment_open():
            messages.error(request, 'No puedes cancelar: las inscripciones de este módulo ya cerraron.')
        else:
            module_name = enrollment.module.name
            enrollment.delete()
            messages.success(request, f'Cancelaste tu inscripción a "{module_name}".')
        return redirect('my_enrollments')

    return render(request, 'enrollments/cancel_confirm.html', {'enrollment': enrollment})


@login_required
def staff_dashboard(request):
    if not request.user.is_staff:
        raise PermissionDenied('Solo el personal administrativo puede ver este panel.')

    modules = Module.objects.all().order_by('-enrollment_start').prefetch_related('enrollments__user__profile')
    return render(request, 'enrollments/staff_dashboard.html', {'modules': modules})
