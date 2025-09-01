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
