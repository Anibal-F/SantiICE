import React, { useState, useRef, useEffect } from 'react';
import { useConfig } from '../contexts/ConfigContext';
import DeleteProductModal from './DeleteProductModal';

const ManualTicketEntry = ({ onAddTicket, showToast, onNavigateToStep }) => {
  const { config, getPrecio } = useConfig();
  const [isOpen, setIsOpen] = useState(false);
  const [manualTickets, setManualTickets] = useState([]);
  const [formData, setFormData] = useState({
    cliente: '',
    fecha: '',
    sucursal: '',
    productos: [{ tipo: '5kg', cantidad: '' }],
    remision: '',
    pedido: '',
    folio: ''
  });
  const [errors, setErrors] = useState({});
  const [sucursalFilter, setSucursalFilter] = useState('');
  const [showSucursalDropdown, setShowSucursalDropdown] = useState(false);
  const sucursalInputRef = useRef(null);
  const dropdownRef = useRef(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0, width: 0 });
  const [deleteProductModal, setDeleteProductModal] = useState({ isOpen: false, ticketId: null, ticketType: null });

  // Actualizar posición del dropdown
  const updateDropdownPosition = () => {
    if (sucursalInputRef.current) {
      const rect = sucursalInputRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width
      });
    }
  };

  // Manejar scroll y resize
  useEffect(() => {
    const handleScrollOrResize = () => {
      if (showSucursalDropdown) {
        updateDropdownPosition();
      }
    };

    if (showSucursalDropdown) {
      window.addEventListener('scroll', handleScrollOrResize, true);
      window.addEventListener('resize', handleScrollOrResize);
      return () => {
        window.removeEventListener('scroll', handleScrollOrResize, true);
        window.removeEventListener('resize', handleScrollOrResize);
      };
    }
  }, [showSucursalDropdown]);

  // Funciones para el modal de eliminación de productos
  const openDeleteProductModal = (ticketId) => {
    const ticket = manualTickets.find(t => t.id === ticketId);
    if (ticket) {
      setDeleteProductModal({ 
        isOpen: true, 
        ticketId, 
        ticketType: ticket.cliente 
      });
    }
  };

  const closeDeleteProductModal = () => {
    setDeleteProductModal({ isOpen: false, ticketId: null, ticketType: null });
  };

  // Catálogos reales del sistema
  const clientes = ['OXXO', 'KIOSKO'];
  const sucursales = config.sucursales || {
    OXXO: ['Girasoles', 'Zaragoza', 'Valle del Sol', 'Urias', 'Guasave', 'Cerro Colorado', 'San Rafael', 'Acapulco', 'Atlantico'],
    KIOSKO: ['20 De Noviembre', 'Gas Cardones', 'Centro', 'Malecón', 'Plaza Norte']
  };
  const productos = [
    { value: '5kg', label: 'Bolsa de 5kg' },
    { value: '15kg', label: 'Bolsa de 15kg' }
  ];

  const validateForm = () => {
    const newErrors = {};
    
    // Campos obligatorios
    if (!formData.cliente) newErrors.cliente = 'Cliente es obligatorio';
    if (!formData.fecha) newErrors.fecha = 'Fecha es obligatoria';
    if (!formData.sucursal) newErrors.sucursal = 'Sucursal es obligatoria';
    if (!formData.productos?.[0]?.cantidad) newErrors.cantidad = 'Cantidad es obligatoria';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    
    if (!validateForm()) {
      showToast('Por favor complete todos los campos obligatorios', 'error');
      return;
    }

    const newTicket = {
      id: `manual-${Date.now()}`,
      tipo: 'manual',
      cliente: formData.cliente,
      fecha: formData.fecha,
      sucursal: formData.sucursal,
      productos: (formData.productos || []).filter(p => p.cantidad).map(p => ({
        nombre: p.tipo === '5kg' ? 'Bolsa de 5kg' : 'Bolsa de 15kg',
        tipo: p.tipo,
        cantidad: parseInt(p.cantidad)
      })),
      remision: formData.remision || null,
      pedido: formData.pedido || null,
      folio: formData.folio || null,
      timestamp: new Date().toISOString()
    };

    setManualTickets([...manualTickets, newTicket]);
    
    // Limpiar formulario
    setFormData({
      cliente: formData.cliente, // Mantener cliente seleccionado
      fecha: '',
      sucursal: '',
      productos: [{ tipo: '5kg', cantidad: '' }],
      remision: '',
      pedido: '',
      folio: ''
    });
    setErrors({});
    
    showToast('Ticket manual agregado correctamente', 'success');
  };

  const handleDeleteTicket = (ticketId) => {
    setManualTickets(manualTickets.filter(t => t.id !== ticketId));
    showToast('Ticket eliminado', 'success');
  };

  const handleDeleteProduct = (ticketId, productIndex) => {
    const updatedTickets = manualTickets.map(ticket => {
      if (ticket.id === ticketId) {
        const newProductos = ticket.productos.filter((_, idx) => idx !== productIndex);
        // Si no quedan productos, eliminar el ticket completo
        if (newProductos.length === 0) {
          showToast('Ticket eliminado (sin productos)', 'info');
          return null;
        }
        return { ...ticket, productos: newProductos };
      }
      return ticket;
    }).filter(Boolean);
    
    setManualTickets(updatedTickets);
    showToast('Producto eliminado', 'success');
  };

  const handleSendTickets = async () => {
    if (manualTickets.length === 0) {
      showToast('No hay tickets para enviar', 'error');
      return;
    }

    try {
      showToast('Enviando tickets a Google Sheets...', 'info');
      
      // Navegar al paso 4 para mostrar el progreso
      if (onNavigateToStep) {
        onNavigateToStep(4, {
          tickets: manualTickets,
          totalTickets: manualTickets.length,
          isManualUpload: true
        });
      }
      
      // Transformar tickets al formato exacto que espera la API
      const formattedTickets = manualTickets.map(ticket => {
        // Calcular precio total correctamente con manejo de errores
        const precioTotal = ticket.productos.reduce((total, prod) => {
          try {
            const precio = getPrecio(ticket.cliente, ticket.sucursal, prod.tipo);
            return total + (precio * prod.cantidad);
          } catch (error) {
            console.warn(`Error calculando precio para ${ticket.cliente}-${ticket.sucursal}-${prod.tipo}:`, error);
            // Usar precio por defecto si hay error
            const precioDefault = ticket.cliente === 'KIOSKO' ? 
              (prod.tipo === '5kg' ? 16.0 : 45.0) : 
              (prod.tipo === '5kg' ? 17.5 : 37.5);
            return total + (precioDefault * prod.cantidad);
          }
        }, 0);

        // Estructura exacta que espera el backend según TicketData
        // Agregar fecha y datos del ticket a cada producto
        const productosConDatos = ticket.productos.map(producto => {
          // Calcular precio usando el catálogo de sucursales con manejo de errores
          let precio;
          try {
            precio = getPrecio(ticket.cliente, ticket.sucursal, producto.tipo);
            console.log(`💰 Precio calculado para ${ticket.cliente}-${ticket.sucursal}-${producto.tipo}: ${precio}`);
          } catch (error) {
            console.warn(`Error calculando precio para ${ticket.cliente}-${ticket.sucursal}-${producto.tipo}:`, error);
            // Usar precio por defecto si hay error
            precio = ticket.cliente === 'KIOSKO' ? 
              (producto.tipo === '5kg' ? 16.0 : 45.0) : 
              (producto.tipo === '5kg' ? 17.5 : 37.5);
            console.log(`💰 Usando precio por defecto: ${precio}`);
          }
          
          return {
            ...producto,
            fecha: ticket.fecha,
            sucursal: ticket.sucursal,
            cliente: ticket.cliente,
            remision: ticket.remision ? String(ticket.remision) : `MANUAL-${ticket.id}`,
            pedido_adicional: ticket.pedido ? String(ticket.pedido) : `MANUAL-${ticket.id}`,
            folio: ticket.folio ? String(ticket.folio) : `MANUAL-${ticket.id}`,
            // Campos adicionales para identificación del producto
            descripcion: producto.nombre, // Para OXXO - "Bolsa de 5kg"
            tipoProducto: producto.nombre, // Para KIOSKO - "Bolsa de 5kg" en lugar de "5kg"
            tipo: producto.tipo, // Mantener el tipo original "5kg"/"15kg"
            costo: precio, // Precio unitario
            numeroPiezasCompradas: producto.cantidad, // Para KIOSKO
            // Identificador único para tickets manuales
            ticket_manual_id: ticket.id, // ID único para evitar duplicados
            // Campo específico para KIOSKO - nombre de la tienda
            nombreTienda: ticket.sucursal // Para que el backend registre la sucursal correctamente
          };
        });

        return {
          id: ticket.id,
          filename: `manual-${ticket.id}.jpg`,
          sucursal: ticket.sucursal,
          fecha: ticket.fecha,
          productos: productosConDatos,
          confidence: 100,
          status: 'confirmed',
          sucursal_type: ticket.cliente,
          // Campos opcionales - SIEMPRE string, nunca null
          remision: ticket.remision ? String(ticket.remision) : `MANUAL-${ticket.id}`, // ID único si está vacío
          pedido_adicional: ticket.pedido ? String(ticket.pedido) : `MANUAL-${ticket.id}`, // ID único si está vacío
          folio: ticket.folio ? String(ticket.folio) : `MANUAL-${ticket.id}` // ID único si está vacío
        };
      });
      
      console.log('Enviando tickets:', JSON.stringify(formattedTickets, null, 2));
      console.log('Estructura completa:', formattedTickets.map(t => ({ 
        id: t.id, 
        fecha: t.fecha, 
        folio: t.folio, 
        remision: t.remision,
        pedido: t.pedido,
        productos: t.productos 
      })));
      
      // Usar fetch directamente - enviar como objeto con propiedad tickets
      const response = await fetch('/confirm-tickets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tickets: formattedTickets
        })
      });
      
      const result = await response.json();
      
      if (response.ok) {
        // Si la respuesta es 200, consideramos que se enviaron correctamente
        // aunque haya algunos errores de procesamiento en el backend
        const successCount = formattedTickets.length;
        if (result.summary?.errors > 0) {
          showToast(`${successCount} tickets enviados (${result.summary.errors} con errores menores)`, 'warning');
        } else {
          showToast(`¡${successCount} tickets manuales enviados a Google Sheets!`, 'success');
        }
        
        // Limpiar tickets enviados
        setManualTickets([]);
        setIsOpen(false);
        
        // Si hay función de navegación, ir al paso final
        if (onNavigateToStep) {
          // Agregar información del cliente a cada resultado
          const enhancedResults = (result.results || []).map(res => {
            const originalTicket = formattedTickets.find(t => t.id === res.id);
            return {
              ...res,
              cliente: originalTicket?.sucursal_type || 'Desconocido',
              sucursal: originalTicket?.sucursal || 'N/A',
              displayName: `${originalTicket?.sucursal_type || 'Manual'} - ${originalTicket?.sucursal || res.filename}`
            };
          });
          
          const resultsData = {
            results: enhancedResults,
            summary: result.summary || { 
              total: formattedTickets.length, 
              success: result.summary?.success || formattedTickets.length, 
              errors: result.summary?.errors || 0,
              duplicated: result.summary?.duplicated || 0
            },
            isManualUpload: true
          };
          console.log('Enviando datos de resultados:', resultsData);
          onNavigateToStep(5, resultsData);
        }
        
        // Log para debugging
        if (result.summary?.errors > 0) {
          console.warn('Algunos tickets tuvieron errores de procesamiento:', result.summary.errors);
          console.log('Respuesta completa del backend:', result);
          console.log('Detalles de errores:', result.results);
          
          // Mostrar errores específicos
          const errores = result.results.filter(r => r.status === 'error');
          errores.forEach(error => {
            console.error(`Error en ${error.filename}: ${error.message}`);
          });
        }
      } else {
        console.error('Error response:', result);
        showToast('Error al enviar tickets manuales', 'error');
      }
    } catch (error) {
      console.error('Error enviando tickets manuales:', error);
      showToast('Error de conexión al enviar tickets', 'error');
    }
  };

  return (
    <div className={`border rounded-lg ${
      config.darkMode ? 'border-gray-600 bg-gray-800' : 'border-gray-300 bg-white'
    }`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-300 dark:border-gray-600">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`w-full flex items-center justify-between text-left ${
            config.darkMode ? 'text-white' : 'text-gray-900'
          }`}
        >
          <div>
            <h3 className="text-lg font-medium">Entrada Manual de Tickets</h3>
            <p className={`text-sm ${
              config.darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Agregar tickets sin imagen física
            </p>
          </div>
          <svg 
            className={`w-5 h-5 transform transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Content */}
      {isOpen && (
        <div className="p-4 space-y-6">
          {/* Vista Tabla para Entrada Manual */}
          <div className="space-y-4">
            <div className="overflow-x-auto">
              <table className={`w-full border rounded-lg ${
                config.darkMode ? 'border-gray-600' : 'border-gray-300'
              }`}>
                <thead className={config.darkMode ? 'bg-gray-700' : 'bg-gray-50'}>
                  <tr>
                    <th className={`px-3 py-2 text-left text-xs font-medium uppercase ${
                      config.darkMode ? 'text-gray-300' : 'text-gray-500'
                    }`}>Cliente *</th>
                    <th className={`px-3 py-2 text-left text-xs font-medium uppercase ${
                      config.darkMode ? 'text-gray-300' : 'text-gray-500'
                    }`}>Fecha *</th>
                    <th className={`px-3 py-2 text-left text-xs font-medium uppercase ${
                      config.darkMode ? 'text-gray-300' : 'text-gray-500'
                    }`}>Sucursal *</th>
                    <th className={`px-3 py-2 text-left text-xs font-medium uppercase ${
                      config.darkMode ? 'text-gray-300' : 'text-gray-500'
                    }`}>Productos *</th>
                    {(manualTickets.some(t => t.cliente === 'OXXO') || formData.cliente === 'OXXO') && (
                      <th className={`px-3 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Remisión</th>
                    )}
                    {(manualTickets.some(t => t.cliente === 'OXXO') || formData.cliente === 'OXXO') && (
                      <th className={`px-3 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Pedido</th>
                    )}
                    {(manualTickets.some(t => t.cliente === 'KIOSKO') || formData.cliente === 'KIOSKO') && (
                      <th className={`px-3 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Folio</th>
                    )}
                    <th className={`px-3 py-2 text-center text-xs font-medium uppercase ${
                      config.darkMode ? 'text-gray-300' : 'text-gray-500'
                    }`}>Acciones</th>
                  </tr>
                </thead>
                <tbody className={`divide-y ${
                  config.darkMode ? 'divide-gray-600 bg-gray-800' : 'divide-gray-200 bg-white'
                }`}>
                  {/* Fila de entrada */}
                  <tr>
                    {/* Cliente */}
                    <td className="px-3 py-2">
                      <select
                        value={formData.cliente}
                        onChange={(e) => {
                          setFormData({...formData, cliente: e.target.value, sucursal: ''});
                          setErrors({...errors, cliente: ''});
                        }}
                        className={`w-full px-2 py-1 text-sm border rounded ${
                          errors.cliente 
                            ? 'border-red-500' 
                            : config.darkMode 
                              ? 'border-gray-600 bg-gray-700 text-white' 
                              : 'border-gray-300 bg-white'
                        }`}
                      >
                        <option value="">Seleccionar</option>
                        {clientes.map(cliente => (
                          <option key={cliente} value={cliente}>{cliente}</option>
                        ))}
                      </select>
                      {errors.cliente && <p className="text-red-500 text-xs mt-1">{typeof errors.cliente === 'string' ? errors.cliente : 'Error en cliente'}</p>}
                    </td>

                    {/* Fecha */}
                    <td className="px-3 py-2">
                      <input
                        type="date"
                        value={formData.fecha}
                        onChange={(e) => {
                          setFormData({...formData, fecha: e.target.value});
                          setErrors({...errors, fecha: ''});
                        }}
                        className={`w-full px-2 py-1 text-sm border rounded ${
                          errors.fecha 
                            ? 'border-red-500' 
                            : config.darkMode 
                              ? 'border-gray-600 bg-gray-700 text-white' 
                              : 'border-gray-300 bg-white'
                        }`}
                      />
                      {errors.fecha && <p className="text-red-500 text-xs mt-1">{typeof errors.fecha === 'string' ? errors.fecha : 'Error en fecha'}</p>}
                    </td>

                    {/* Sucursal con filtro */}
                    <td className="px-3 py-2">
                      <input
                        type="text"
                        value={formData.sucursal || sucursalFilter}
                        onChange={(e) => {
                          const value = e.target.value;
                          setSucursalFilter(value);
                          setFormData({...formData, sucursal: ''});
                          setShowSucursalDropdown(true);
                          setErrors({...errors, sucursal: ''});
                        }}
                        onFocus={() => {
                          if (formData.cliente) {
                            updateDropdownPosition();
                            setShowSucursalDropdown(true);
                            setSucursalFilter('');
                          }
                        }}
                        onBlur={(e) => {
                          // Solo cerrar si no se está haciendo clic en el dropdown
                          setTimeout(() => {
                            if (!dropdownRef.current?.contains(document.activeElement)) {
                              setShowSucursalDropdown(false);
                            }
                          }, 150);
                        }}
                        disabled={!formData.cliente}
                        placeholder={formData.cliente ? "Buscar..." : "Cliente primero"}
                        ref={sucursalInputRef}
                        className={`w-full px-2 py-1 text-sm border rounded ${
                          errors.sucursal 
                            ? 'border-red-500' 
                            : config.darkMode 
                              ? 'border-gray-600 bg-gray-700 text-white' 
                              : 'border-gray-300 bg-white'
                        } ${!formData.cliente ? 'opacity-50 cursor-not-allowed' : ''}`}
                      />
                      
                      {/* Dropdown de sucursales */}
                      {showSucursalDropdown && formData.cliente && (
                        <div 
                          ref={dropdownRef}
                          className={`fixed border rounded-md shadow-xl max-h-48 overflow-y-auto border rounded-md shadow-xl ${
                            config.darkMode 
                              ? 'bg-gray-800 border-gray-600' 
                              : 'bg-white border-gray-300'
                          }`}
                          style={{
                            top: dropdownPosition.top + 2,
                            left: dropdownPosition.left,
                            width: Math.max(dropdownPosition.width, 200),
                            zIndex: 9999
                          }}
                        >
                          {sucursales[formData.cliente]
                            ?.filter(sucursal => 
                              sucursal.toLowerCase().includes(sucursalFilter.toLowerCase())
                            )
                            .map(sucursal => (
                              <button
                                key={sucursal}
                                type="button"
                                onMouseDown={(e) => {
                                  e.preventDefault(); // Prevenir que se active onBlur
                                  setFormData({...formData, sucursal});
                                  setSucursalFilter('');
                                  setShowSucursalDropdown(false);
                                  setErrors({...errors, sucursal: ''});
                                }}
                                className={`w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-sm ${
                                  config.darkMode ? 'text-white' : 'text-gray-900'
                                }`}
                              >
                                {sucursal}
                              </button>
                            ))
                          }
                        </div>
                      )}
                      {errors.sucursal && <p className="text-red-500 text-xs mt-1">{typeof errors.sucursal === 'string' ? errors.sucursal : 'Error en sucursal'}</p>}
                    </td>

                    {/* Productos */}
                    <td className="px-3 py-2">
                      <div className="flex items-center space-x-2">
                        <div className="flex-1">
                          {(formData.productos || []).map((producto, index) => (
                            <div key={index} className="flex items-center space-x-2 mb-1">
                              <select
                                value={producto.tipo}
                                onChange={(e) => {
                                  const newProductos = [...(formData.productos || [])];
                                  newProductos[index].tipo = e.target.value;
                                  setFormData({...formData, productos: newProductos});
                                }}
                                className={`px-2 py-1 text-sm border rounded ${
                                  config.darkMode 
                                    ? 'border-gray-600 bg-gray-700 text-white' 
                                    : 'border-gray-300 bg-white'
                                }`}
                              >
                                <option value="5kg">5kg</option>
                                <option value="15kg">15kg</option>
                              </select>
                              <input
                                type="number"
                                min="1"
                                value={producto.cantidad}
                                onChange={(e) => {
                                  const newProductos = [...(formData.productos || [])];
                                  newProductos[index].cantidad = e.target.value;
                                  setFormData({...formData, productos: newProductos});
                                  setErrors({...errors, cantidad: ''});
                                }}
                                className={`w-20 px-2 py-1 text-sm border rounded ${
                                  errors.cantidad && index === 0
                                    ? 'border-red-500' 
                                    : config.darkMode 
                                      ? 'border-gray-600 bg-gray-700 text-white' 
                                      : 'border-gray-300 bg-white'
                                }`}
                                placeholder="10"
                              />
                              {index > 0 && (
                                <button
                                  onClick={() => {
                                    const newProductos = (formData.productos || []).filter((_, i) => i !== index);
                                    setFormData({...formData, productos: newProductos});
                                  }}
                                  className="text-red-600 hover:text-red-800"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                </button>
                              )}
                            </div>
                          ))}
                        </div>
                        <button
                          onClick={() => {
                            setFormData({
                              ...formData,
                              productos: [...(formData.productos || []), { tipo: '5kg', cantidad: '' }]
                            });
                          }}
                          className="text-blue-600 hover:text-blue-800"
                          title="Agregar producto"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                          </svg>
                        </button>
                      </div>
                      {errors.cantidad && <p className="text-red-500 text-xs mt-1">{typeof errors.cantidad === 'string' ? errors.cantidad : 'Error en cantidad'}</p>}
                    </td>

                    {/* Campos dinámicos según cliente */}
                    {(manualTickets.some(t => t.cliente === 'OXXO') || formData.cliente === 'OXXO') && (
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={formData.remision}
                          onChange={(e) => setFormData({...formData, remision: e.target.value})}
                          disabled={formData.cliente !== 'OXXO'}
                          className={`w-full px-2 py-1 text-sm border rounded ${
                            config.darkMode 
                              ? 'border-gray-600 bg-gray-700 text-white' 
                              : 'border-gray-300 bg-white'
                          } ${formData.cliente !== 'OXXO' ? 'opacity-50' : ''}`}
                          placeholder="Opcional"
                        />
                      </td>
                    )}
                    {(manualTickets.some(t => t.cliente === 'OXXO') || formData.cliente === 'OXXO') && (
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={formData.pedido}
                          onChange={(e) => setFormData({...formData, pedido: e.target.value})}
                          disabled={formData.cliente !== 'OXXO'}
                          className={`w-full px-2 py-1 text-sm border rounded ${
                            config.darkMode 
                              ? 'border-gray-600 bg-gray-700 text-white' 
                              : 'border-gray-300 bg-white'
                          } ${formData.cliente !== 'OXXO' ? 'opacity-50' : ''}`}
                          placeholder="Opcional"
                        />
                      </td>
                    )}
                    {(manualTickets.some(t => t.cliente === 'KIOSKO') || formData.cliente === 'KIOSKO') && (
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={formData.folio}
                          onChange={(e) => setFormData({...formData, folio: e.target.value})}
                          disabled={formData.cliente !== 'KIOSKO'}
                          className={`w-full px-2 py-1 text-sm border rounded ${
                            config.darkMode 
                              ? 'border-gray-600 bg-gray-700 text-white' 
                              : 'border-gray-300 bg-white'
                          } ${formData.cliente !== 'KIOSKO' ? 'opacity-50' : ''}`}
                          placeholder="Opcional"
                        />
                      </td>
                    )}

                    {/* Acciones */}
                    <td className="px-3 py-2 text-center">
                      <button
                        onClick={handleSubmit}
                        className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                      >
                        Agregar
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Tabla de tickets manuales */}
          {manualTickets.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h4 className={`text-lg font-medium ${
                  config.darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  Tickets Agregados ({manualTickets.length})
                </h4>
                <button
                  onClick={handleSendTickets}
                  className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                  disabled={manualTickets.length === 0}
                >
                  Enviar Directamente a Sheets
                </button>
              </div>

              <div className="overflow-x-auto">
                <table className={`w-full border rounded-lg ${
                  config.darkMode ? 'border-gray-600' : 'border-gray-300'
                }`}>
                  <thead className={config.darkMode ? 'bg-gray-700' : 'bg-gray-50'}>
                    <tr>
                      <th className={`px-4 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Cliente</th>
                      <th className={`px-4 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Fecha</th>
                      <th className={`px-4 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Sucursal</th>
                      <th className={`px-4 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Producto</th>
                      <th className={`px-4 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Cantidad</th>
                      <th className={`px-4 py-2 text-left text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Info Adicional</th>
                      <th className={`px-4 py-2 text-center text-xs font-medium uppercase ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>Acciones</th>
                    </tr>
                  </thead>
                  <tbody className={`divide-y ${
                    config.darkMode ? 'divide-gray-600 bg-gray-800' : 'divide-gray-200 bg-white'
                  }`}>
                    {manualTickets.map((ticket) => (
                      <tr key={ticket.id}>
                        <td className={`px-4 py-2 text-sm ${
                          config.darkMode ? 'text-white' : 'text-gray-900'
                        }`}>{ticket.cliente}</td>
                        <td className={`px-4 py-2 text-sm ${
                          config.darkMode ? 'text-white' : 'text-gray-900'
                        }`}>{ticket.fecha}</td>
                        <td className={`px-4 py-2 text-sm ${
                          config.darkMode ? 'text-white' : 'text-gray-900'
                        }`}>{ticket.sucursal}</td>
                        <td className={`px-4 py-2 text-sm ${
                          config.darkMode ? 'text-white' : 'text-gray-900'
                        }`}>
                          {ticket.productos.map((prod, idx) => (
                            <div key={idx}>
                              {prod.nombre} ({prod.cantidad})
                            </div>
                          ))}
                        </td>
                        <td className={`px-4 py-2 text-sm ${
                          config.darkMode ? 'text-white' : 'text-gray-900'
                        }`}>
                          {ticket.productos.reduce((total, prod) => total + prod.cantidad, 0)}
                        </td>
                        <td className={`px-4 py-2 text-sm ${
                          config.darkMode ? 'text-gray-300' : 'text-gray-600'
                        }`}>
                          {ticket.remision && `Rem: ${ticket.remision}`}
                          {ticket.pedido && `Ped: ${ticket.pedido}`}
                          {ticket.folio && `Folio: ${ticket.folio}`}
                          {!ticket.remision && !ticket.pedido && !ticket.folio && '-'}
                        </td>
                        <td className="px-4 py-2 text-center relative">
                          <div className="flex items-center justify-center space-x-2">
                            {/* Botón eliminar producto */}
                            {ticket.productos.length > 1 && (
                              <button
                                onClick={() => openDeleteProductModal(ticket.id)}
                                className="text-orange-600 hover:text-orange-800 transition-colors"
                                title="Eliminar producto"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                                </svg>
                              </button>
                            )}
                            
                            {/* Botón eliminar ticket completo */}
                            <button
                              onClick={() => handleDeleteTicket(ticket.id)}
                              className="text-red-600 hover:text-red-800 transition-colors"
                              title="Eliminar ticket completo"
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
          )}
        </div>
      )}
      
      {/* Modal para eliminar productos */}
      <DeleteProductModal
        isOpen={deleteProductModal.isOpen}
        onClose={closeDeleteProductModal}
        onDelete={(productIndex) => {
          const ticketId = deleteProductModal.ticketId;
          handleDeleteProduct(ticketId, productIndex);
          closeDeleteProductModal();
        }}
        products={manualTickets.find(t => t.id === deleteProductModal.ticketId)?.productos || []}
        ticketType={deleteProductModal.ticketType}
      />
    </div>
  );
};

export default ManualTicketEntry;