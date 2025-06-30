import { useState } from 'react';
import { processTickets as apiProcessTickets, confirmTickets as apiConfirmTickets } from '../utils/api';
import { useConfig } from '../contexts/ConfigContext';
import { sanitizeApiResponse } from '../utils/errorUtils';

export const useTicketProcessing = () => {
  const { config } = useConfig();
  const [tickets, setTickets] = useState([]);
  const [processing, setProcessing] = useState(null);
  const [confirming, setConfirming] = useState(null);
  const [results, setResults] = useState(null);
  const [processingMore, setProcessingMore] = useState(false);
  const [newTicketCounts, setNewTicketCounts] = useState({ oxxo: 0, kiosko: 0 });

  const processTickets = async (files, isAdditional = false) => {
    try {
      if (isAdditional) {
        setProcessingMore(true);
      } else {
        setProcessing({
          total: files.length,
          completed: 0,
          current: files[0]?.name
        });
      }

      const response = await apiProcessTickets(files, (progress) => {
        if (!isAdditional) {
          setProcessing(prev => ({
            ...prev,
            completed: progress.completed,
            current: progress.current
          }));
        }
      });

      if (response.success) {
        if (isAdditional) {
          // Contar nuevos tickets por tipo
          const newOxxo = response.results.filter(t => t.sucursal_type === 'OXXO' && t.status === 'processed').length;
          const newKiosko = response.results.filter(t => t.sucursal_type === 'KIOSKO' && t.status === 'processed').length;
          
          setNewTicketCounts({ oxxo: newOxxo, kiosko: newKiosko });
          setTickets(prevTickets => [...prevTickets, ...response.results]);
          setProcessingMore(false);
        } else {
          setTickets(response.results);
          setProcessing(null);
          setNewTicketCounts({ oxxo: 0, kiosko: 0 });
        }
        return { success: true, processedCount: response.processed };
      } else {
        throw new Error('Error al procesar tickets');
      }
    } catch (error) {
      console.error('Error processing tickets:', error);
      if (isAdditional) {
        setProcessingMore(false);
      } else {
        setProcessing(null);
      }
      return false;
    }
  };

  const confirmTickets = async (ticketsToConfirm) => {
    try {
      setConfirming({
        total: ticketsToConfirm.length,
        completed: 0
      });

      // Asegurar que los datos editados estén sincronizados con los productos
      const ticketsWithUpdatedProducts = ticketsToConfirm.map(ticket => {
        const baseProductUpdate = {
          sucursal: ticket.sucursal,
          fecha: ticket.fecha
        };
        
        // Agregar campos específicos según el tipo
        if (ticket.sucursal_type === 'OXXO') {
          baseProductUpdate.remision = ticket.remision;
          baseProductUpdate.pedido_adicional = ticket.pedido_adicional;
        } else if (ticket.sucursal_type === 'KIOSKO') {
          baseProductUpdate.folio = ticket.folio;
          // Para KIOSKO, también sincronizar nombreTienda con sucursal
          baseProductUpdate.nombreTienda = ticket.sucursal;
        }
        
        return {
          ...ticket,
          productos: ticket.productos.map(producto => ({
            ...producto,
            ...baseProductUpdate
          }))
        };
      });

      const response = await apiConfirmTickets(ticketsWithUpdatedProducts, config.precios);
      
      // Sanitizar la respuesta para asegurar mensajes seguros
      const safeResponse = sanitizeApiResponse({
        success: response?.success || false,
        results: response?.results || [],
        summary: response?.summary || {
          total: 0,
          success: 0,
          errors: 0,
          duplicated: 0
        }
      });
      
      setResults(safeResponse);
      setConfirming(null);
      return safeResponse;
    } catch (error) {
      console.error('Error confirming tickets:', error);
      
      // Establecer un resultado de error seguro
      const errorResponse = sanitizeApiResponse({
        success: false,
        results: ticketsToConfirm.map(ticket => ({
          id: ticket.id,
          filename: ticket.filename || 'Unknown file',
          status: 'error',
          message: error.message || 'Error de procesamiento'
        })),
        summary: {
          total: ticketsToConfirm.length,
          success: 0,
          errors: ticketsToConfirm.length,
          duplicated: 0
        },
        error: error.message || 'Error de procesamiento'
      });
      
      setResults(errorResponse);
      setConfirming(null);
      return errorResponse;
    }
  };

  const updateTicket = (ticketId, field, value) => {
    console.log('updateTicket llamado:', { ticketId, field, value });
    
    setTickets(prevTickets => {
      const updatedTickets = prevTickets.map(ticket => {
        if (ticket.id === ticketId) {
          // Caso especial para actualizar productos directamente
          if (field === 'productos') {
            console.log('Actualizando productos:', value);
            return { ...ticket, productos: value };
          }
          
          const updatedTicket = { ...ticket, [field]: value };
          
          // Actualizar también los productos con la nueva información
          if (['sucursal', 'fecha', 'remision', 'pedido_adicional', 'folio'].includes(field)) {
            updatedTicket.productos = ticket.productos.map(producto => ({
              ...producto,
              [field]: value,
              // Para KIOSKO, también actualizar nombreTienda si se edita sucursal
              ...(field === 'sucursal' && ticket.sucursal_type === 'KIOSKO' ? { nombreTienda: value } : {})
            }));
          }
          
          return updatedTicket;
        }
        return ticket;
      });
      
      console.log('Tickets actualizados:', updatedTickets);
      return updatedTickets;
    });
  };

  const addMoreTickets = async (files) => {
    const result = await processTickets(files, true);
    // Limpiar indicadores después de un tiempo
    if (result) {
      setTimeout(() => {
        setNewTicketCounts({ oxxo: 0, kiosko: 0 });
      }, 5000);
    }
    return result;
  };

  const updateQuantity = (ticketId, productIndex, newQuantity) => {
    setTickets(prevTickets => 
      prevTickets.map(ticket => {
        if (ticket.id === ticketId) {
          const updatedProducts = ticket.productos.map((producto, index) => {
            if (index === productIndex) {
              // Para OXXO usar 'cantidad', para KIOSKO usar 'numeroPiezasCompradas'
              if (ticket.sucursal_type === 'OXXO') {
                return { ...producto, cantidad: newQuantity };
              } else {
                return { ...producto, numeroPiezasCompradas: newQuantity };
              }
            }
            return producto;
          });
          return { ...ticket, productos: updatedProducts };
        }
        return ticket;
      })
    );
  };

  const addProductToTicket = (ticketId, productType, quantity) => {
    setTickets(prevTickets => 
      prevTickets.map(ticket => {
        if (ticket.id === ticketId) {
          const newProduct = ticket.sucursal_type === 'OXXO' ? {
            id: `${ticketId}-${Date.now()}`,
            descripcion: productType === '5kg' ? 'BOLSA HIELO SANTI 5K' : 'HIELO SANTI ICE 15KG',
            cantidad: quantity,
            costo: productType === '5kg' ? 17.5 : 37.5,
            sucursal: ticket.sucursal,
            fecha: ticket.fecha,
            remision: ticket.remision,
            pedido_adicional: ticket.pedido_adicional
          } : {
            id: `${ticketId}-${Date.now()}`,
            tipoProducto: productType === '5kg' ? 'Bolsas de 5kg' : 'Bolsas de 15kg',
            numeroPiezasCompradas: quantity,
            sucursal: ticket.sucursal,
            fecha: ticket.fecha,
            folio: ticket.folio
          };
          
          return {
            ...ticket,
            productos: [...ticket.productos, newProduct]
          };
        }
        return ticket;
      })
    );
  };

  const deleteTicket = (ticketId) => {
    setTickets(prevTickets => prevTickets.filter(ticket => ticket.id !== ticketId));
  };

  const addManualTicket = (manualTicket) => {
    // Convertir ticket manual al formato esperado
    const formattedTicket = {
      id: manualTicket.id,
      sucursal_type: manualTicket.cliente,
      sucursal: manualTicket.sucursal,
      fecha: manualTicket.fecha,
      status: 'processed',
      tipo: 'manual',
      ...(manualTicket.cliente === 'OXXO' ? {
        remision: manualTicket.remision || '',
        pedido_adicional: manualTicket.pedido || '',
        productos: manualTicket.productos.map(p => ({
          id: `${manualTicket.id}-${Date.now()}`,
          descripcion: p.nombre === 'Hielo en Cubos' ? 'BOLSA HIELO SANTI 5K' : 'HIELO SANTI ICE 15KG',
          cantidad: p.cantidad,
          costo: p.nombre === 'Hielo en Cubos' ? 17.5 : 37.5,
          sucursal: manualTicket.sucursal,
          fecha: manualTicket.fecha,
          remision: manualTicket.remision || '',
          pedido_adicional: manualTicket.pedido || ''
        }))
      } : {
        folio: manualTicket.folio || '',
        productos: manualTicket.productos.map(p => ({
          id: `${manualTicket.id}-${Date.now()}`,
          tipoProducto: p.nombre === 'Hielo en Cubos' ? 'Bolsas de 5kg' : 'Bolsas de 15kg',
          numeroPiezasCompradas: p.cantidad,
          sucursal: manualTicket.sucursal,
          fecha: manualTicket.fecha,
          folio: manualTicket.folio || '',
          nombreTienda: manualTicket.sucursal
        }))
      })
    };
    
    setTickets(prevTickets => [...prevTickets, formattedTicket]);
  };

  const resetProcess = () => {
    setTickets([]);
    setProcessing(null);
    setConfirming(null);
    setResults(null);
    setProcessingMore(false);
    setNewTicketCounts({ oxxo: 0, kiosko: 0 });
  };

  // Función específica para eliminar un producto de un ticket
  const deleteProductFromTicket = (ticketId, productIndex) => {
    console.log('deleteProductFromTicket llamado:', { ticketId, productIndex });
    
    setTickets(prevTickets => {
      return prevTickets.map(ticket => {
        if (ticket.id === ticketId) {
          // Verificar que hay más de un producto
          if (ticket.productos.length <= 1) {
            console.warn('No se puede eliminar el único producto del ticket');
            return ticket;
          }
          
          // Crear una copia de los productos sin el producto a eliminar
          const updatedProducts = [...ticket.productos];
          updatedProducts.splice(productIndex, 1);
          
          console.log('Productos actualizados:', updatedProducts);
          return { ...ticket, productos: updatedProducts };
        }
        return ticket;
      });
    });
  };

  return {
    tickets,
    processing,
    confirming,
    results,
    processingMore,
    newTicketCounts,
    processTickets,
    confirmTickets,
    updateTicket,
    addMoreTickets,
    addProductToTicket,
    updateQuantity,
    deleteTicket,
    deleteProduct: deleteProductFromTicket, // Alias para consistencia
    addManualTicket,
    resetProcess
  };
};