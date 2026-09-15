from django.urls import path
from . import views

urlpatterns = [
    path('', views.portal_home, name='portal_home'),
    path('inscribirse/<int:module_id>/', views.enroll, name='enroll'),
    path('mis-inscripciones/', views.my_enrollments, name='my_enrollments'),
    path('mis-inscripciones/<int:enrollment_id>/cancelar/', views.cancel_enrollment, name='cancel_enrollment'),
    path('administrar/', views.staff_dashboard, name='staff_dashboard'),
]
