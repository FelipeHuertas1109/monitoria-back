# 📚 Documentación de la API - Sistema de Monitoreo

## 🔐 Autenticación

### Login de Usuario
**POST** `/example/login/`

**Body:**
```json
{
  "password": "Admin#1234",
  "nombre_de_usuario": "superusuario"
}
```

**Respuesta Exitosa (200):**
```json
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "usuario": {
    "id": 1,
    "username": "superusuario",
    "nombre": "superusuario",
    "tipo_usuario": "DIRECTIVO",
    "tipo_usuario_display": "Directivo"
  }
}
```

### Registro de Usuario
**POST** `/example/registro/`

**Descripción:** Crea un nuevo usuario con tipo MONITOR automáticamente. Los usuarios no pueden elegir su tipo.

**Body:**
```json
{
  "username": "nuevo_usuario",
  "nombre": "Usuario Nuevo",
  "password": "password123",
  "confirm_password": "password123"
}
```

**Validaciones:**
- `username`: Único, requerido
- `nombre`: Requerido
- `password`: Mínimo 6 caracteres, requerido
- `confirm_password`: Debe coincidir con password

**Respuesta Exitosa (201):**
```json
{
  "mensaje": "Usuario registrado exitosamente",
  "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "usuario": {
    "id": 3,
    "username": "nuevo_usuario",
    "nombre": "Usuario Nuevo",
    "tipo_usuario": "MONITOR",
    "tipo_usuario_display": "Monitor"
  }
}
```

**Respuesta de Error (400):**
```json
{
  "username": ["Este nombre de usuario ya está en uso."]
}
```

**O:**
```json
{
  "non_field_errors": ["Las contraseñas no coinciden."]
}
```

**O:**
```json
{
  "password": ["Ensure this field has at least 6 characters."]
}
```

**Headers para endpoints protegidos:**
```
Authorization: Bearer <token>
```

---

## 👤 Usuarios

### Obtener Usuario Actual
**GET** `/example/usuario/`

**Headers:** `Authorization: Bearer <token>`

**Respuesta (200):**
```json
{
  "id": 1,
  "username": "superusuario",
  "nombre": "superusuario"
}
```

---

## 🕐 Horarios Fijos

### Listar Horarios del Usuario
**GET** `/example/horarios/`

**Headers:** `Authorization: Bearer <token>`

**Respuesta (200):**
```json
[
  {
    "id": 1,
    "usuario": {
      "id": 1,
      "username": "superusuario",
      "nombre": "superusuario"
    },
    "dia_semana": 0,
    "dia_semana_display": "Lunes",
    "jornada": "M",
    "jornada_display": "Mañana",
    "sede": "SA",
    "sede_display": "San Antonio"
  }
]
```

### Crear Horario Fijo
**POST** `/example/horarios/`

**Headers:** `Authorization: Bearer <token>`

**Body:**
```json
{
  "dia_semana": 0,
  "jornada": "M",
  "sede": "SA"
}
```

**Respuesta (201):**
```json
{
  "dia_semana": 0,
  "jornada": "M",
  "sede": "SA"
}
```

### Obtener Horario Específico
**GET** `/example/horarios/{id}/`

**Headers:** `Authorization: Bearer <token>`

### Actualizar Horario
**PUT** `/example/horarios/{id}/`

**Headers:** `Authorization: Bearer <token>`

**Body:** Igual que crear

### Eliminar Horario
**DELETE** `/example/horarios/{id}/`

**Headers:** `Authorization: Bearer <token>`

---

## ✅ Asistencias

### Listar Asistencias del Usuario
**GET** `/example/asistencias/`

**Headers:** `Authorization: Bearer <token>`

