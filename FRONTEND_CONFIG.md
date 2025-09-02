# 🔗 Configuración del Frontend

## 📡 URLs del API Backend

### Desarrollo Local
```
Base URL: http://localhost:8000/example/
```

### Producción (si tienes el backend desplegado)
```
Base URL: https://tu-backend-url.vercel.app/example/
```

## 🔐 Endpoints Disponibles

### Autenticación
```javascript
// Login
POST /example/login/
{
  "nombre_de_usuario": "string",
  "password": "string"
}

// Registro
POST /example/registro/
{
  "username": "string",
  "nombre": "string", 
  "password": "string",
  "confirm_password": "string"
}

// Usuario actual
GET /example/usuario/actual/
Headers: { Authorization: "Bearer <token>" }
```

### Horarios
```javascript
// Obtener horarios
GET /example/horarios/
Headers: { Authorization: "Bearer <token>" }

// Crear horario
POST /example/horarios/
Headers: { Authorization: "Bearer <token>" }
{
  "dia_semana": 0-6,  // 0=Lunes, 6=Domingo
  "jornada": "M|T",   // M=Mañana, T=Tarde
  "sede": "SA|BA"     // SA=San Antonio, BA=Barcelona
}

// Crear múltiples horarios
POST /example/horarios/multiple/
Headers: { Authorization: "Bearer <token>" }
{
  "horarios": [
    {
      "dia_semana": 0,
      "jornada": "M",
      "sede": "SA"
    },
    {
      "dia_semana": 1,
      "jornada": "T", 
      "sede": "BA"
    }
  ]
}

// Reemplazar todos los horarios
POST /example/horarios/edit-multiple/
Headers: { Authorization: "Bearer <token>" }
{
  "horarios": [
    // Nuevos horarios que reemplazarán TODOS los existentes
  ]
}

// Horario específico
GET|PUT|DELETE /example/horarios/{id}/
Headers: { Authorization: "Bearer <token>" }
```

### Endpoints para Directivos
```javascript
// Listar horarios de todos los monitores (solo DIRECTIVOS)
GET /example/directivo/horarios/
Headers: { Authorization: "Bearer <token>" }

// Con filtros opcionales:
GET /example/directivo/horarios/?usuario_id=5
GET /example/directivo/horarios/?dia_semana=0
GET /example/directivo/horarios/?jornada=M&sede=SA

// Respuesta:
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
    }
  ]
}
```

## 🌐 Configuración CORS

El backend ya está configurado para aceptar peticiones desde:
- ✅ `https://monitoria-front-jaime.vercel.app`
- ✅ `http://localhost:3000` (desarrollo local)
- ✅ `http://localhost:8080` (Vue/Nuxt desarrollo)

## 📝 Ejemplo de Configuración en Frontend

### React/Next.js
```javascript
// config/api.js
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? 'https://tu-backend-url.vercel.app/example'
  : 'http://localhost:8000/example';

export const API_ENDPOINTS = {
  login: `${API_BASE_URL}/login/`,
  registro: `${API_BASE_URL}/registro/`,
  usuario: `${API_BASE_URL}/usuario/actual/`,
  horarios: `${API_BASE_URL}/horarios/`,
  horariosMultiple: `${API_BASE_URL}/horarios/multiple/`,
  horariosEditMultiple: `${API_BASE_URL}/horarios/edit-multiple/`,
};

// Función helper para headers
export const getAuthHeaders = (token) => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${token}`
});
```

### Vue/Nuxt.js
```javascript
// plugins/api.js
export default {
  baseURL: process.env.NODE_ENV === 'production' 
    ? 'https://tu-backend-url.vercel.app/example'
    : 'http://localhost:8000/example',
    
  endpoints: {
    login: '/login/',
    registro: '/registro/',
    usuario: '/usuario/actual/',
    horarios: '/horarios/',
    horariosMultiple: '/horarios/multiple/',
    horariosEditMultiple: '/horarios/edit-multiple/',
  }
};
```

## 🧪 Probar la Conexión

### Desde el Frontend (JavaScript)
```javascript
// Probar login
const testLogin = async () => {
  try {
    const response = await fetch('http://localhost:8000/example/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        nombre_de_usuario: 'superusuario',
        password: 'lolandia1'
      })
    });
    
    const data = await response.json();
    console.log('Login exitoso:', data);
    
    // Guardar token para futuras peticiones
    localStorage.setItem('token', data.token);
    
  } catch (error) {
    console.error('Error en login:', error);
  }
};

// Probar endpoint protegido
const testProtectedEndpoint = async () => {
  const token = localStorage.getItem('token');
  
  try {
    const response = await fetch('http://localhost:8000/example/horarios/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    console.log('Horarios:', data);
    
  } catch (error) {
    console.error('Error al obtener horarios:', error);
  }
};
```

## 🔒 Tipos de Usuario

- **DIRECTIVO**: Acceso completo (creado manualmente)
- **MONITOR**: Acceso estándar (se asigna automáticamente al registrarse)

El campo `tipo_usuario` viene en la respuesta del login/registro:
```json
{
  "usuario": {
    "id": 1,
    "username": "usuario",
    "nombre": "Usuario",
    "tipo_usuario": "MONITOR",
    "tipo_usuario_display": "Monitor"
  }
}
```
