from django.contrib import admin
from .models import UsuarioPersonalizado, HorarioFijo, Asistencia

@admin.register(UsuarioPersonalizado)
class UsuarioPersonalizadoAdmin(admin.ModelAdmin):
    list_display = ['username', 'nombre', 'tipo_usuario', 'is_active', 'date_joined']
    list_filter = ['tipo_usuario', 'is_active', 'date_joined']
    search_fields = ['username', 'nombre']
    ordering = ['username']

@admin.register(HorarioFijo)
class HorarioFijoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'dia_semana', 'jornada', 'sede']
    list_filter = ['dia_semana', 'jornada', 'sede']
    search_fields = ['usuario__username', 'usuario__nombre']
    ordering = ['usuario', 'dia_semana', 'jornada']

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'fecha', 'horario', 'presente']
    list_filter = ['fecha', 'presente', 'horario__sede']
    search_fields = ['usuario__username', 'usuario__nombre']
    ordering = ['-fecha', 'usuario']
    date_hierarchy = 'fecha'
