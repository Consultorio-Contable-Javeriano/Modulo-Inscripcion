from django.urls import path
from . import views
from . import admin_views

app_name = 'consultorio'

urlpatterns = [
    # ── Portal del usuario ────────────────────────────────────────────────────
    path('', views.portal_home, name='portal_home'),
    path('inscribirme/<int:module_id>/', views.enroll, name='enroll'),
    path('mis-inscripciones/', views.my_enrollments, name='my_enrollments'),
    path('mis-inscripciones/<int:enrollment_id>/cancelar/', views.cancel_enrollment, name='cancel_enrollment'),
    path('staff/', views.staff_dashboard, name='staff_dashboard'),
    path('localidad/', views.locality_field, name='locality_field'),

    # ── Panel admin – Módulos ─────────────────────────────────────────────────
    path('admin/modulos/', admin_views.ModuleAdminListView.as_view(), name='admin_module_list'),
    path('admin/modulos/nuevo/', admin_views.ModuleTemplateCreateView.as_view(), name='admin_module_create'),
    path('admin/modulos/<int:pk>/editar/', admin_views.ModuleAdminUpdateView.as_view(), name='admin_module_update'),
    path('admin/modulos/<int:pk>/eliminar/', admin_views.ModuleAdminDeleteView.as_view(), name='admin_module_delete'),

    # ── Panel admin – Usuarios ────────────────────────────────────────────────
    path('admin/usuarios/', admin_views.UserAdminListView.as_view(), name='admin_user_list'),

    # ── Panel admin – Inscripciones ───────────────────────────────────────────
    path('admin/inscripciones/', admin_views.EnrollmentListView.as_view(), name='admin_enrollment_list'),
    path('admin/inscripciones/<int:pk>/eliminar/', admin_views.EnrollmentDeleteView.as_view(), name='admin_enrollment_delete'),

    # ── Panel admin – Subgrupos ───────────────────────────────────────────────
    path('admin/modulos/<int:module_id>/subgrupos/', admin_views.ManageSubgroupsView.as_view(), name='manage_subgroups'),
]