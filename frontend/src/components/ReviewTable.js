import React, { useState, useMemo } from 'react';
import ClientTabs from './ClientTabs';
import OxxoTable from './OxxoTable';
import KioskoTable from './KioskoTable';
import ImageModal from './ImageModal';
import AddMoreFiles from './AddMoreFiles';
import AddProductModal from './AddProductModal';
import DeleteProductModal from './DeleteProductModal';
import { useConfig } from '../contexts/ConfigContext';

const ReviewTable = ({ tickets, onUpdateTicket, onConfirm, onCancel, onAddMoreFiles, onAddProduct, onUpdateQuantity, isProcessingMore, newTicketCounts, showToast, onDeleteTicket, onDeleteProduct }) => {
  const { config } = useConfig();

  // Función para detectar si un ticket necesita atención
  const needsAttention = (ticket) => {
    // Campos base para todos los tickets
    let fieldsToCheck = [ticket.sucursal, ticket.fecha];
    
    // Agregar campos específicos según el tipo
    if (ticket.sucursal_type === 'OXXO') {
      fieldsToCheck.push(ticket.remision, ticket.pedido_adicional);
    } else if (ticket.sucursal_type === 'KIOSKO') {
      fieldsToCheck.push(ticket.folio);
    }
    
    const hasEmptyFields = fieldsToCheck.some(field => 
      field === 'No detectada' || 
      field === 'No detectado' || 
      !field || 
      field.trim() === ''
    );

    // Verificar productos con cantidad 0, sin productos o productos desconocidos
    const hasEmptyProducts = !ticket.productos || 
      ticket.productos.length === 0 || 
      ticket.productos.some(producto => {
        const cantidad = ticket.sucursal_type === 'OXXO' 
          ? (producto.cantidad || 0)
          : (producto.numeroPiezasCompradas || 0);
        
        // Verificar si es producto desconocido
        const isUnknownProduct = ticket.sucursal_type === 'KIOSKO' 
          ? (producto.tipoProducto && (producto.tipoProducto.includes('DESCONOCIDO') || producto.tipoProducto.includes('PRODUCTO DESCONOCIDO') || producto.tipoProducto.includes('Producto con importe') || producto.tipoProducto === 'Producto'))
          : (producto.descripcion && (producto.descripcion.includes('DESCONOCIDO') || producto.descripcion.includes('PRODUCTO DESCONOCIDO')));
        
        return cantidad === 0 || isUnknownProduct;
      });

    // Debug temporal
    if (ticket.sucursal_type === 'KIOSKO') {
      console.log('🔍 Debug KIOSKO:', {
        sucursal: ticket.sucursal,
        fecha: ticket.fecha,
        folio: ticket.folio,
        hasEmptyFields,
        hasEmptyProducts,
        productos: ticket.productos?.map(p => ({
          tipoProducto: p.tipoProducto,
          cantidad: p.numeroPiezasCompradas
        }))
      });
    }

    return hasEmptyFields || hasEmptyProducts;
  };
  const [selectedTickets, setSelectedTickets] = useState(
    tickets.filter(t => t.status === 'processed').map(t => t.id)
  );
  const [imageModal, setImageModal] = useState({ isOpen: false, imageSrc: '', filename: '' });
  const [activeTab, setActiveTab] = useState('OXXO');
  const [addProductModal, setAddProductModal] = useState({ isOpen: false, ticketId: null, ticketType: null });
  const [deleteProductModal, setDeleteProductModal] = useState({ isOpen: false, ticketId: null, ticketType: null });

  // Separar tickets por tipo y contar los que necesitan atención
  const { oxxoTickets, kioskoTickets, processedTickets, errorTickets, attentionCounts } = useMemo(() => {
    const processed = tickets.filter(t => t.status === 'processed');
    const errors = tickets.filter(t => t.status === 'error');
    const oxxo = processed.filter(t => t.sucursal_type === 'OXXO');
    const kiosko = processed.filter(t => t.sucursal_type === 'KIOSKO');
    
    // Contar tickets únicos que necesitan atención
    const oxxoAttention = oxxo.filter(ticket => needsAttention(ticket)).length;
    const kioskoAttention = kiosko.filter(ticket => needsAttention(ticket)).length;
    
    return {
      oxxoTickets: oxxo,
      kioskoTickets: kiosko,
      processedTickets: processed,
      errorTickets: errors,
      attentionCounts: {
        oxxo: oxxoAttention,
        kiosko: kioskoAttention
      }
    };
  }, [tickets]);

  // Tickets activos según el tab seleccionado
  const activeTickets = activeTab === 'OXXO' ? oxxoTickets : kioskoTickets;

  const openImageModal = (imageSrc, filename) => {
    setImageModal({ isOpen: true, imageSrc, filename });
  };

  const closeImageModal = () => {
    setImageModal({ isOpen: false, imageSrc: '', filename: '' });
  };

  const openAddProductModal = (ticketId, ticketType) => {
    setAddProductModal({ isOpen: true, ticketId, ticketType });
  };

  const closeAddProductModal = () => {
    setAddProductModal({ isOpen: false, ticketId: null, ticketType: null });
  };

  const openDeleteProductModal = (ticketId, ticketType) => {
    setDeleteProductModal({ isOpen: true, ticketId, ticketType });
  };

  const closeDeleteProductModal = () => {
    setDeleteProductModal({ isOpen: false, ticketId: null, ticketType: null });
  };

  const handleAddProduct = (productType, quantity) => {
    onAddProduct(addProductModal.ticketId, productType, quantity);
    showToast(`Producto agregado: ${quantity} bolsas de ${productType}`, 'success');
    closeAddProductModal();
  };

  const handleUpdateQuantity = (ticketId, productIndex, newQuantity) => {
    onUpdateQuantity(ticketId, productIndex, newQuantity);
  };

  const handleDeleteProduct = (ticketId, productIndex) => {
    const ticket = tickets.find(t => t.id === ticketId);
    if (!ticket) {
      console.error('Ticket no encontrado:', ticketId);
      showToast('Error: Ticket no encontrado', 'error');
      return;
    }
    
    if (ticket.productos.length <= 1) {
      showToast('No se puede eliminar el único producto del ticket', 'error');
      return;
    }
    
    console.log('Eliminando producto:', { ticketId, productIndex, productos: ticket.productos });
    
    // Usar la función específica para eliminar productos
    onDeleteProduct(ticketId, productIndex);
    showToast('Producto eliminado correctamente', 'success');
  };

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedTickets(activeTickets.map(t => t.id));
    } else {
      // Solo deseleccionar los tickets del tab activo
      const activeTicketIds = activeTickets.map(t => t.id);
      setSelectedTickets(prev => prev.filter(id => !activeTicketIds.includes(id)));
    }
  };

  const handleSelectAllGlobal = (checked) => {
    if (checked) {
      setSelectedTickets(processedTickets.map(t => t.id));
    } else {
      setSelectedTickets([]);
    }
  };

  const handleSelectTicket = (ticketId, checked) => {
    if (checked) {
      setSelectedTickets([...selectedTickets, ticketId]);
    } else {
      setSelectedTickets(selectedTickets.filter(id => id !== ticketId));
    }
  };

  const handleConfirm = () => {
    const ticketsToConfirm = processedTickets.filter(t => selectedTickets.includes(t.id));
    
    // Verificar si hay tickets que necesitan atención entre los seleccionados
    const ticketsWithIssues = ticketsToConfirm.filter(needsAttention);
    
    if (ticketsWithIssues.length > 0) {
      showToast(
        `No se puede confirmar. ${ticketsWithIssues.length} ticket(s) seleccionado(s) requieren atención. Complete los campos faltantes, corrija productos con cantidad 0, o deseleccione estos tickets para continuar.`,
        'error'
      );
      return;
    }
    
    onConfirm(ticketsToConfirm);
  };

  // Cambiar tab automáticamente si no hay tickets en el tab actual
  React.useEffect(() => {
    if (activeTab === 'OXXO' && oxxoTickets.length === 0 && kioskoTickets.length > 0) {
      setActiveTab('KIOSKO');
    } else if (activeTab === 'KIOSKO' && kioskoTickets.length === 0 && oxxoTickets.length > 0) {
      setActiveTab('OXXO');
    }
  }, [activeTab, oxxoTickets.length, kioskoTickets.length]);

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className={`card p-6 ${
        config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'
      }`}>
        <h2 className={`text-xl font-semibold mb-4 ${
          config.darkMode ? 'text-white' : 'text-gray-900'
        }`}>
          Revisión de Tickets
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 sm:gap-4 text-center">
          <div className={`rounded-lg p-4 ${
            config.darkMode ? 'bg-green-800' : 'bg-green-50'
          }`}>
            <div className={`text-lg sm:text-2xl font-bold ${
              config.darkMode ? 'text-green-200' : 'text-green-600'
            }`}>{processedTickets.length}</div>
            <div className={`text-xs sm:text-sm ${
              config.darkMode ? 'text-green-300' : 'text-green-600'
            }`}>Procesados</div>
          </div>
          <div className={`rounded-lg p-4 ${
            config.darkMode ? 'bg-blue-800' : 'bg-blue-50'
          }`}>
            <div className={`text-lg sm:text-2xl font-bold ${
              config.darkMode ? 'text-blue-200' : 'text-blue-600'
            }`}>{oxxoTickets.length}</div>
            <div className={`text-xs sm:text-sm ${
              config.darkMode ? 'text-blue-300' : 'text-blue-600'
            }`}>OXXO</div>
          </div>
          <div className={`rounded-lg p-4 ${
            config.darkMode ? 'bg-purple-800' : 'bg-purple-50'
          }`}>
            <div className={`text-lg sm:text-2xl font-bold ${
              config.darkMode ? 'text-purple-200' : 'text-purple-600'
            }`}>{kioskoTickets.length}</div>
            <div className={`text-xs sm:text-sm ${
              config.darkMode ? 'text-purple-300' : 'text-purple-600'
            }`}>KIOSKO</div>
          </div>
          <div className={`rounded-lg p-4 ${
            config.darkMode ? 'bg-indigo-800' : 'bg-indigo-50'
          }`}>
            <div className={`text-lg sm:text-2xl font-bold ${
              config.darkMode ? 'text-indigo-200' : 'text-indigo-600'
            }`}>{selectedTickets.length}</div>
            <div className={`text-xs sm:text-sm ${
              config.darkMode ? 'text-indigo-300' : 'text-indigo-600'
            }`}>Seleccionados</div>
          </div>
        </div>
      </div>

      {/* Error Tickets */}
      {errorTickets.length > 0 && (
        <div className={`card p-6 ${
          config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'
        }`}>
          <h3 className={`text-lg font-medium mb-4 ${
            config.darkMode ? 'text-red-400' : 'text-red-600'
          }`}>
            Tickets con errores
          </h3>
          <div className="space-y-2">
            {errorTickets.map(ticket => (
              <div key={ticket.id} className={`flex items-center justify-between p-3 rounded-lg ${
                config.darkMode ? 'bg-red-900' : 'bg-red-50'
              }`}>
                <span className={`font-medium ${
                  config.darkMode ? 'text-red-100' : 'text-red-900'
                }`}>{ticket.filename}</span>
                <span className={`text-sm ${
                  config.darkMode ? 'text-red-300' : 'text-red-600'
                }`}>{ticket.error}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Review Tables with Tabs */}
      {processedTickets.length > 0 && (
        <div className={`card overflow-visible ${
          config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'
        }`} style={{minHeight: '600px'}}>
          <div className={`p-6 border-b ${
            config.darkMode ? 'border-gray-700' : 'border-gray-200'
          }`}>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-4 space-y-2 sm:space-y-0">
              <h3 className={`text-base sm:text-lg font-medium ${
                config.darkMode ? 'text-white' : 'text-gray-900'
              }`}>
                Datos extraídos para revisión
              </h3>
              <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={activeTickets.length > 0 && activeTickets.every(t => selectedTickets.includes(t.id))}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  />
                  <span className={`text-xs sm:text-sm ${
                    config.darkMode ? 'text-gray-400' : 'text-gray-600'
                  }`}>Seleccionar todos ({activeTab})</span>
                </label>
                
                {/* Etiqueta de atención */}
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded ${
                    config.darkMode ? 'bg-red-600' : 'bg-red-500'
                  }`}></div>
                  <span className={`text-xs ${
                    config.darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    Por atender ({activeTab === 'OXXO' ? attentionCounts.oxxo : attentionCounts.kiosko})
                  </span>
                </div>
              </div>
            </div>
            
            <ClientTabs
              activeTab={activeTab}
              onTabChange={setActiveTab}
              oxxoCount={oxxoTickets.length}
              kioskoCount={kioskoTickets.length}
              newOxxoCount={newTicketCounts.oxxo}
              newKioskoCount={newTicketCounts.kiosko}
            />
          </div>

          {activeTab === 'OXXO' && oxxoTickets.length > 0 && (
            <OxxoTable
              tickets={oxxoTickets}
              onUpdateTicket={onUpdateTicket}
              selectedTickets={selectedTickets}
              onSelectTicket={handleSelectTicket}
              openImageModal={openImageModal}
              onAddProduct={(ticketId) => openAddProductModal(ticketId, 'OXXO')}
              onUpdateQuantity={handleUpdateQuantity}
              onDeleteTicket={onDeleteTicket}
              onDeleteProduct={(ticketId) => openDeleteProductModal(ticketId, 'OXXO')}
            />
          )}

          {activeTab === 'KIOSKO' && kioskoTickets.length > 0 && (
            <KioskoTable
              tickets={kioskoTickets}
              onUpdateTicket={onUpdateTicket}
              selectedTickets={selectedTickets}
              onSelectTicket={handleSelectTicket}
              imageModal={imageModal}
              openImageModal={openImageModal}
              onAddProduct={(ticketId) => openAddProductModal(ticketId, 'KIOSKO')}
              onUpdateQuantity={handleUpdateQuantity}
              onDeleteTicket={onDeleteTicket}
              onDeleteProduct={(ticketId) => openDeleteProductModal(ticketId, 'KIOSKO')}
            />
          )}

          {activeTickets.length === 0 && (
            <div className={`p-8 text-center ${
              config.darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              No hay tickets de {activeTab} para mostrar
            </div>
          )}
        </div>
      )}

      {/* Add More Files */}
      <AddMoreFiles 
        onFilesAdded={onAddMoreFiles}
        isProcessing={isProcessingMore}
      />

      {/* Global Actions */}
      <div className={`card p-4 ${
        config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'
      }`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={processedTickets.length > 0 && processedTickets.every(t => selectedTickets.includes(t.id))}
                onChange={(e) => handleSelectAllGlobal(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span className={`text-sm font-medium ${
                config.darkMode ? 'text-gray-200' : 'text-gray-700'
              }`}>Seleccionar todos los tickets</span>
            </label>
            <span className={`text-sm ${
              config.darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              ({selectedTickets.length} de {processedTickets.length} seleccionados)
            </span>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={onCancel}
              className="btn-secondary"
            >
              Cancelar
            </button>
            <button
              onClick={handleConfirm}
              disabled={selectedTickets.length === 0}
              className={`btn-primary disabled:opacity-50 disabled:cursor-not-allowed ${
                processedTickets.filter(t => selectedTickets.includes(t.id)).some(needsAttention)
                  ? 'bg-red-500 hover:bg-red-600'
                  : ''
              }`}
            >
              Confirmar {selectedTickets.length} tickets
            </button>
          </div>
        </div>
      </div>

      {/* Modals */}
      <ImageModal
        isOpen={imageModal.isOpen}
        onClose={closeImageModal}
        imageSrc={imageModal.imageSrc}
        filename={imageModal.filename}
      />
      
      <AddProductModal
        isOpen={addProductModal.isOpen}
        onClose={closeAddProductModal}
        onAdd={handleAddProduct}
        ticketType={addProductModal.ticketType}
      />
      
      {/* Modal para eliminar productos */}
      {deleteProductModal.isOpen && (
        <DeleteProductModal
          isOpen={deleteProductModal.isOpen}
          onClose={closeDeleteProductModal}
          onDelete={(productIndex) => {
            const ticketId = deleteProductModal.ticketId;
            handleDeleteProduct(ticketId, productIndex);
          }}
          products={tickets.find(t => t.id === deleteProductModal.ticketId)?.productos || []}
          ticketType={deleteProductModal.ticketType}
        />
      )}
    </div>
  );
};

export default ReviewTable;