**Respuesta (200):**
```json
[
  {
    "id": 1,
    "usuario": {
      "id": 1,
      "username": "superusuario",
      "nombre": "superusuario"
    },
    "fecha": "2024-01-15",
    "horario": {
      "id": 1,
      "usuario": {...},
      "dia_semana": 0,
      "dia_semana_display": "Lunes",
      "jornada": "M",
      "jornada_display": "Mañana",
      "sede": "SA",
      "sede_display": "San Antonio"
    },
    "presente": true
  }
]
```

### Crear Asistencia
**POST** `/example/asistencias/`

**Headers:** `Authorization: Bearer <token>`

**Body:**
```json
{
  "fecha": "2024-01-15",
  "horario": 1,
  "presente": true
}
```

**Respuesta (201):**
```json
{
  "fecha": "2024-01-15",
  "horario": 1,
  "presente": true
}
```

### Obtener Asistencia Específica
**GET** `/example/asistencias/{id}/`

**Headers:** `Authorization: Bearer <token>`

### Actualizar Asistencia
**PUT** `/example/asistencias/{id}/`

**Headers:** `Authorization: Bearer <token>`

**Body:** Igual que crear

### Eliminar Asistencia
**DELETE** `/example/asistencias/{id}/`

**Headers:** `Authorization: Bearer <token>`

---

## 👥 Endpoints para Directivos

### Listar Horarios de Todos los Monitores
**GET** `/example/directivo/horarios/`

**Descripción:** Permite a los directivos ver todos los horarios fijos de todos los monitores del sistema con filtros opcionales.

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

**Parámetros de consulta (opcionales):**
- `usuario_id`: ID específico del monitor (número entero)
- `dia_semana`: Día de la semana (0-6, donde 0=Lunes)
- `jornada`: Jornada (M=Mañana, T=Tarde)
- `sede`: Sede (SA=San Antonio, BA=Barcelona)

**Ejemplos de uso:**
```bash
# Todos los horarios de todos los monitores
GET /example/directivo/horarios/

# Horarios de un monitor específico
GET /example/directivo/horarios/?usuario_id=5

# Horarios de los lunes
GET /example/directivo/horarios/?dia_semana=0

# Horarios de mañana en San Antonio
GET /example/directivo/horarios/?jornada=M&sede=SA
```

**Respuesta Exitosa (200):**
```json
{
  "total_horarios": 15,
  "total_monitores": 8,
  "horarios": [
    {
      "id": 1,
      "usuario": {
        "id": 3,
        "username": "monitor1",
        "nombre": "Juan Monitor"
      },
      "dia_semana": 0,
      "dia_semana_display": "Lunes",
      "jornada": "M",
      "jornada_display": "Mañana",
      "sede": "SA",
      "sede_display": "San Antonio"
    },
    {
      "id": 2,
      "usuario": {
        "id": 3,
        "username": "monitor1", 
        "nombre": "Juan Monitor"
      },
      "dia_semana": 2,
      "dia_semana_display": "Miércoles",
      "jornada": "T",
      "jornada_display": "Tarde",
      "sede": "BA",
      "sede_display": "Barcelona"
    }
  ]
}
```

**Respuesta de Error (400):**
```json
{
  "detail": "dia_semana debe ser entre 0-6"
}
```

**Respuesta de Error (401):**
```json
{
  "detail": "Token de autenticación requerido"
}
```

**Respuesta de Error (403):**
```json
{
  "detail": "No hay usuarios DIRECTIVO"
}
```

---

## 📈 Endpoints para Reportes

### Reporte de Horas por Monitor Individual
**GET** `/example/directivo/reportes/horas-monitor/{monitor_id}/`

**Descripción:** Genera un reporte detallado de las horas trabajadas por un monitor específico en un período determinado. **Incluye tanto horas de asistencias como ajustes manuales de horas.**

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

**Parámetros de consulta (opcionales):**
- `fecha_inicio`: Fecha de inicio del reporte (YYYY-MM-DD). Por defecto: 30 días atrás
- `fecha_fin`: Fecha de fin del reporte (YYYY-MM-DD). Por defecto: hoy
- `sede`: Filtrar por sede (SA=San Antonio, BA=Barcelona)
- `jornada`: Filtrar por jornada (M=Mañana, T=Tarde)

