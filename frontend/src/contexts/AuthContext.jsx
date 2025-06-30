import React, { createContext, useState, useEffect, useContext } from 'react';
import axios from 'axios';
import { safeErrorMessage } from '../utils/errorUtils';

// Crear contexto
const AuthContext = createContext();

// Proveedor del contexto
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Verificar si hay un token guardado al cargar la aplicación
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      
      if (token) {
        try {
          // Configurar el token en los headers de axios
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
          
          // Verificar si el token es válido
          const response = await axios.get('/auth/me');
          setUser(response.data);
        } catch (error) {
          console.error('Error al verificar autenticación:', error);
          // Si hay un error, limpiar el almacenamiento
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          delete axios.defaults.headers.common['Authorization'];
        }
      }
      
      setLoading(false);
    };

    checkAuth();
  }, []);

  // Función para iniciar sesión
  const login = async (username, password) => {
    setError(null);
    try {
      const response = await axios.post('/auth/login', {
        username,
        password
      }, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      // Guardar token en localStorage
      localStorage.setItem('token', response.data.access_token);
      
      // Configurar el token en los headers de axios
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
      
      // Actualizar estado
      setUser(response.data.user);
      
      return response.data;
    } catch (error) {
      console.error('Error de login:', error);
      const errorMessage = safeErrorMessage(error.response?.data?.detail || error.response?.data || 'Error al iniciar sesión');
      setError(errorMessage);
      throw error;
    }
  };

  // Función para cerrar sesión
  const logout = async () => {
    try {
      // Llamar al endpoint de logout si existe
      if (user) {
        await axios.post('/auth/logout');
      }
    } catch (error) {
      console.error('Error al cerrar sesión:', error);
    } finally {
      // Limpiar almacenamiento y estado
      localStorage.removeItem('token');
      delete axios.defaults.headers.common['Authorization'];
      setUser(null);
    }
  };

  // Verificar si el usuario tiene un permiso específico
  const hasPermission = (permission) => {
    return user?.permissions?.includes(permission) || false;
  };

  // Valor del contexto
  const value = {
    user,
    loading,
    error,
    login,
    logout,
    hasPermission,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook personalizado para usar el contexto
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider');
  }
  return context;
};

export default AuthContext;