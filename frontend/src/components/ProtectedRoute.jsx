import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children, requiredPermission = null }) => {
  const { isAuthenticated, loading, hasPermission } = useAuth();
  const location = useLocation();

  // Mostrar un indicador de carga mientras se verifica la autenticación
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Redirigir a login si no está autenticado
  if (!isAuthenticated) {
    // Guardar la ubicación actual para redirigir después del login
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Verificar permisos si se requiere
  if (requiredPermission && !hasPermission(requiredPermission)) {
    return <Navigate to="/unauthorized" replace />;
  }

  // Si está autenticado y tiene los permisos necesarios, mostrar el contenido
  return children;
};

export default ProtectedRoute;