**Ejemplos de uso:**
```bash
# Reporte del último mes para el monitor ID 3
GET /example/directivo/reportes/horas-monitor/3/

# Reporte de enero 2024 para el monitor ID 3
GET /example/directivo/reportes/horas-monitor/3/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31

# Reporte solo de mañana en San Antonio
GET /example/directivo/reportes/horas-monitor/3/?jornada=M&sede=SA
```

**Respuesta Exitosa (200):**
```json
{
  "monitor": {
    "id": 3,
    "username": "monitor1",
    "nombre": "Juan Monitor"
  },
  "periodo": {
    "fecha_inicio": "2024-01-01",
    "fecha_fin": "2024-01-31"
  },
  "estadisticas": {
    "horas_asistencias": 60.0,
    "horas_ajustes": 4.0,
    "total_horas": 64.0,
    "total_asistencias": 16,
    "total_ajustes": 1,
    "asistencias_presentes": 14,
    "asistencias_autorizadas": 15,
    "promedio_horas_por_dia": 2.06
  },
  "filtros_aplicados": {
    "sede": "SA",
    "jornada": "M"
  },
  "detalle_por_fecha": {
    "2024-01-15": [
      {
        "id": 1,
        "usuario": {...},
        "fecha": "2024-01-15",
        "horario": {...},
        "presente": true,
        "estado_autorizacion": "autorizado",
        "estado_autorizacion_display": "Autorizado",
        "horas": 4.00
      }
    ]
  },
  "ajustes_por_fecha": {
    "2024-01-16": [
      {
        "id": 1,
        "usuario": {...},
        "fecha": "2024-01-16",
        "cantidad_horas": 4.00,
        "motivo": "Recuperación por día perdido",
        "asistencia": null,
        "creado_por": {...},
        "created_at": "2024-01-16T09:00:00Z"
      }
    ]
  }
}
```

### Reporte de Horas de Todos los Monitores
**GET** `/example/directivo/reportes/horas-todos/`

**Descripción:** Genera un reporte consolidado de las horas trabajadas por todos los monitores en un período determinado. **Incluye tanto horas de asistencias como ajustes manuales de horas.**

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

**Parámetros de consulta (opcionales):**
- `fecha_inicio`: Fecha de inicio del reporte (YYYY-MM-DD). Por defecto: 30 días atrás
- `fecha_fin`: Fecha de fin del reporte (YYYY-MM-DD). Por defecto: hoy
- `sede`: Filtrar por sede (SA=San Antonio, BA=Barcelona)
- `jornada`: Filtrar por jornada (M=Mañana, T=Tarde)

**Ejemplos de uso:**
```bash
# Reporte del último mes para todos los monitores
GET /example/directivo/reportes/horas-todos/

# Reporte de enero 2024 para todos los monitores
GET /example/directivo/reportes/horas-todos/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31

# Reporte solo de mañana en San Antonio
GET /example/directivo/reportes/horas-todos/?jornada=M&sede=SA
```

**Respuesta Exitosa (200):**
```json
{
  "periodo": {
    "fecha_inicio": "2024-01-01",
    "fecha_fin": "2024-01-31"
  },
  "estadisticas_generales": {
    "total_horas": 256.0,
    "total_asistencias": 64,
    "total_ajustes": 8,
    "total_monitores": 8,
    "promedio_horas_por_monitor": 32.0
  },
  "filtros_aplicados": {
    "sede": "SA",
    "jornada": "M"
  },
  "monitores": [
    {
      "monitor": {
        "id": 3,
        "username": "monitor1",
        "nombre": "Juan Monitor"
      },
      "horas_asistencias": 60.0,
      "horas_ajustes": 4.0,
      "total_horas": 64.0,
      "total_asistencias": 16,
      "total_ajustes": 1,
      "asistencias_presentes": 14,
      "asistencias_autorizadas": 15,
      "asistencias": [...],
      "ajustes": [...]
    },
    {
      "monitor": {
        "id": 4,
        "username": "monitor2",
        "nombre": "María Monitor"
      },
      "horas_asistencias": 48.0,
      "horas_ajustes": 0.0,
      "total_horas": 48.0,
      "total_asistencias": 12,
      "total_ajustes": 0,
      "asistencias_presentes": 12,
      "asistencias_autorizadas": 12,
      "asistencias": [...],
      "ajustes": []
    }
  ]
}
```

**Respuesta de Error (404):**
```json
{
  "detail": "Monitor no encontrado"
}
```

---

## 👨‍💼 Endpoints para Monitores

### Marcar Asistencia
**POST** `/example/monitor/marcar/`

**Headers:** `Authorization: Bearer <token>`

**Body:**
```json
{
  "fecha": "2024-01-15",
  "jornada": "M"
}
```

**Descripción:** Los monitores pueden marcar asistencia **durante todo el día** si la asistencia está autorizada por un directivo. No hay restricciones de horario - pueden marcar la jornada de mañana a las 5 PM si está autorizada.

**Validaciones:**
- El usuario debe ser de tipo MONITOR
- Debe tener horario asignado para esa jornada
- La asistencia debe estar autorizada por un directivo

**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "usuario": {
    "id": 3,
    "username": "monitor1",
    "nombre": "Juan Monitor"
  },
  "fecha": "2024-01-15",
  "horario": {
    "id": 1,
    "dia_semana": 0,
    "dia_semana_display": "Lunes",
    "jornada": "M",
    "jornada_display": "Mañana",
    "sede": "SA",
    "sede_display": "San Antonio"
  },
  "presente": true,
  "estado_autorizacion": "autorizado",
  "estado_autorizacion_display": "Autorizado",
  "horas": 4.00
}
```

**Respuesta de Error (400):**
```json
{
  "detail": "Jornada inválida"
}
```

**Respuesta de Error (403):**
```json
{
  "detail": "Solo monitores pueden marcar asistencia"
}
```

**O:**
```json
{
  "detail": "Este bloque aún no ha sido autorizado por un directivo.",
  "code": "not_authorized"
}
```

**O:**
```json
{
  "detail": "No tienes horario asignado para esa jornada hoy"
}
```

### Mis Asistencias
**GET** `/example/monitor/mis-asistencias/`

**Headers:** `Authorization: Bearer <token>`

**Parámetros de consulta (opcionales):**
- `fecha`: Fecha específica (YYYY-MM-DD). Por defecto: hoy

**Descripción:** Lista las asistencias del monitor para una fecha específica. Genera automáticamente las asistencias faltantes basadas en los horarios fijos.

**Respuesta Exitosa (200):**
```json
[
  {
    "id": 1,
    "usuario": {...},
    "fecha": "2024-01-15",
    "horario": {...},
    "presente": false,
    "estado_autorizacion": "pendiente",
    "estado_autorizacion_display": "Pendiente",
    "horas": 0.00
  }
]
```

---

## 🔧 Endpoints para Ajustes de Horas

### Listar y Crear Ajustes de Horas
**GET/POST** `/example/directivo/ajustes-horas/`

**Descripción:** Permite a los directivos listar ajustes de horas existentes y crear nuevos ajustes para dar o quitar horas a monitores.

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

#### GET - Listar Ajustes
**Parámetros de consulta (opcionales):**
- `monitor_id`: ID específico del monitor (número entero)
- `fecha_inicio`: Fecha de inicio del filtro (YYYY-MM-DD). Por defecto: 30 días atrás
- `fecha_fin`: Fecha de fin del filtro (YYYY-MM-DD). Por defecto: hoy

**Ejemplos de uso:**
```bash
# Todos los ajustes del último mes
GET /example/directivo/ajustes-horas/

