import React from 'react';
import { useConfig } from '../contexts/ConfigContext';
import { MODULE_CONFIG, getEnabledModules } from '../core/config/moduleConfig';
import { usePermissions } from '../core/auth/permissions';
import { useAuth } from '../contexts/AuthContext';
import ModuleIcon from '../shared/components/ModuleIcon';

const Home = ({ onModuleSelect }) => {
  const { config } = useConfig();
  const { user, logout } = useAuth();
  const permissions = usePermissions(); // Por ahora usa ADMIN por defecto
  
  // Obtener módulos desde configuración central
  const allModules = Object.values(MODULE_CONFIG);
  
  // Filtrar módulos según permisos del usuario
  const availableModules = allModules.filter(module => 
    permissions.canAccessModule(module.id)
  );

  const getColorClasses = (color, disabled = false) => {
    if (disabled) {
      return config.darkMode 
        ? 'bg-gray-700 border-gray-600 text-gray-500 cursor-not-allowed'
        : 'bg-gray-100 border-gray-200 text-gray-400 cursor-not-allowed';
    }

    const colors = {
      blue: config.darkMode 
        ? 'bg-blue-900 border-blue-700 text-blue-200 hover:bg-blue-800'
        : 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100',
      green: config.darkMode 
        ? 'bg-green-900 border-green-700 text-green-200 hover:bg-green-800'
        : 'bg-green-50 border-green-200 text-green-700 hover:bg-green-100',
      purple: config.darkMode 
        ? 'bg-purple-900 border-purple-700 text-purple-200 hover:bg-purple-800'
        : 'bg-purple-50 border-purple-200 text-purple-700 hover:bg-purple-100'
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className={`min-h-screen transition-colors duration-200 ${
      config.darkMode ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="flex justify-between items-center mb-12">
          {/* Logo y título del sistema */}
          <div className="flex items-center space-x-3">
            <img 
              src="/logo-santi-ice.png" 
              alt="Santi ICE Logo" 
              className="h-12 w-auto"
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <h1 className={`text-xl font-bold ${
              config.darkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Sistema SICE
            </h1>
          </div>
          
          {/* Controles de usuario */}
          <div className="flex items-center space-x-3">
            <span className={`text-sm ${
              config.darkMode ? 'text-gray-300' : 'text-gray-600'
            }`}>
              Bienvenido, {user?.username}
            </span>
            
            {/* Botón modo oscuro */}
            <button
              onClick={() => config.toggleDarkMode()}
              className={`p-2 rounded-lg transition-colors ${
                config.darkMode 
                  ? 'hover:bg-gray-800 text-gray-300 hover:text-white' 
                  : 'hover:bg-gray-200 text-gray-600 hover:text-gray-900'
              }`}
              title={config.darkMode ? 'Modo claro' : 'Modo oscuro'}
            >
              {config.darkMode ? (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              ) : (
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
                </svg>
              )}
            </button>
          </div>
        </div>
        
        {/* Contenido principal */}
        <div className="text-center mb-8">
          <p className={`text-lg font-medium ${
            config.darkMode ? 'text-gray-300' : 'text-gray-700'
          }`}>
            Selecciona un módulo para comenzar
          </p>
        </div>

        {/* Módulos Grid */}
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {availableModules.map((module) => (
              <button
                key={module.id}
                onClick={() => module.enabled && onModuleSelect(module.id)}
                disabled={!module.enabled}
                className={`relative p-6 rounded-xl border-2 transition-all duration-200 transform hover:scale-105 ${
                  getColorClasses(module.color, !module.enabled)
                } ${module.enabled ? 'hover:shadow-lg' : ''}`}
              >
                {/* Icono */}
                <div className="flex justify-center mb-4">
                  <div className={`p-3 rounded-full ${
                    !module.enabled 
                      ? config.darkMode ? 'bg-gray-600' : 'bg-gray-200'
                      : config.darkMode ? 'bg-gray-700' : 'bg-white'
                  }`}>
                    <ModuleIcon icon={module.icon} />
                  </div>
                </div>

                {/* Contenido */}
                <div className="text-center">
                  <h3 className="text-lg font-semibold mb-2">
                    {module.name}
                  </h3>
                  <p className={`text-sm ${
                    !module.enabled 
                      ? config.darkMode ? 'text-gray-500' : 'text-gray-400'
                      : config.darkMode ? 'text-gray-300' : 'text-gray-600'
                  }`}>
                    {module.description}
                  </p>
                </div>

                {/* Badge "Próximamente" */}
                {!module.enabled && (
                  <div className="absolute top-2 right-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      config.darkMode 
                        ? 'bg-gray-600 text-gray-300' 
                        : 'bg-gray-200 text-gray-500'
                    }`}>
                      Próximamente
                    </span>
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Footer Info */}
        <div className="text-center mt-12">
          <p className={`text-sm ${
            config.darkMode ? 'text-gray-500' : 'text-gray-400'
          }`}>
            Todos los derechos reservados ® 2025 SantiICE & AF Consulting
          </p>
        </div>
        
        {/* Botón de cerrar sesión flotante */}
        <button
          onClick={logout}
          className={`fixed bottom-6 right-6 px-4 py-2 text-sm rounded-full shadow-lg transition-colors z-50 ${
            config.darkMode 
              ? 'bg-red-600 hover:bg-red-700 text-white' 
              : 'bg-red-500 hover:bg-red-600 text-white'
          }`}
          title="Cerrar Sesión"
        >
          Cerrar Sesión
        </button>
      </div>
    </div>
  );
};

export default Home;