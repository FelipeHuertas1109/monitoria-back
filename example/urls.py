from django.urls import path
from . import views

urlpatterns = [
    # Autenticación
    path('login/', views.login_usuario, name='login_usuario'),
    path('registro/', views.registro_usuario, name='registro_usuario'),
    path('usuario/actual/', views.obtener_usuario_actual, name='obtener_usuario_actual'),
    
    # Horarios Fijos
    path('horarios/', views.horarios_fijos, name='horarios_fijos'),
    path('horarios/multiple/', views.horarios_fijos_multiple, name='horarios_fijos_multiple'),
    path('horarios/edit-multiple/', views.horarios_fijos_edit_multiple, name='horarios_fijos_edit_multiple'),
    path('horarios/<int:pk>/', views.horario_fijo_detalle, name='horario_fijo_detalle'),
    
    # Asistencias
    path('asistencias/', views.asistencias, name='asistencias'),
    path('asistencias/<int:pk>/', views.asistencia_detalle, name='asistencia_detalle'),
]