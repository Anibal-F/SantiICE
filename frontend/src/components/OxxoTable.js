import React, { useState, useEffect } from 'react';
import EditableCell from './EditableCell';
import DatePicker from './DatePicker';
import ConfidenceIndicator from './ConfidenceIndicator';
import SucursalSelector from './SucursalSelector';
import EditableQuantity from './EditableQuantity';
import { useConfig } from '../contexts/ConfigContext';

const OxxoTable = ({ 
  tickets, 
  onUpdateTicket, 
  selectedTickets, 
  onSelectTicket,
  openImageModal,
  onAddProduct,
  onUpdateQuantity,
  onDeleteTicket,
  onDeleteProduct
}) => {
  const { config } = useConfig();
  const [showDeleteDropdown, setShowDeleteDropdown] = useState({});
  const [deleteDropdownPosition, setDeleteDropdownPosition] = useState({});

  // Función para detectar si un ticket necesita atención (actualizada dinámicamente)
  const needsAttention = (ticket) => {
    const hasEmptyFields = [
      ticket.sucursal,
      ticket.fecha,
      ticket.remision,
      ticket.pedido_adicional
    ].some(field => 
      field === 'No detectada' || 
      field === 'No detectado' || 
      !field || 
      field.trim() === ''
    );

    const hasEmptyProducts = !ticket.productos || 
      ticket.productos.length === 0 || 
      ticket.productos.some(producto => {
        const cantidad = producto.cantidad || 0;
        const isUnknownProduct = producto.descripcion && 
          (producto.descripcion.includes('DESCONOCIDO') || 
           producto.descripcion.includes('PRODUCTO DESCONOCIDO') ||
           producto.descripcion.includes('Producto con importe') ||
           producto.descripcion === 'Producto');
        
        console.log('🔍 Debug OxxoTable needsAttention:', {
          descripcion: producto.descripcion,
          isUnknownProduct,
          cantidad
        });
        return cantidad === 0 || isUnknownProduct;
      });

    return hasEmptyFields || hasEmptyProducts;
  };

  const toggleDeleteDropdown = (ticketId, event) => {
    event.stopPropagation();
    const rect = event.currentTarget.getBoundingClientRect();
    setDeleteDropdownPosition({
      ...deleteDropdownPosition,
      [ticketId]: {
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX - 150,
        width: 200
      }
    });
    setShowDeleteDropdown(prev => ({
      ...prev,
      [ticketId]: !prev[ticketId]
    }));
  };

  // Cerrar dropdown al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = () => {
      if (Object.keys(showDeleteDropdown).some(key => showDeleteDropdown[key])) {
        setShowDeleteDropdown({});
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showDeleteDropdown]);
  const formatOxxoProducts = (productos, ticket, onUpdateQuantity) => {
    return productos.map((producto, index) => {
      const cantidad = producto.cantidad || 0;
      const esSingular = cantidad === 1;
      
      let tipo = '';
      const descripcion = producto.descripcion || '';
      
      // Verificar primero 15kg para evitar conflictos con 5kg
      if (descripcion.includes('15KG') || descripcion.includes('15kg') || descripcion.includes('15 kg')) {
        tipo = 'Bolsas de 15kg: ';
      } else if (descripcion.includes('5K') || descripcion.includes('5kg') || descripcion.includes('5 kg')) {
        tipo = 'Bolsas de 5kg: ';
      } else {
        tipo = `${descripcion}: `;
      }
      
      return (
        <div key={index} className="inline-flex items-center mr-4">
          <span>{tipo}</span>
          <EditableQuantity
            value={cantidad}
            onChange={(newQuantity) => onUpdateQuantity(ticket.id, index, newQuantity)}
            confidence={ticket.confidence}
            ticketId={ticket.id}
            productIndex={index}
          />
          <span className="ml-1">{esSingular ? 'pz' : 'pzs'}</span>
        </div>
      );
    });
  };

  return (
    <div className="overflow-x-auto -mx-2 sm:mx-0" style={{minHeight: '400px'}}>
      <div className="min-w-full inline-block align-middle">
      <table className={`min-w-full divide-y table-fixed ${
        config.darkMode ? 'divide-gray-700' : 'divide-gray-200'
      }`}>
        <thead className={config.darkMode ? 'bg-gray-700' : 'bg-gray-50'}>
          <tr>
            <th className={`px-2 py-3 text-center text-xs font-medium uppercase tracking-wider w-12 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              ✅
            </th>
            <th className={`px-2 py-3 text-left text-xs font-medium uppercase tracking-wider w-24 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              Imagen
            </th>
            <th className={`px-3 py-3 text-left text-xs font-medium uppercase tracking-wider w-32 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              Sucursal
            </th>
            <th className={`px-3 py-3 text-left text-xs font-medium uppercase tracking-wider w-28 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              Fecha
            </th>
            <th className={`px-3 py-3 text-left text-xs font-medium uppercase tracking-wider w-24 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              Remisión
            </th>
            <th className={`px-3 py-3 text-left text-xs font-medium uppercase tracking-wider w-24 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              Pedido
            </th>
            <th className={`px-3 py-3 text-left text-xs font-medium uppercase tracking-wider w-64 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              Productos
            </th>
            <th className={`px-3 py-3 text-left text-xs font-medium uppercase tracking-wider w-32 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              Precios
            </th>
            <th className={`px-2 py-3 text-center text-xs font-medium uppercase tracking-wider w-12 ${
              config.darkMode ? 'text-white' : 'text-gray-500'
            }`}>
              Eliminar
            </th>
          </tr>
        </thead>
        <tbody className={`divide-y ${
          config.darkMode ? 'bg-gray-800 divide-gray-700' : 'bg-white divide-gray-200'
        }`}>
          {tickets.map((ticket) => (
            <tr key={ticket.id} className={`${
              needsAttention(ticket)
                ? config.darkMode 
                  ? 'bg-red-900 hover:bg-red-800' 
                  : 'bg-red-200 hover:bg-red-300'
                : config.darkMode 
                  ? 'hover:bg-gray-700' 
                  : 'hover:bg-gray-50'
            }`}>
              <td className="px-2 py-4 whitespace-nowrap text-center">
                <input
                  type="checkbox"
                  checked={selectedTickets.includes(ticket.id)}
                  onChange={(e) => onSelectTicket(ticket.id, e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
              </td>
              <td className="px-2 py-4 whitespace-nowrap">
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => openImageModal(ticket.image_base64, ticket.filename)}
                    className="flex items-center justify-center w-8 h-8 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                    title={`Ver imagen: ${ticket.filename}`}
                  >
                    <svg className="w-4 h-4 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </button>
                  <span className="text-xs text-gray-500 truncate max-w-16" title={ticket.filename}>
                    {ticket.filename}
                  </span>
                </div>
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <SucursalSelector
                  value={ticket.sucursal}
                  onChange={(value) => onUpdateTicket(ticket.id, 'sucursal', value)}
                  ticketType="OXXO"
                />
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <DatePicker
                  value={ticket.fecha}
                  onChange={(value) => onUpdateTicket(ticket.id, 'fecha', value)}
                />
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <EditableCell
                  value={ticket.remision}
                  onChange={(value) => onUpdateTicket(ticket.id, 'remision', value)}
                />
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <EditableCell
                  value={ticket.pedido_adicional}
                  onChange={(value) => onUpdateTicket(ticket.id, 'pedido_adicional', value)}
                />
              </td>
              <td className="px-3 py-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm">
                    {formatOxxoProducts(ticket.productos, ticket, onUpdateQuantity)}
                  </div>
                  <div className="flex items-center space-x-1 relative">
                    {/* Botón eliminar producto */}
                    {ticket.productos.length > 1 && onDeleteProduct && (
                      <button
                        onClick={() => onDeleteProduct(ticket.id)}
                        className={`flex items-center justify-center w-6 h-6 transition-colors ${
                          config.darkMode 
                            ? 'text-orange-400 hover:text-orange-300' 
                            : 'text-orange-600 hover:bg-orange-100 rounded'
                        }`}
                        title="Eliminar producto"
                      >
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                        </svg>
                      </button>
                    )}
                    
                    {/* Botón agregar producto */}
                    <button
                      onClick={() => onAddProduct(ticket.id)}
                      className={`flex items-center justify-center w-8 h-8 transition-colors ${
                        config.darkMode 
                          ? 'text-white hover:text-gray-300' 
                          : 'bg-primary-100 hover:bg-primary-200 text-primary-600 rounded-full'
                      }`}
                      title="Agregar producto"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                    </button>
                  </div>
                </div>
              </td>
              <td className="px-3 py-4 whitespace-nowrap">
                <div className="space-y-1">
                  {ticket.productos.map((producto, index) => {
                    const descripcion = producto.descripcion || '';
                    let tipo = '';
                    let precioDefault = 17.5;
                    
                    if (descripcion.includes('15KG') || descripcion.includes('15kg') || descripcion.includes('15 kg')) {
                      tipo = '15kg';
                      precioDefault = 37.5;
                    } else if (descripcion.includes('5K') || descripcion.includes('5kg') || descripcion.includes('5 kg')) {
                      tipo = '5kg';
                      precioDefault = 17.5;
                    }
                    
                    const precio = producto.costo || precioDefault;
                    
                    return (
                      <div key={index} className="flex items-center space-x-1">
                        <span className="text-xs text-gray-500">{tipo}:</span>
                        <input
                          type="number"
                          step="0.1"
                          value={precio}
                          onChange={(e) => {
                            const updatedProducts = [...ticket.productos];
                            updatedProducts[index] = { ...updatedProducts[index], costo: parseFloat(e.target.value) || 0 };
                            onUpdateTicket(ticket.id, 'productos', updatedProducts);
                          }}
                          className={`w-16 px-1 py-0.5 text-xs border rounded ${
                            config.darkMode 
                              ? 'bg-gray-700 border-gray-600 text-white' 
                              : 'bg-white border-gray-300'
                          }`}
                        />
                      </div>
                    );
                  })}
                </div>
              </td>
              <td className="px-2 py-4 whitespace-nowrap">
                <div className="flex justify-center">
                  <button
                    onClick={() => onDeleteTicket && onDeleteTicket(ticket.id)}
                    className={`flex items-center justify-center w-8 h-8 rounded transition-colors ${
                      config.darkMode 
                        ? 'text-red-400 hover:bg-red-900' 
                        : 'text-red-600 hover:bg-red-100'
                    }`}
                    title="Eliminar ticket"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      </div>
    </div>
  );
};

export default OxxoTable;