import React, { useState, useEffect, useRef } from 'react';
import { useConfig } from '../contexts/ConfigContext';

const SucursalSelector = ({ value, onChange, ticketType }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [customValue, setCustomValue] = useState(value);
  const { config } = useConfig();
  const dropdownRef = useRef(null);

  const sucursales = config.sucursales[ticketType] || [];

  // Cerrar dropdown al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
        if (isEditing && customValue !== value) {
          handleCustomSave();
        } else {
          setIsEditing(false);
        }
      }
    };

    if (isDropdownOpen || isEditing) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isDropdownOpen, isEditing, customValue, value]);

  const handleSelect = (sucursal) => {
    onChange(sucursal);
    setIsDropdownOpen(false);
    setIsEditing(false);
  };

  const handleCustomSave = () => {
    onChange(customValue);
    setIsEditing(false);
    setIsDropdownOpen(false);
  };

  const handleCancel = () => {
    setCustomValue(value);
    setIsEditing(false);
    setIsDropdownOpen(false);
  };

  const handleInputFocus = () => {
    setIsDropdownOpen(true);
    // Si el input está vacío, mostrar el valor actual para que se vean todas las opciones
    if (customValue === '') {
      setCustomValue('');
    }
  };

  if (isEditing || isDropdownOpen) {
    return (
      <div className="relative" ref={dropdownRef}>
        <div className="flex items-center space-x-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={customValue}
              onChange={(e) => setCustomValue(e.target.value)}
              onFocus={handleInputFocus}
              onClick={handleInputFocus}
              placeholder="Escribir o seleccionar..."
              className={`w-full text-sm border rounded px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                config.darkMode 
                  ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                  : 'bg-white border-gray-300'
              }`}
              autoFocus
            />
            
            {/* Dropdown */}
            {isDropdownOpen && (
              <div className={`absolute top-full left-0 mt-1 border rounded-md shadow-xl z-[9999] w-64 ${
                config.darkMode 
                  ? 'bg-gray-800 border-gray-600' 
                  : 'bg-white border-gray-300'
              }`}>
                <div className="max-h-48 overflow-y-auto flex flex-col">
                  {sucursales.length > 0 ? (
                    <>
                      {/* Mostrar todas las sucursales, filtradas si hay texto */}
                      {sucursales
                        .filter(s => customValue === '' || s.toLowerCase().includes(customValue.toLowerCase()))
                        .map((sucursal, index) => (
                          <button
                            key={index}
                            onClick={() => handleSelect(sucursal)}
                            className={`w-full text-left px-3 py-2 text-sm border-b last:border-b-0 block ${
                              config.darkMode 
                                ? 'hover:bg-gray-700 focus:bg-gray-700 border-gray-600 text-white' 
                                : 'hover:bg-gray-100 focus:bg-gray-100 border-gray-100'
                            }`}
                          >
                            {sucursal}
                          </button>
                        ))}
                      
                      {/* Opción para agregar nueva si no existe */}
                      {customValue && customValue.trim() !== '' && !sucursales.some(s => s.toLowerCase() === customValue.toLowerCase()) && (
                        <button
                          onClick={handleCustomSave}
                          className={`w-full text-left px-3 py-2 text-sm font-medium border-t block ${
                            config.darkMode 
                              ? 'text-blue-400 hover:bg-gray-700 border-gray-600' 
                              : 'text-blue-600 hover:bg-blue-50 border-gray-200'
                          }`}
                        >
                          + Usar "{customValue}"
                        </button>
                      )}
                    </>
                  ) : (
                    <div className={`px-3 py-2 text-sm ${
                      config.darkMode ? 'text-gray-400' : 'text-gray-500'
                    }`}>
                      No hay sucursales configuradas para {ticketType}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          
          <div className="flex space-x-1">
            <button
              onClick={handleCustomSave}
              className="text-green-600 hover:text-green-800"
              title="Guardar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
            <button
              onClick={handleCancel}
              className="text-red-600 hover:text-red-800"
              title="Cancelar"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      onClick={() => {
        setIsEditing(true);
        setCustomValue(value || ''); // Mantener el valor actual
        setIsDropdownOpen(true);
      }}
      className={`text-sm cursor-pointer px-2 py-1 rounded group flex items-center ${
        config.darkMode 
          ? 'text-gray-100 hover:bg-gray-700' 
          : 'text-gray-900 hover:bg-gray-100'
      }`}
    >
      <span>{value}</span>
      <svg className="w-3 h-3 text-gray-400 ml-1 opacity-0 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
      </svg>
    </div>
  );
};

export default SucursalSelector;