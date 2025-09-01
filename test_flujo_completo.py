#!/usr/bin/env python3
"""
Test del flujo completo de autorización y marcación
"""
import requests
import json
from datetime import date

BASE_URL = "http://127.0.0.1:8000"

def login_usuario(username, password):
    """Login y obtener token"""
    response = requests.post(f"{BASE_URL}/login/", json={
        "nombre_de_usuario": username,
        "password": password
    })
    if response.status_code == 200:
        data = response.json()
        return data["token"], data["usuario"]
    else:
        print(f"❌ Error en login: {response.status_code} - {response.text}")
        return None, None

def test_flujo_completo():
    print("🔍 === PROBANDO FLUJO COMPLETO ===")
    
    # 1. Login como directivo
    print("\n1️⃣ Login como DIRECTIVO...")
    token_directivo, user_directivo = login_usuario("superusuario", "lolandia1")
    if not token_directivo:
        return
    print(f"✅ Directivo logueado: {user_directivo['username']} - {user_directivo.get('tipo_usuario', 'NO_TIPO')}")
    
    # 2. Login como monitor
    print("\n2️⃣ Login como MONITOR...")
    token_monitor, user_monitor = login_usuario("fhuertas", "lolandia1")
    if not token_monitor:
        return
    print(f"✅ Monitor logueado: {user_monitor['username']} - {user_monitor.get('tipo_usuario', 'NO_TIPO')}")
    
    # 3. Monitor ve sus asistencias (debería estar vacío inicialmente)
    print("\n3️⃣ Monitor consulta sus asistencias...")
    headers_monitor = {"Authorization": f"Bearer {token_monitor}"}
    response = requests.get(f"{BASE_URL}/monitor/mis-asistencias/", headers=headers_monitor)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        asistencias_monitor = response.json()
        print(f"Asistencias del monitor: {len(asistencias_monitor)} encontradas")
        for asist in asistencias_monitor:
            print(f"  - {asist['fecha']} {asist['horario']['jornada_display']} - Estado: {asist['estado_autorizacion']}")
    else:
        print(f"❌ Error: {response.text}")
        return
    
    # 4. Directivo ve las asistencias del día para autorizar
    print("\n4️⃣ Directivo consulta asistencias del día...")
    headers_directivo = {"Authorization": f"Bearer {token_directivo}"}
    response = requests.get(f"{BASE_URL}/directivo/asistencias/", headers=headers_directivo)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        asistencias_directivo = response.json()
        print(f"Asistencias visibles para directivo: {len(asistencias_directivo)} encontradas")
        for asist in asistencias_directivo:
            print(f"  - ID: {asist['id']} | {asist['usuario']['username']} | {asist['fecha']} {asist['horario']['jornada_display']} | Estado: {asist['estado_autorizacion']}")
    else:
        print(f"❌ Error: {response.text}")
        return
    
    # 5. Directivo autoriza la primera asistencia del monitor
    asistencias_monitor_para_autorizar = [a for a in asistencias_directivo if a['usuario']['username'] == 'fhuertas']
    if not asistencias_monitor_para_autorizar:
        print("❌ No hay asistencias del monitor para autorizar")
        return
    
    asistencia_a_autorizar = asistencias_monitor_para_autorizar[0]
    print(f"\n5️⃣ Directivo autoriza asistencia ID {asistencia_a_autorizar['id']}...")
    response = requests.post(
        f"{BASE_URL}/directivo/asistencias/{asistencia_a_autorizar['id']}/autorizar/",
        headers=headers_directivo
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Asistencia autorizada exitosamente")
        print(f"Respuesta: {response.json()}")
    else:
        print(f"❌ Error autorizando: {response.text}")
        return
    
    # 6. Monitor vuelve a consultar sus asistencias (ahora debería ver la autorizada)
    print("\n6️⃣ Monitor consulta nuevamente sus asistencias...")
    response = requests.get(f"{BASE_URL}/monitor/mis-asistencias/", headers=headers_monitor)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        asistencias_monitor_actualizadas = response.json()
        print(f"Asistencias del monitor ACTUALIZADAS: {len(asistencias_monitor_actualizadas)} encontradas")
        for asist in asistencias_monitor_actualizadas:
            estado = asist['estado_autorizacion']
            print(f"  - {asist['fecha']} {asist['horario']['jornada_display']} - Estado: {estado}")
            if estado == 'autorizado':
                print(f"    ✅ BLOQUE AUTORIZADO - Puede marcar asistencia")
    else:
        print(f"❌ Error: {response.text}")
        return
    
    # 7. Monitor intenta marcar asistencia en el bloque autorizado
    asistencias_autorizadas = [a for a in asistencias_monitor_actualizadas if a['estado_autorizacion'] == 'autorizado']
    if not asistencias_autorizadas:
        print("❌ No hay asistencias autorizadas para marcar")
        return
    
    asistencia_autorizada = asistencias_autorizadas[0]
    print(f"\n7️⃣ Monitor marca asistencia en bloque autorizado...")
    response = requests.post(
        f"{BASE_URL}/monitor/marcar/",
        headers=headers_monitor,
        json={
            "fecha": asistencia_autorizada['fecha'],
            "jornada": asistencia_autorizada['horario']['jornada']
        }
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Asistencia marcada exitosamente")
        marcacion = response.json()
        print(f"Presente: {marcacion['presente']}")
        print(f"Horas: {marcacion.get('horas', 'N/A')}")
    else:
        print(f"❌ Error marcando: {response.text}")
        return
    
    print("\n🎉 === FLUJO COMPLETO EXITOSO ===")

if __name__ == "__main__":
    test_flujo_completo()
