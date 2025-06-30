import React, { useState } from 'react';
import { useConfig } from '../contexts/ConfigContext';

const ProductTypeSelector = ({ value, onChange, ticketType }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [selectedType, setSelectedType] = useState('5kg');
  const { config } = useConfig();

  const productOptions = [
    { value: '5kg', label: 'Bolsa de 5kg' },
    { value: '15kg', label: 'Bolsa de 15kg' }
  ];

  const isUnknownProduct = value && (
    value.includes('DESCONOCIDO') || 
    value.includes('PRODUCTO DESCONOCIDO') ||
    value.includes('UNKNOWN') ||
    value.includes('Producto con importe') ||
    value === 'Producto'
  );

  const handleSave = () => {
    const newProductName = selectedType === '5kg' ? 'Bolsa de 5kg' : 'Bolsa de 15kg';
    onChange(newProductName);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
  };

  if (isEditing) {
    return (
      <div className="flex items-center space-x-2">
        <select
          value={selectedType}
          onChange={(e) => setSelectedType(e.target.value)}
          className={`text-sm border rounded px-2 py-1 focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            config.darkMode 
              ? 'bg-gray-700 border-gray-600 text-white' 
              : 'bg-white border-gray-300'
          }`}
          autoFocus
        >
          {productOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <button
          onClick={handleSave}
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
    );
  }

  return (
    <div
      onClick={() => isUnknownProduct && setIsEditing(true)}
      className={`text-sm px-2 py-1 rounded group flex items-center ${
        isUnknownProduct
          ? config.darkMode
            ? 'text-red-300 cursor-pointer hover:bg-red-800'
            : 'text-red-700 cursor-pointer hover:bg-red-200'
          : config.darkMode
            ? 'text-gray-100'
            : 'text-gray-900'
      }`}
    >
      <span>{value}</span>
      {isUnknownProduct && (
        <svg className="w-3 h-3 text-red-500 ml-1 opacity-0 group-hover:opacity-100" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      )}
    </div>
  );
};

export default ProductTypeSelector;