# Ajustes de un monitor específico
GET /example/directivo/ajustes-horas/?monitor_id=3

# Ajustes en un período específico
GET /example/directivo/ajustes-horas/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
```

**Respuesta Exitosa (200):**
```json
{
  "periodo": {
    "fecha_inicio": "2024-01-01",
    "fecha_fin": "2024-01-31"
  },
  "estadisticas": {
    "total_ajustes": 5,
    "total_horas_ajustadas": 12.5,
    "monitores_afectados": 3
  },
  "filtros_aplicados": {
    "monitor_id": null
  },
  "ajustes": [
    {
      "id": 1,
      "usuario": {
        "id": 3,
        "username": "monitor1",
        "nombre": "Juan Monitor"
      },
      "fecha": "2024-01-15",
      "cantidad_horas": 4.00,
      "motivo": "Recuperación por día perdido por enfermedad",
      "asistencia": null,
      "creado_por": {
        "id": 1,
        "username": "directivo1",
        "nombre": "María Directivo"
      },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

#### POST - Crear Ajuste
**Body:**
```json
{
  "monitor_id": 3,
  "fecha": "2024-01-15",
  "cantidad_horas": 4.00,
  "motivo": "Recuperación por día perdido por enfermedad",
  "asistencia_id": 25
}
```

**Campos:**
- `monitor_id`: (requerido) ID del monitor al que se le ajustan las horas
- `fecha`: (requerido) Fecha del ajuste en formato YYYY-MM-DD
- `cantidad_horas`: (requerido) Cantidad de horas (positivo para agregar, negativo para restar). Rango: -24.00 a 24.00
- `motivo`: (requerido) Descripción del motivo del ajuste
- `asistencia_id`: (opcional) ID de la asistencia relacionada si aplica

**Validaciones:**
- `monitor_id` debe existir y ser de tipo MONITOR
- `cantidad_horas` no puede ser 0 y debe estar entre -24.00 y 24.00
- Si se proporciona `asistencia_id`, debe existir y pertenecer al monitor especificado

**Respuesta Exitosa (201):**
```json
{
  "id": 1,
  "usuario": {
    "id": 3,
    "username": "monitor1",
    "nombre": "Juan Monitor"
  },
  "fecha": "2024-01-15",
  "cantidad_horas": 4.00,
  "motivo": "Recuperación por día perdido por enfermedad",
  "asistencia": {
    "id": 25,
    "fecha": "2024-01-10",
    "presente": false,
    "estado_autorizacion": "rechazado"
  },
  "creado_por": {
    "id": 1,
    "username": "directivo1",
    "nombre": "María Directivo"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Respuesta de Error (400):**
```json
{
  "cantidad_horas": ["La cantidad de horas debe estar entre -24.00 y 24.00."]
}
```

### Detalles y Eliminar Ajuste
**GET/DELETE** `/example/directivo/ajustes-horas/{id}/`

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

#### GET - Obtener Detalles
**Respuesta Exitosa (200):**
```json
{
  "id": 1,
  "usuario": {
    "id": 3,
    "username": "monitor1",
    "nombre": "Juan Monitor"
  },
  "fecha": "2024-01-15",
  "cantidad_horas": 4.00,
  "motivo": "Recuperación por día perdido por enfermedad",
  "asistencia": null,
  "creado_por": {
    "id": 1,
    "username": "directivo1",
    "nombre": "María Directivo"
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### DELETE - Eliminar Ajuste
**Descripción:** Elimina un ajuste de horas. Útil para corregir errores.

**Respuesta Exitosa (204):**
```json
{
  "detail": "Ajuste de horas eliminado exitosamente"
}
```

**Respuesta de Error (404):**
```json
{
  "detail": "Ajuste de horas no encontrado"
}
```

### Buscar Monitores
**GET** `/example/directivo/buscar-monitores/`

**Descripción:** Permite a los directivos buscar monitores por nombre o username para obtener su ID. Útil para formularios de ajustes de horas.

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

**Parámetros de consulta:**
- `q`: (requerido) Término de búsqueda (mínimo 2 caracteres)

**Ejemplos de uso:**
```bash
# Buscar monitores por nombre
GET /example/directivo/buscar-monitores/?q=juan

# Buscar por username
GET /example/directivo/buscar-monitores/?q=monitor1

# Búsqueda parcial
GET /example/directivo/buscar-monitores/?q=mar
```

**Respuesta Exitosa (200):**
```json
{
  "busqueda": "juan",
  "total_encontrados": 2,
  "monitores": [
    {
      "id": 3,
      "username": "monitor1",
      "nombre": "Juan Monitor"
    },
    {
      "id": 7,
      "username": "jperez",
      "nombre": "Juan Pérez"
    }
  ]
}
```

**Respuesta de Error (400):**
```json
{
  "detail": "Parámetro de búsqueda \"q\" es requerido"
}
```

**O:**
```json
{
  "detail": "La búsqueda debe tener al menos 2 caracteres"
}
```

**Características:**
- Búsqueda case-insensitive en nombre y username
- Máximo 20 resultados por búsqueda
- Resultados ordenados por nombre
- Solo busca usuarios de tipo MONITOR

---

## 💰 Endpoints para Finanzas

### Reporte Financiero Individual de Monitor
**GET** `/example/directivo/finanzas/monitor/{monitor_id}/`

**Descripción:** Genera un reporte financiero detallado de un monitor específico, incluyendo costos actuales, proyecciones del semestre, horas semanales y estadísticas completas.

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

**Parámetros de consulta (opcionales):**
- `fecha_inicio`: Fecha de inicio del reporte (YYYY-MM-DD). Por defecto: 30 días atrás
- `fecha_fin`: Fecha de fin del reporte (YYYY-MM-DD). Por defecto: hoy
- `semanas_trabajadas`: Número de semanas trabajadas en el semestre (0-16). Por defecto: 8

**Ejemplos de uso:**
```bash
# Reporte del último mes para el monitor ID 3
GET /example/directivo/finanzas/monitor/3/

# Reporte de enero 2024 con 10 semanas trabajadas
GET /example/directivo/finanzas/monitor/3/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31&semanas_trabajadas=10
```

**Respuesta Exitosa (200):**
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
      "Lunes": [
        {"jornada": "Mañana", "sede": "San Antonio"}
      ],
      "Miércoles": [
        {"jornada": "Tarde", "sede": "Barcelona"}
      ],
      "Viernes": [
        {"jornada": "Mañana", "sede": "San Antonio"}
      ]
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

### Reporte Financiero de Todos los Monitores
**GET** `/example/directivo/finanzas/todos-monitores/`

**Descripción:** Genera un reporte financiero consolidado de todos los monitores, incluyendo costos totales, proyecciones, comparativas y estadísticas generales.

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

**Parámetros de consulta (opcionales):**
- `fecha_inicio`: Fecha de inicio del reporte (YYYY-MM-DD). Por defecto: 30 días atrás
- `fecha_fin`: Fecha de fin del reporte (YYYY-MM-DD). Por defecto: hoy
- `semanas_trabajadas`: Número de semanas trabajadas en el semestre (0-16). Por defecto: 8

**Ejemplos de uso:**
```bash
# Reporte consolidado del último mes
GET /example/directivo/finanzas/todos-monitores/

# Reporte de enero 2024 con 10 semanas trabajadas
GET /example/directivo/finanzas/todos-monitores/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31&semanas_trabajadas=10
```

**Respuesta Exitosa (200):**
```json
{
  "periodo_actual": {
    "fecha_inicio": "2024-01-01",
    "fecha_fin": "2024-01-31",
    "dias_trabajados": 31
  },
  "semanas_trabajadas": 8,
  "estadisticas_generales": {
    "total_monitores": 8,
    "costo_total_actual": 3826560.0,
    "costo_total_proyectado": 7653120.0,
    "costo_promedio_por_monitor": 478320.0,
    "horas_totales_actuales": 384.0,
    "horas_totales_proyectadas": 768.0,
    "horas_promedio_por_monitor": 48.0,
    "costo_por_hora": 9965
  },
  "resumen_financiero": {
    "diferencia_proyeccion_vs_actual": 3826560.0,
    "porcentaje_ejecutado": 50.0,
    "costo_semanal_promedio": 86352.0
  },
  "monitores": [
    {
      "monitor": {
        "id": 3,
        "username": "monitor1",
        "nombre": "Juan Monitor"
      },
      "horarios_semanales": {
        "horas_por_semana": 12,
        "jornadas_por_semana": 3
      },
      "finanzas_actuales": {
        "horas_trabajadas": 48.0,
        "costo_total": 478320.0
      },
      "proyeccion_semestre": {
        "semanas_trabajadas": 8,
        "semanas_faltantes": 8,
        "costo_total_proyectado": 1913280.0,
        "costo_trabajado_proyectado": 956640.0,
        "porcentaje_completado": 50.0
      },
      "estadisticas": {
        "total_asistencias": 12,
        "total_ajustes": 1
      }
    }
  ]
}
```

### Resumen Ejecutivo Financiero
**GET** `/example/directivo/finanzas/resumen-ejecutivo/`

**Descripción:** Dashboard ejecutivo con métricas clave, tendencias, alertas y resumen financiero del sistema completo.

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

**Parámetros de consulta (opcionales):**
- `fecha_inicio`: Fecha de inicio del reporte (YYYY-MM-DD). Por defecto: 30 días atrás
- `fecha_fin`: Fecha de fin del reporte (YYYY-MM-DD). Por defecto: hoy
- `semanas_trabajadas`: Número de semanas trabajadas en el semestre (0-16). Por defecto: 8

**Ejemplos de uso:**
```bash
# Dashboard ejecutivo del último mes
GET /example/directivo/finanzas/resumen-ejecutivo/

# Dashboard de enero 2024
GET /example/directivo/finanzas/resumen-ejecutivo/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31
```

**Respuesta Exitosa (200):**
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
    ],
    "total_considerados": 8
  },
  "alertas": [
    {
      "tipo": "info",
      "mensaje": "Solo 6 de 8 monitores han trabajado en el período"
    }
  ],
  "resumen_semanal": {
    "costo_semanal_total": 690816.0,
    "horas_semanal_promedio": 86.71,
    "proyeccion_fin_semestre": 3826560.0
  }
}
```

### Comparativa Financiera por Semanas
**GET** `/example/directivo/finanzas/comparativa-semanas/`

**Descripción:** Muestra la evolución financiera por semanas del semestre, incluyendo costos acumulados, horas trabajadas y tendencias.

**Headers:** `Authorization: Bearer <token>` (solo DIRECTIVO)

**Ejemplos de uso:**
```bash
# Comparativa de las 16 semanas del semestre
GET /example/directivo/finanzas/comparativa-semanas/
```

**Respuesta Exitosa (200):**
```json
{
  "total_semanas": 16,
  "semanas_trabajadas": 8,
  "semanas_pendientes": 8,
  "resumen_general": {
    "costo_total_semestre": 7653120.0,
    "horas_total_semestre": 768.0,
    "costo_promedio_por_semana": 478320.0,
    "horas_promedio_por_semana": 48.0
  },
  "semanas": [
    {
      "semana": 1,
      "costo_total": 478320.0,
      "horas_total": 48.0,
      "monitores_activos": 8,
      "costo_promedio_por_monitor": 59790.0,
      "estado": "completada",
      "costo_acumulado": 478320.0,
      "horas_acumuladas": 48.0,
      "porcentaje_completado": 6.25
    },
    {
      "semana": 2,
      "costo_total": 478320.0,
      "horas_total": 48.0,
      "monitores_activos": 8,
      "costo_promedio_por_monitor": 59790.0,
      "estado": "completada",
      "costo_acumulado": 956640.0,
      "horas_acumuladas": 96.0,
      "porcentaje_completado": 12.5
    }
  ],
  "tendencias": {
    "costo_por_semana": [478320.0, 478320.0, 478320.0],
    "horas_por_semana": [48.0, 48.0, 48.0],
    "costo_acumulado": [478320.0, 956640.0, 1434960.0]
  }
}
```

**Respuesta de Error (400):**
```json
{
  "detail": "semanas_trabajadas debe estar entre 0 y 16"
}
```

**Respuesta de Error (404):**
```json
{
  "detail": "Monitor no encontrado"
}
```

**Características de los Endpoints Financieros:**
- **Costo por hora:** 9,965 COP (fijo para todos los cálculos)
- **Duración del semestre:** 16 semanas máximo
- **Cálculo de horas:** Cada jornada (M/T) = 4 horas
- **Proyecciones:** Basadas en horarios fijos de cada monitor
- **Incluye:** Asistencias + ajustes de horas manuales
- **Ordenamiento:** Monitores ordenados por costo total (descendente)

---

## 📊 Códigos de Estado

- **200 OK**: Petición exitosa
- **201 Created**: Recurso creado exitosamente
- **204 No Content**: Recurso eliminado exitosamente
- **400 Bad Request**: Error en los datos enviados
- **401 Unauthorized**: Token inválido o faltante
- **404 Not Found**: Recurso no encontrado

---

## 🔧 Valores de los Campos

### Días de la Semana
- `0`: Lunes
- `1`: Martes
- `2`: Miércoles
- `3`: Jueves
- `4`: Viernes
- `5`: Sábado
- `6`: Domingo

### Jornadas
- `"M"`: Mañana
- `"T"`: Tarde

### Sedes
- `"SA"`: San Antonio
- `"BA"`: Barcelona

---

## 🚀 Ejemplos de Uso

### 1. Login y Obtener Token
```bash
curl -X POST http://localhost:8000/example/login/ \
  -H "Content-Type: application/json" \
  -d '{"password": "Admin#1234", "nombre_de_usuario": "superusuario"}'
```

### 2. Crear Horario Fijo
```bash
curl -X POST http://localhost:8000/example/horarios/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"dia_semana": 0, "jornada": "M", "sede": "SA"}'
```

### 3. Registrar Asistencia
```bash
curl -X POST http://localhost:8000/example/asistencias/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"fecha": "2024-01-15", "horario": 1, "presente": true}'
```

### 4. Reporte Financiero Individual
```bash
curl -X GET "http://localhost:8000/example/directivo/finanzas/monitor/3/?fecha_inicio=2024-01-01&fecha_fin=2024-01-31" \
  -H "Authorization: Bearer <token>"
```

### 5. Resumen Ejecutivo Financiero
```bash
curl -X GET "http://localhost:8000/example/directivo/finanzas/resumen-ejecutivo/?semanas_trabajadas=8" \
  -H "Authorization: Bearer <token>"
```

### 6. Comparativa por Semanas
```bash
curl -X GET "http://localhost:8000/example/directivo/finanzas/comparativa-semanas/" \
  -H "Authorization: Bearer <token>"
```

---

## 📝 Notas Importantes

- **Tokens JWT**: No expiran (configurados para 100 años)
- **Autenticación**: Todos los endpoints excepto login requieren token
- **Permisos**: Los usuarios solo pueden acceder a sus propios datos
- **Validaciones**: Los horarios fijos son únicos por usuario, día, jornada
- **Asistencias**: Únicas por usuario, fecha y horario
