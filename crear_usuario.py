#!/usr/bin/env python
"""
Script para crear el usuario superusuario con las credenciales especificadas
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from example.models import UsuarioPersonalizado

def crear_usuarios():
    try:
        # 1. Actualizar o crear el usuario superusuario (DIRECTIVO)
        superusuario, created = UsuarioPersonalizado.objects.get_or_create(
            username='superusuario',
            defaults={
                'nombre': 'superusuario',
                'tipo_usuario': 'DIRECTIVO'
            }
        )
        
        if not created:
            # Si ya existe, actualizar el tipo a DIRECTIVO
            superusuario.tipo_usuario = 'DIRECTIVO'
            superusuario.save()
            print("✅ Usuario 'superusuario' actualizado a DIRECTIVO")
        else:
            print("✅ Usuario 'superusuario' creado como DIRECTIVO")
        
        superusuario.set_password('lolandia1')
        superusuario.save()
        
        print(f"  Username: {superusuario.username}")
        print(f"  Nombre: {superusuario.nombre}")
        print(f"  Tipo: {superusuario.get_tipo_usuario_display()}")
        print(f"  ID: {superusuario.id}")
        
        print("\n" + "="*50 + "\n")
        
        # 2. Crear el usuario fhuertas (MONITOR)
        if UsuarioPersonalizado.objects.filter(username='fhuertas').exists():
            print("❌ El usuario 'fhuertas' ya existe.")
        else:
            fhuertas = UsuarioPersonalizado(
                username='fhuertas',
                nombre='fhuertas',
                tipo_usuario='MONITOR'
            )
            fhuertas.set_password('lolandia1')
            fhuertas.save()
            
            print("✅ Usuario 'fhuertas' creado como MONITOR")
            print(f"  Username: {fhuertas.username}")
            print(f"  Nombre: {fhuertas.nombre}")
            print(f"  Tipo: {fhuertas.get_tipo_usuario_display()}")
            print(f"  ID: {fhuertas.id}")
        
        print("\n" + "="*50)
        print("📋 RESUMEN DE USUARIOS:")
        usuarios = UsuarioPersonalizado.objects.all()
        for usuario in usuarios:
            print(f"  • {usuario.username} - {usuario.get_tipo_usuario_display()}")
        
    except Exception as e:
        print(f"❌ Error al crear/actualizar usuarios: {e}")

if __name__ == '__main__':
    crear_usuarios()
