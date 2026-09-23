from django.urls import path
from . import views

app_name = 'consultorio' # O el nombre de tu aplicación

urlpatterns = [
    # ... tus URLs anteriores (ej. manage_subgroups) ...

    # URLs para Módulos
    path('modulos/', views.ModuleListView.as_view(), name='module_list'),
    path('modulos/crear/', views.ModuleCreateView.as_view(), name='module_create'),
    path('modulos/<int:pk>/editar/', views.ModuleUpdateView.as_view(), name='module_update'),
    path('modulos/<int:pk>/eliminar/', views.ModuleDeleteView.as_view(), name='module_delete'),

    # URLs para Usuarios
    path('usuarios/', views.UserListView.as_view(), name='user_list'),
]