from django.urls import path
from . import views

urlpatterns = [
    path('', views.operator_select, name='pit_select'),
    path('board/', views.task_board, name='pit_board'),
    path('inbound/', views.inbound_list, name='pit_inbound'),
    path('inbound/<int:task_id>/', views.inbound_work, name='pit_inbound_work'),
    path('inbound/<int:task_id>/start/', views.start_task, name='pit_start_task'),
    path('inbound/<int:task_id>/complete/', views.complete_task, name='pit_complete_task'),
    path('outbound/', views.outbound_list, name='pit_outbound'),
    path('outbound/<int:task_id>/', views.outbound_work, name='pit_outbound_work'),
    path('outbound/<int:task_id>/start/', views.start_task, name='pit_start_outbound'),
    path('outbound/<int:task_id>/complete/', views.complete_task, name='pit_complete_outbound'),
    path('putaway/', views.putaway_list, name='pit_putaway'),
    path('putaway/<int:task_id>/', views.putaway_work, name='pit_putaway_work'),
    path('putaway/<int:task_id>/start/', views.start_task, name='pit_start_putaway'),
    path('putaway/<int:task_id>/complete/', views.complete_putaway, name='pit_complete_putaway'),
    path('pick/', views.pick_list, name='pit_pick'),
    path('pick/<int:task_id>/', views.pick_work, name='pit_pick_work'),
    path('pick/<int:task_id>/start/', views.start_pick, name='pit_start_pick'),
    path('pick/<int:task_id>/complete/', views.complete_pick, name='pit_complete_pick'),
]
