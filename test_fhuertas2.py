#!/usr/bin/env python3
"""
Test específico para el usuario fhuertas2
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_fhuertas2():
    print("🔍 === TESTING USUARIO FHUERTAS2 ===")
    
    # 1. Login como fhuertas2
    print("\n1️⃣ Login como fhuertas2...")
    response = requests.post(f"{BASE_URL}/login/", json={
        "nombre_de_usuario": "fhuertas2",
        "password": "123456"
    })
    
    print(f"Status del login: {response.status_code}")
    if response.status_code != 200:
        print(f"❌ Error en login: {response.text}")
        return
    
    data = response.json()
    token = data["token"]
    usuario = data["usuario"]
    
    print(f"✅ Usuario logueado: {usuario}")
    print(f"Token obtenido: {token[:50]}...")
    
    # 2. Verificar asistencias del usuario
    print("\n2️⃣ Consultando asistencias...")
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(f"{BASE_URL}/monitor/mis-asistencias/", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        asistencias = response.json()
        print(f"Asistencias encontradas: {len(asistencias)}")
        for asist in asistencias:
            print(f"  - ID: {asist['id']} | Fecha: {asist['fecha']} | Estado: {asist['estado_autorizacion']} | Presente: {asist['presente']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_fhuertas2()
