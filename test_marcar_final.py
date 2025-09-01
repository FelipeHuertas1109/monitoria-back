#!/usr/bin/env python3
"""
Test de marcación final para fhuertas2
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_marcar():
    print("🔍 === TESTING MARCACIÓN FHUERTAS2 ===")
    
    # 1. Login como fhuertas2
    response = requests.post(f"{BASE_URL}/login/", json={
        "nombre_de_usuario": "fhuertas2",
        "password": "123456"
    })
    
    if response.status_code != 200:
        print(f"❌ Error en login: {response.text}")
        return
    
    data = response.json()
    token = data["token"]
    usuario = data["usuario"]
    
    print(f"✅ Usuario logueado: {usuario['username']} (ID: {usuario['id']})")
    
    # 2. Marcar asistencia en bloque autorizado
    print("\n2️⃣ Marcando asistencia...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.post(f"{BASE_URL}/monitor/marcar/", 
                           headers=headers,
                           json={
                               "fecha": "2025-09-01",
                               "jornada": "M"
                           })
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        marcacion = response.json()
        print(f"✅ Asistencia marcada exitosamente!")
        print(f"  - Presente: {marcacion['presente']}")
        print(f"  - Estado: {marcacion['estado_autorizacion']}")
        print(f"  - Horas: {marcacion.get('horas', 'N/A')}")
    else:
        print(f"❌ Error al marcar: {response.status_code} - {response.text}")
    
    # 3. Verificar asistencias actualizadas
    print("\n3️⃣ Verificando asistencias después de marcar...")
    response = requests.get(f"{BASE_URL}/monitor/mis-asistencias/", headers=headers)
    
    if response.status_code == 200:
        asistencias = response.json()
        print(f"Asistencias después de marcar: {len(asistencias)}")
        for asist in asistencias:
            print(f"  - ID: {asist['id']} | Presente: {asist['presente']} | Horas: {asist.get('horas', 'N/A')}")

if __name__ == "__main__":
    test_marcar()
