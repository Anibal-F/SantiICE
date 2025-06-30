# Integración de Autenticación en SantiICE OCR

Este documento explica cómo integrar el sistema de autenticación en el frontend existente de React.

## Componentes creados

1. **Login.jsx**: Componente de inicio de sesión
2. **AuthContext.jsx**: Contexto para manejar la autenticación
3. **ProtectedRoute.jsx**: Componente para proteger rutas
4. **Unauthorized.jsx**: Página para acceso denegado

## Usuarios predefinidos

- **admin / admin123**: Acceso completo (tickets, conciliador, config)
- **user / user123**: Acceso limitado (solo tickets)

## Pasos para integrar

### 1. Instalar dependencias

```bash
cd frontend
npm install http-proxy-middleware
```

### 2. Configurar el Router principal

Modifica tu archivo `App.jsx` o donde tengas definidas tus rutas:

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './components/Login';
import Unauthorized from './components/Unauthorized';
// Importa tus componentes existentes
import Dashboard from './components/Dashboard';
import TicketUpload from './components/TicketUpload';
import Conciliator from './components/Conciliator';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Ruta pública */}
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<Unauthorized />} />
          
          {/* Ruta protegida - acceso general */}
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } 
          />
          
          {/* Ruta protegida - solo con permiso "tickets" */}
          <Route 
            path="/tickets" 
            element={
              <ProtectedRoute requiredPermission="tickets">
                <TicketUpload />
              </ProtectedRoute>
            } 
          />
          
          {/* Ruta protegida - solo con permiso "conciliator" */}
          <Route 
            path="/conciliador" 
            element={
              <ProtectedRoute requiredPermission="conciliator">
                <Conciliator />
              </ProtectedRoute>
            } 
          />
          
          {/* Redirigir rutas desconocidas */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
```

### 3. Usar el contexto de autenticación en componentes

```jsx
import { useAuth } from '../contexts/AuthContext';

function MiComponente() {
  const { user, logout, hasPermission } = useAuth();
  
  return (
    <div>
      <p>Bienvenido, {user.username}</p>
      
      {/* Mostrar elementos según permisos */}
      {hasPermission('conciliator') && (
        <button>Ir a Conciliador</button>
      )}
      
      <button onClick={logout}>Cerrar Sesión</button>
    </div>
  );
}
```

### 4. Configurar Axios para incluir el token en todas las peticiones

En tu archivo principal (index.js o main.jsx):

```jsx
import axios from 'axios';

// Configurar interceptor para incluir el token en todas las peticiones
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);
```

## Endpoints de autenticación

- **POST /api/auth/login**: Iniciar sesión
  - Body: `{ username, password }`
  - Response: `{ access_token, token_type, user }`

- **GET /api/auth/me**: Obtener información del usuario actual
  - Headers: `Authorization: Bearer <token>`
  - Response: `{ username, role, permissions }`

- **POST /api/auth/logout**: Cerrar sesión
  - Headers: `Authorization: Bearer <token>`
  - Response: `{ message }`

## Permisos disponibles

- **tickets**: Acceso al módulo de subida de tickets
- **conciliator**: Acceso al módulo de conciliación
- **config**: Acceso a configuraciones y catálogos