import React, { useState } from 'react';

const AddProductModal = ({ isOpen, onClose, onAdd, ticketType }) => {
  const [productType, setProductType] = useState('5kg');
  const [quantity, setQuantity] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (quantity && parseInt(quantity) > 0) {
      onAdd(productType, parseInt(quantity));
      setQuantity('');
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4" onClick={e => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-gray-900">Agregar Producto</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tipo de Producto
            </label>
            <select
              value={productType}
              onChange={(e) => setProductType(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="5kg">Bolsas de 5kg</option>
              <option value="15kg">Bolsas de 15kg</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cantidad
            </label>
            <input
              type="number"
              min="1"
              max="999"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="Ingresa la cantidad"
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              autoFocus
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!quantity || parseInt(quantity) <= 0}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Agregar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddProductModal;