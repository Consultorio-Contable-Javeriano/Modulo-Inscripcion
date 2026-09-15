from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import SignupForm, UserProfileForm
from .models import UserProfile


def _safe_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return next_url
    return reverse('portal_home')


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = _safe_next_url(request)

            # Si es una petición de HTMX, usamos HX-Redirect para mover al usuario al portal/dashboard
            if request.headers.get('HX-Request'):
                response = HttpResponse(status=200)
                response['HX-Redirect'] = next_url
                return response
            return redirect(next_url)
        else:
            # Si hay error en las credenciales y viene por HTMX, devolvemos solo el formulario con los errores
            if request.headers.get('HX-Request'):
                return render(request, 'users/components/login_form.html', {
                    'form': form, 'next': request.POST.get('next', ''),
                })
    else:
        form = AuthenticationForm()

    # Si entra por primera vez a la página de login
    return render(request, 'users/login.html', {'form': form, 'next': request.GET.get('next', '')})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('portal_home')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cuenta creada con éxito. Completa tu perfil para continuar.')
            return redirect('complete_profile')
    else:
        form = SignupForm()

    return render(request, 'users/signup.html', {'form': form})


@login_required
def profile_view(request):
    profile = getattr(request.user, 'profile', None)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, 'Tu perfil se guardó correctamente.')
            return redirect('portal_home')
    else:
        form = UserProfileForm(instance=profile)

    return render(request, 'users/profile_form.html', {'form': form, 'is_new': profile is None})
