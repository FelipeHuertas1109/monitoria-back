#!/usr/bin/env python
"""
Script para resetear completamente la base de datos
"""
import os
import django
import psycopg2
from decouple import config

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')
django.setup()

def reset_database():
    try:
        # Obtener configuración de la base de datos
        db_host = config('DB_HOST', default='db.jpqhjkimtxvbqswauxod.supabase.co')
        db_port = config('DB_PORT', default='5432')
        db_name = config('DB_NAME', default='postgres')
        db_user = config('DB_USER', default='postgres')
        db_password = config('DB_PASSWORD', default='YOUR_PASSWORD_HERE')
        
        print(f"Conectando a la base de datos: {db_host}:{db_port}")
        
        # Conectar a la base de datos
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password
        )
        
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Eliminar todas las tablas existentes
        print("Eliminando todas las tablas existentes...")
        
        # Obtener todas las tablas
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'pg_%'
        """)
        
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            print(f"Eliminando tabla: {table_name}")
            cursor.execute(f'DROP TABLE IF EXISTS "{table_name}" CASCADE')
        
        # Eliminar todas las secuencias
        cursor.execute("""
            SELECT sequence_name FROM information_schema.sequences 
            WHERE sequence_schema = 'public'
        """)
        
        sequences = cursor.fetchall()
        
        for sequence in sequences:
            sequence_name = sequence[0]
            print(f"Eliminando secuencia: {sequence_name}")
            cursor.execute(f'DROP SEQUENCE IF EXISTS "{sequence_name}" CASCADE')
        
        print("Base de datos reseteada exitosamente!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error al resetear la base de datos: {e}")
        print("Asegúrate de que las credenciales en el archivo .env sean correctas")

if __name__ == '__main__':
    reset_database()
