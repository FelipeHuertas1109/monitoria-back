# 💰 Guía Completa del Módulo de Finanzas

## 📋 1. Configuración Inicial

Antes de usar las finanzas, asegúrate de tener:

**A. Usuarios DIRECTIVO**
- Los endpoints solo funcionan con este tipo de usuario
- Verifica que tengas al menos un usuario con `tipo_usuario='DIRECTIVO'`

**B. Configuraciones del Sistema**
- Las configuraciones ya están inicializadas:
  - `costo_por_hora`: 9,965 COP
  - `semanas_semestre`: 14 semanas

**C. Datos Base**
- Monitores con `tipo_usuario='MONITOR'`
- Horarios Fijos asignados a los monitores
- Asistencias registradas (opcional, para datos reales)

## 🔐 2. Autenticación

Todos los endpoints requieren autenticación JWT:

**Headers requeridos en todas las peticiones:**
```
Authorization: Bearer <tu_token_jwt>
Content-Type: application/json
```

## 📊 3. Endpoints Disponibles

### A. Reporte Individual de Monitor
**GET** `/example/directivo/finanzas/monitor/{monitor_id}/`

**Parámetros opcionales:**
- `fecha_inicio`: YYYY-MM-DD (por defecto: 30 días atrás)
- `fecha_fin`: YYYY-MM-DD (por defecto: hoy)
- `semanas_trabajadas`: número (por defecto: 8)

**Ejemplos de uso:**
```bash
# Reporte del monitor ID 3 del último mes
GET /example/directivo/finanzas/monitor/3/

# Reporte de enero 2024 con 10 semanas trabajadas
GET /example/directivo/finanzas/monitor/3/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31&semanas_trabajadas=10
```

**¿Qué obtienes?**
- Información del monitor
- Horarios semanales (horas por semana, jornadas)
- Finanzas actuales (horas trabajadas, costos)
- Proyección del semestre completo
- Estadísticas detalladas

### B. Reporte Consolidado de Todos los Monitores
**GET** `/example/directivo/finanzas/todos-monitores/`

**Parámetros opcionales:**
- `fecha_inicio`: YYYY-MM-DD
- `fecha_fin`: YYYY-MM-DD
- `semanas_trabajadas`: número

**¿Qué obtienes?**
- Estadísticas generales del sistema
- Resumen financiero con comparativas
- Lista de todos los monitores ordenados por costo
- Métricas de eficiencia

### C. Resumen Ejecutivo (Dashboard)
**GET** `/example/directivo/finanzas/resumen-ejecutivo/`

**¿Qué obtienes?**
- Métricas principales del sistema
- Indicadores financieros clave
- Top 5 monitores por costo
- Alertas automáticas
- Resumen semanal

### D. Comparativa por Semanas
**GET** `/example/directivo/finanzas/comparativa-semanas/`

**¿Qué obtienes?**
- Evolución financiera semana a semana
- Proyección de costos por semana
- Análisis de tendencias temporales
- Totales acumulados

### E. Gestión de Configuraciones
```bash
# Listar configuraciones
GET /example/directivo/configuraciones/

# Inicializar configuraciones
POST /example/directivo/configuraciones/inicializar/

# Crear nueva configuración
POST /example/directivo/configuraciones/crear/

# Ver/editar configuración específica
GET /example/directivo/configuraciones/{clave}/
PUT /example/directivo/configuraciones/{clave}/
DELETE /example/directivo/configuraciones/{clave}/
```

## 💡 4. Casos de Uso Prácticos

### A. Control Presupuestario Diario
```bash
# Ver resumen ejecutivo para monitorear gastos
GET /example/directivo/finanzas/resumen-ejecutivo/
```

### B. Análisis de Monitor Específico
```bash
# Analizar el rendimiento de un monitor
GET /example/directivo/finanzas/monitor/3/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
```

### C. Planificación Semestral
```bash
# Ver proyección completa del semestre
GET /example/directivo/finanzas/comparativa-semanas/
```

### D. Identificar Monitores Costosos
```bash
# Ver todos los monitores ordenados por costo
GET /example/directivo/finanzas/todos-monitores/
```

## 📈 5. Interpretación de Datos

### Métricas Clave:
- **Costo por hora**: 9,965 COP (configurable)
- **Horas semanales**: Basadas en horarios fijos
- **Costo total**: `horas_trabajadas × costo_por_hora`
- **Proyección**: Basada en horarios fijos × semanas

### Alertas Automáticas:
- Presupuesto ejecutado >80%
- Baja actividad de monitores
- Diferencias significativas entre proyección y realidad

## ⚙️ 6. Configuración Avanzada

### A. Cambiar Costo por Hora
```json
PUT /example/directivo/configuraciones/costo_por_hora/
{
    "valor": "10000",
    "descripcion": "Nuevo costo por hora actualizado"
}
```

### B. Ajustar Semanas del Semestre
```json
PUT /example/directivo/configuraciones/semanas_semestre/
{
    "valor": "16",
    "descripcion": "Semestre de 16 semanas"
}
```

## 🎯 7. Flujo de Trabajo Recomendado

1. **Configuración Inicial**
   - Verificar configuraciones del sistema
   - Asegurar que los monitores tengan horarios asignados

2. **Monitoreo Diario**
   - Revisar resumen ejecutivo
   - Verificar alertas del sistema

3. **Análisis Semanal**
   - Revisar comparativa por semanas
   - Analizar monitores individuales si es necesario

4. **Planificación Mensual**
   - Revisar reporte consolidado
   - Ajustar configuraciones si es necesario

## ⚠️ 8. Consideraciones Importantes

- **Solo usuarios DIRECTIVO** pueden acceder a estos endpoints
- **Las configuraciones** afectan todos los cálculos
- **Los horarios fijos** son la base para las proyecciones
- **Las asistencias reales** se suman a las proyecciones
- **Los ajustes de horas** permiten correcciones manuales

