from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpResponse

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # Si es una petición de HTMX, usamos HX-Redirect para mover al usuario al portal/dashboard
            if request.headers.get('HX-Request'):
                response = HttpResponse(status=200)
                response['HX-Redirect'] = '/portal/' # Cambiar por tu URL de redirección
                return response
            return redirect('portal_home')
        else:
            # Si hay error en las credenciales y viene por HTMX, devolvemos solo el formulario con los errores
            if request.headers.get('HX-Request'):
                return render(request, 'users/components/login_form.html', {'form': form})
    else:
        form = AuthenticationForm()

    # Si entra por primera vez a la página de login
    return render(request, 'users/login.html', {'form': form})