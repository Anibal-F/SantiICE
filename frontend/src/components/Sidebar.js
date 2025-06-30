import React, { useState } from 'react';
import { useConfig } from '../contexts/ConfigContext';

const Sidebar = ({ isOpen, onToggle, onOpenCatalogManager }) => {
  const { config, updateConfig } = useConfig();
  const [activeSection, setActiveSection] = useState('general');

  const sections = [
    { id: 'general', name: 'General', icon: '⚙️' },
    { id: 'catalogs', name: 'Catálogos', icon: '📋' }
  ];

  return (
    <>
      {/* Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onToggle}
        />
      )}
      
      {/* Sidebar */}
      <div className={`fixed top-0 right-0 h-full w-80 shadow-xl transform transition-transform duration-300 ease-in-out z-50 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      } ${config.darkMode ? 'bg-gray-800 text-white' : 'bg-white'}`}>
        
        {/* Header */}
        <div className={`flex items-center justify-between p-4 border-b ${
          config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <h2 className={`text-lg font-semibold ${
            config.darkMode ? 'text-white' : 'text-gray-900'
          }`}>Configuración</h2>
          <button
            onClick={onToggle}
            className={`p-2 rounded-lg hover:bg-gray-100 ${
              config.darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
            }`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Navigation */}
        <div className={`border-b ${
          config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          {sections.map(section => (
            <button
              key={section.id}
              onClick={() => section.id === 'catalogs' ? onOpenCatalogManager() : setActiveSection(section.id)}
              className={`w-full flex items-center px-4 py-3 text-left ${
                activeSection === section.id 
                  ? config.darkMode ? 'bg-gray-700 text-blue-400' : 'bg-blue-50 text-blue-600'
                  : config.darkMode ? 'text-gray-300 hover:bg-gray-700 hover:text-white' : 'text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span className="mr-3">{section.icon}</span>
              {section.name}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className={`flex-1 overflow-y-auto p-4 max-h-[calc(100vh-200px)] ${
          config.darkMode ? 'bg-gray-800' : 'bg-white'
        }`}>
          {activeSection === 'general' && (
            <GeneralSettings config={config} updateConfig={updateConfig} />
          )}
          {activeSection === 'catalogs' && (
            <div className={`text-center py-8 ${
              config.darkMode ? 'bg-gray-800' : 'bg-white'
            }`}>
              <p className={`text-sm mb-4 ${
                config.darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Los catálogos se gestionan en una pantalla dedicada</p>
              <button
                onClick={onOpenCatalogManager}
                className="px-4 py-2 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600"
              >
                Abrir Gestión de Catálogos
              </button>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

const GeneralSettings = ({ config, updateConfig }) => (
  <div className={`space-y-6 ${
    config.darkMode ? 'bg-gray-800' : 'bg-white'
  }`}>
    <div className={`${
      config.darkMode ? 'bg-gray-800' : 'bg-white'
    }`}>
      <h3 className={`text-md font-medium mb-4 ${
        config.darkMode ? 'text-white' : 'text-gray-900'
      }`}>Configuración General</h3>
      
      {/* Modo Oscuro */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <label className={`text-sm font-medium ${
            config.darkMode ? 'text-white' : 'text-gray-900'
          }`}>Modo Oscuro</label>
          <p className={`text-xs ${
            config.darkMode ? 'text-gray-400' : 'text-gray-500'
          }`}>Cambiar tema de la aplicación</p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={config.darkMode}
            onChange={(e) => updateConfig({ darkMode: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>

      {/* Edición de baja confianza */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <label className={`text-sm font-medium ${
            config.darkMode ? 'text-white' : 'text-gray-900'
          }`}>Permitir Edición de Alta Confianza</label>
          <p className={`text-xs ${
            config.darkMode ? 'text-gray-400' : 'text-gray-500'
          }`}>Permite editar todas las cantidades independientemente de la confianza</p>
        </div>
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={config.allowHighConfidenceEdit}
            onChange={(e) => updateConfig({ allowHighConfidenceEdit: e.target.checked })}
            className="sr-only peer"
          />
          <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
        </label>
      </div>

      {/* Descripción del umbral */}
      <div className="mb-2">
        <p className={`text-xs ${
          config.darkMode ? 'text-gray-400' : 'text-gray-600'
        }`}>
          {config.allowHighConfidenceEdit 
            ? 'Todas las cantidades son editables' 
            : `Solo cantidades con confianza menor a ${config.minConfidenceThreshold}% son editables`
          }
        </p>
      </div>

      {/* Umbral de confianza */}
      <div className="mb-4">
        <label className={`block text-sm font-medium mb-2 ${
          config.darkMode ? 'text-white' : 'text-gray-900'
        }`}>
          Umbral Mínimo de Confianza: {config.minConfidenceThreshold}%
        </label>
        <input
          type="range"
          min="50"
          max="95"
          value={config.minConfidenceThreshold}
          onChange={(e) => updateConfig({ minConfidenceThreshold: parseInt(e.target.value) })}
          className={`w-full h-2 rounded-lg appearance-none cursor-pointer ${
            config.darkMode ? 'bg-gray-600' : 'bg-gray-200'
          }`}
        />
        <div className={`flex justify-between text-xs mt-1 ${
          config.darkMode ? 'text-gray-400' : 'text-gray-500'
        }`}>
          <span>50%</span>
          <span>95%</span>
        </div>
      </div>
    </div>
  </div>
);



export default Sidebar;