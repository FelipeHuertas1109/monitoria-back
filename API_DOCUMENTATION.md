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

**Descripción:** Genera un reporte detallado de las horas trabajadas por un monitor específico en un período determinado.

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
    "total_horas": 64.0,
    "total_asistencias": 16,
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
  }
}
```

### Reporte de Horas de Todos los Monitores
**GET** `/example/directivo/reportes/horas-todos/`

**Descripción:** Genera un reporte consolidado de las horas trabajadas por todos los monitores en un período determinado.

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
      "total_horas": 64.0,
      "total_asistencias": 16,
      "asistencias_presentes": 14,
      "asistencias_autorizadas": 15,
      "asistencias": [...]
    },
    {
      "monitor": {
        "id": 4,
        "username": "monitor2",
        "nombre": "María Monitor"
      },
      "total_horas": 48.0,
      "total_asistencias": 12,
      "asistencias_presentes": 12,
      "asistencias_autorizadas": 12,
      "asistencias": [...]
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

---

## 📝 Notas Importantes

- **Tokens JWT**: No expiran (configurados para 100 años)
- **Autenticación**: Todos los endpoints excepto login requieren token
- **Permisos**: Los usuarios solo pueden acceder a sus propios datos
- **Validaciones**: Los horarios fijos son únicos por usuario, día, jornada
- **Asistencias**: Únicas por usuario, fecha y horario
