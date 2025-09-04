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

    # Directivo
    path('directivo/horarios/', views.directivo_horarios_monitores, name='directivo_horarios_monitores'),
    path('directivo/asistencias/', views.directivo_asistencias, name='directivo_asistencias'),
    path('directivo/asistencias/<int:pk>/autorizar/', views.directivo_autorizar_asistencia, name='directivo_autorizar_asistencia'),
    path('directivo/asistencias/<int:pk>/rechazar/', views.directivo_rechazar_asistencia, name='directivo_rechazar_asistencia'),
    
    # Reportes
    path('directivo/reportes/horas-monitor/<int:monitor_id>/', views.directivo_reporte_horas_monitor, name='directivo_reporte_horas_monitor'),
    path('directivo/reportes/horas-todos/', views.directivo_reporte_horas_todos, name='directivo_reporte_horas_todos'),

    # Monitor
    path('monitor/mis-asistencias/', views.monitor_mis_asistencias, name='monitor_mis_asistencias'),
    path('monitor/marcar/', views.monitor_marcar, name='monitor_marcar'),
    
    # Ajustes de Horas
    path('directivo/ajustes-horas/', views.directivo_ajustes_horas, name='directivo_ajustes_horas'),
    path('directivo/ajustes-horas/<int:pk>/', views.directivo_ajuste_horas_detalle, name='directivo_ajuste_horas_detalle'),
    
    # Búsqueda de Monitores
    path('directivo/buscar-monitores/', views.directivo_buscar_monitores, name='directivo_buscar_monitores'),
]