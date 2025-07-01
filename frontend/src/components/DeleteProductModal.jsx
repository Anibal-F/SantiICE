import React from 'react';
import { useConfig } from '../contexts/ConfigContext';

const DeleteProductModal = ({ isOpen, onClose, onDelete, products, ticketType }) => {
  const { config } = useConfig();
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className={`w-full max-w-md p-6 rounded-lg shadow-xl ${
        config.darkMode ? 'bg-gray-800' : 'bg-white'
      }`}>
        <h3 className={`text-lg font-medium mb-4 ${
          config.darkMode ? 'text-white' : 'text-gray-900'
        }`}>
          Eliminar Producto
        </h3>
        
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {products.map((product, index) => {
            // Determinar qué mostrar según el tipo de ticket
            const displayName = ticketType === 'OXXO' 
              ? product.descripcion 
              : product.tipoProducto;
              
            const quantity = ticketType === 'OXXO'
              ? product.cantidad
              : product.numeroPiezasCompradas;
            
            return (
              <button
                key={index}
                onClick={() => {
                  onDelete(index);
                  // Cerrar el modal después de un pequeño delay para asegurar que se procese la eliminación
                  setTimeout(() => onClose(), 100);
                }}
                className={`w-full text-left p-3 rounded-md flex items-center justify-between ${
                  config.darkMode 
                    ? 'bg-gray-700 hover:bg-gray-600' 
                    : 'bg-gray-100 hover:bg-gray-200'
                }`}
              >
                <span className={config.darkMode ? 'text-white' : 'text-gray-900'}>
                  {displayName} ({quantity})
                </span>
                <svg className="w-5 h-5 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            );
          })}
        </div>
        
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className={`px-4 py-2 rounded-md ${
              config.darkMode 
                ? 'bg-gray-700 hover:bg-gray-600 text-white' 
                : 'bg-gray-200 hover:bg-gray-300 text-gray-800'
            }`}
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteProductModal;