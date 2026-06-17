from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('appointments/add/', views.add_appointment, name='add_appointment'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('check-in/', views.check_in, name='check_in'),
    path('check-out/', views.check_out, name='check_out'),
    path('kpi-export/', views.kpi_export, name='kpi_export'),
    path('api/appointments/', views.api_appointments, name='api_appointments'),
    path('api/check-bol/', views.api_check_bol, name='api_check_bol'),
    path('api/capacity-check/', views.api_capacity_check, name='api_capacity_check'),
    path('api/appointment-stats/', views.api_appointment_stats, name='api_appointment_stats'),
]
