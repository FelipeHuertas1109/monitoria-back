#!/usr/bin/env python
"""
Script para probar la conexión a la base de datos PostgreSQL de Supabase
"""

import os
import sys
import django
from django.conf import settings

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

from django.db import connection

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print("✅ Conexión exitosa a la base de datos!")
            print(f"Versión de PostgreSQL: {version[0]}")
            return True
    except Exception as e:
        print("❌ Error al conectar a la base de datos:")
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Probando conexión a la base de datos...")
    success = test_database_connection()
    
    if success:
        print("\n🎉 La configuración de la base de datos está funcionando correctamente!")
    else:
        print("\n💥 Hay un problema con la configuración de la base de datos.")
        sys.exit(1) 