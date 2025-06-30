import React, { useState } from 'react';
import { useConfig } from '../contexts/ConfigContext';

const SucursalSelectorDebug = ({ value, onChange, ticketType }) => {
  const [isOpen, setIsOpen] = useState(false);
  const { config } = useConfig();

  const sucursales = config?.sucursales?.[ticketType] || [];
  
  // Debug logs
  console.log('=== DEBUG SUCURSAL SELECTOR ===');
  console.log('ticketType:', ticketType);
  console.log('config:', config);
  console.log('config.sucursales:', config?.sucursales);
  console.log('sucursales para', ticketType, ':', sucursales);
  console.log('================================');

  const handleSelect = (sucursal) => {
    onChange(sucursal);
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="text-sm text-gray-900 cursor-pointer hover:bg-gray-100 px-2 py-1 rounded flex items-center"
      >
        <span>{value}</span>
        <svg className="w-3 h-3 text-gray-400 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-md shadow-lg z-50 min-w-48">
          <div className="p-2 border-b text-xs text-gray-500">
            Tipo: {ticketType} | Total: {sucursales.length}
          </div>
          
          {sucursales.length > 0 ? (
            sucursales.map((sucursal, index) => (
              <button
                key={index}
                onClick={() => handleSelect(sucursal)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100 border-b border-gray-100 last:border-b-0"
              >
                {sucursal}
              </button>
            ))
          ) : (
            <div className="px-3 py-2 text-sm text-red-500">
              ❌ No hay sucursales para {ticketType}
            </div>
          )}
          
          <button
            onClick={() => setIsOpen(false)}
            className="w-full px-3 py-2 text-xs text-gray-500 hover:bg-gray-50 border-t"
          >
            Cerrar
          </button>
        </div>
      )}
    </div>
  );
};

export default SucursalSelectorDebug;