## 📋 9. Estructura de Respuesta Típica

### Reporte Individual de Monitor:
```json
{
  "monitor": {
    "id": 3,
    "username": "monitor1",
    "nombre": "Juan Monitor"
  },
  "periodo_actual": {
    "fecha_inicio": "2024-01-01",
    "fecha_fin": "2024-01-31",
    "dias_trabajados": 31
  },
  "horarios_semanales": {
    "horas_por_semana": 12,
    "jornadas_por_semana": 3,
    "detalle_por_dia": {
      "Lunes": [{"jornada": "Mañana", "sede": "San Antonio"}],
      "Miércoles": [{"jornada": "Tarde", "sede": "Barcelona"}]
    }
  },
  "finanzas_actuales": {
    "horas_trabajadas": 48.0,
    "horas_asistencias": 44.0,
    "horas_ajustes": 4.0,
    "costo_total": 478320.0,
    "costo_por_hora": 9965
  },
  "proyeccion_semestre": {
    "semanas_trabajadas": 8,
    "semanas_faltantes": 8,
    "horas_totales_proyectadas": 192.0,
    "horas_trabajadas_proyectadas": 96.0,
    "costo_total_proyectado": 1913280.0,
    "costo_trabajado_proyectado": 956640.0,
    "porcentaje_completado": 50.0
  },
  "estadisticas": {
    "total_asistencias": 12,
    "total_ajustes": 1,
    "promedio_horas_por_dia": 1.55
  }
}
```

### Resumen Ejecutivo:
```json
{
  "periodo": {
    "fecha_inicio": "2024-01-01",
    "fecha_fin": "2024-01-31",
    "semanas_trabajadas": 8
  },
  "metricas_principales": {
    "total_monitores": 8,
    "monitores_activos": 6,
    "porcentaje_actividad": 75.0,
    "costo_total_actual": 3826560.0,
    "costo_total_proyectado": 7653120.0,
    "horas_totales_actuales": 384.0,
    "horas_totales_proyectadas": 768.0
  },
  "indicadores_financieros": {
    "costo_por_hora": 9965,
    "costo_promedio_por_monitor": 478320.0,
    "costo_semanal_promedio": 86352.0,
    "porcentaje_ejecutado": 50.0,
    "diferencia_presupuesto": 3826560.0
  },
  "top_monitores": {
    "por_costo": [
      {
        "monitor": {
          "id": 3,
          "nombre": "Juan Monitor",
          "username": "monitor1"
        },
        "costo_actual": 478320.0,
        "horas_trabajadas": 48.0
      }
    ]
  },
  "alertas": [
    {
      "tipo": "warning",
      "mensaje": "Se ha ejecutado el 80.5% del presupuesto proyectado"
    }
  ]
}
```

## 💻 10. Ejemplos de Implementación

### En JavaScript/Fetch:
```javascript
// Obtener resumen ejecutivo
const response = await fetch('/example/directivo/finanzas/resumen-ejecutivo/', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
console.log('Costo total actual:', data.metricas_principales.costo_total_actual);
```

### En Python/Requests:
```python
import requests

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}

# Obtener todos los monitores
response = requests.get(
    'http://localhost:8000/example/directivo/finanzas/todos-monitores/',
    headers=headers
)

data = response.json()
print(f"Total de monitores: {data['estadisticas_generales']['total_monitores']}")
```

### En cURL:
```bash
# Obtener resumen ejecutivo
curl -X GET "http://localhost:8000/example/directivo/finanzas/resumen-ejecutivo/" \
  -H "Authorization: Bearer tu_token_aqui" \
  -H "Content-Type: application/json"

# Obtener reporte de un monitor específico
curl -X GET "http://localhost:8000/example/directivo/finanzas/monitor/3/" \
  -H "Authorization: Bearer tu_token_aqui" \
  -H "Content-Type: application/json"
```

## 🔧 11. Solución de Problemas Comunes

### Error 500 - Internal Server Error
- Verificar que las migraciones estén aplicadas
- Comprobar que existan usuarios DIRECTIVO
- Verificar que las configuraciones estén inicializadas

### Error 401 - Unauthorized
- Verificar que el token JWT sea válido
- Comprobar que el usuario sea de tipo DIRECTIVO
- Verificar el formato del header Authorization

### Error 403 - Forbidden
- Asegurar que exista al menos un usuario DIRECTIVO
- Verificar que el token corresponda a un usuario válido

### Datos vacíos en reportes
- Verificar que los monitores tengan horarios asignados
- Comprobar que existan asistencias registradas
- Revisar los filtros de fecha aplicados

## 📚 12. Referencias Técnicas

### Modelos de Base de Datos:
- `UsuarioPersonalizado`: Usuarios del sistema (MONITOR/DIRECTIVO)
- `HorarioFijo`: Horarios asignados a los monitores
- `Asistencia`: Registro de asistencias reales
- `AjusteHoras`: Ajustes manuales de horas
- `ConfiguracionSistema`: Configuraciones del sistema

### Funciones de Cálculo:
- `calcular_horas_totales_monitor()`: Calcula horas totales (asistencias + ajustes)
- `calcular_costo_total_monitor()`: Calcula costo total basado en horas
- `calcular_horas_semanales_monitor()`: Calcula horas semanales basadas en horarios
- `calcular_costo_proyectado_monitor()`: Calcula proyecciones del semestre

### Configuraciones por Defecto:
- `costo_por_hora`: 9,965 COP
- `semanas_semestre`: 14 semanas

---

**¡Con esta guía tienes todo lo necesario para implementar y usar el módulo de finanzas en tu aplicación!** 🚀
