import React, { useState } from 'react';
import { useConfig } from '../contexts/ConfigContext';
import { useToast } from '../hooks/useToast';
import Toast from './Toast';

const CatalogManager = ({ onClose }) => {
  const { config, updateConfig } = useConfig();
  const { toast, showToast, hideToast } = useToast();
  const [activeClient, setActiveClient] = useState('OXXO');
  const [newSucursal, setNewSucursal] = useState('');
  const [bulkPrice, setBulkPrice] = useState({ type: '5kg', price: '' });
  const [editingSucursal, setEditingSucursal] = useState({ name: '', newName: '' });
  const [searchFilter, setSearchFilter] = useState('');
  const [pendingChanges, setPendingChanges] = useState({});
  const [tempPrices, setTempPrices] = useState({});

  const clients = ['OXXO', 'KIOSKO'];
  const productTypes = ['5kg', '15kg'];

  const getSucursalesWithPrices = (client) => {
    const sucursales = config.sucursales[client] || [];
    const filteredSucursales = sucursales.filter(sucursal => 
      sucursal.toLowerCase().includes(searchFilter.toLowerCase())
    );
    return filteredSucursales.map(sucursal => {
      const key = `${client}-${sucursal}`;
      const originalPrices = {
        '5kg': config.precios[client]?.[sucursal]?.['5kg'] || (client === 'KIOSKO' ? 16.0 : 17.5),
        '15kg': config.precios[client]?.[sucursal]?.['15kg'] || (client === 'KIOSKO' ? 45.0 : 37.5)
      };
      return {
        name: sucursal,
        prices: tempPrices[key] || originalPrices,
        hasChanges: !!pendingChanges[key]
      };
    });
  };

  const handleAddSucursal = () => {
    if (newSucursal.trim()) {
      const existingSucursales = config.sucursales[activeClient] || [];
      const sucursalExists = existingSucursales.some(s => 
        s.toLowerCase() === newSucursal.trim().toLowerCase()
      );
      
      if (sucursalExists) {
        showToast(`La sucursal "${newSucursal}" ya está registrada en ${activeClient}`, 'error');
        return;
      }
      
      const newSucursales = {
        ...config.sucursales,
        [activeClient]: [...existingSucursales, newSucursal.trim()]
      };
      updateConfig({ sucursales: newSucursales });
      setNewSucursal('');
      showToast(`Sucursal "${newSucursal}" agregada a ${activeClient}`, 'success');
    }
  };

  const handleDeleteSucursal = (sucursal) => {
    const newSucursales = {
      ...config.sucursales,
      [activeClient]: config.sucursales[activeClient].filter(s => s !== sucursal)
    };
    updateConfig({ sucursales: newSucursales });
    showToast(`Sucursal "${sucursal}" eliminada`, 'success');
  };

  const handleEditSucursal = (oldName, newName) => {
    if (newName.trim() && newName !== oldName) {
      const existingSucursales = config.sucursales[activeClient] || [];
      const sucursalExists = existingSucursales.some(s => 
        s.toLowerCase() === newName.trim().toLowerCase() && s !== oldName
      );
      
      if (sucursalExists) {
        showToast(`La sucursal "${newName}" ya existe`, 'error');
        return;
      }
      
      const newSucursales = {
        ...config.sucursales,
        [activeClient]: config.sucursales[activeClient].map(s => s === oldName ? newName.trim() : s)
      };
      
      // También actualizar precios si existen
      const newPrecios = { ...config.precios };
      if (newPrecios[activeClient] && newPrecios[activeClient][oldName]) {
        newPrecios[activeClient][newName.trim()] = newPrecios[activeClient][oldName];
        delete newPrecios[activeClient][oldName];
      }
      
      updateConfig({ sucursales: newSucursales, precios: newPrecios });
      setEditingSucursal({ name: '', newName: '' });
      showToast(`Sucursal renombrada de "${oldName}" a "${newName}"`, 'success');
    }
  };

  const handlePriceChange = (sucursal, productType, price) => {
    const key = `${activeClient}-${sucursal}`;
    
    // Si es la primera vez que editamos esta sucursal, inicializar con precios actuales
    if (!tempPrices[key]) {
      const currentPrices = {
        '5kg': config.precios[activeClient]?.[sucursal]?.['5kg'] || (activeClient === 'KIOSKO' ? 16.0 : 17.5),
        '15kg': config.precios[activeClient]?.[sucursal]?.['15kg'] || (activeClient === 'KIOSKO' ? 45.0 : 37.5)
      };
      
      const newTempPrices = {
        ...tempPrices,
        [key]: {
          ...currentPrices,
          [productType]: parseFloat(price) || 0
        }
      };
      setTempPrices(newTempPrices);
    } else {
      // Si ya existe, solo actualizar el precio específico
      const newTempPrices = {
        ...tempPrices,
        [key]: {
          ...tempPrices[key],
          [productType]: parseFloat(price) || 0
        }
      };
      setTempPrices(newTempPrices);
    }
    
    // Marcar como pendiente
    setPendingChanges({
      ...pendingChanges,
      [key]: true
    });
  };

  const handleSaveChanges = (sucursal) => {
    const key = `${activeClient}-${sucursal}`;
    const tempPricesForSucursal = tempPrices[key];
    
    if (tempPricesForSucursal) {
      // Obtener precios actuales de la sucursal
      const currentPrices = config.precios[activeClient]?.[sucursal] || {};
      
      // Combinar precios actuales con los cambios temporales
      const mergedPrices = {
        ...currentPrices,
        ...tempPricesForSucursal
      };
      
      const newPrecios = {
        ...config.precios,
        [activeClient]: {
          ...config.precios[activeClient],
          [sucursal]: mergedPrices
        }
      };
      updateConfig({ precios: newPrecios });
      
      // Limpiar cambios pendientes
      const newPendingChanges = { ...pendingChanges };
      delete newPendingChanges[key];
      setPendingChanges(newPendingChanges);
      
      const newTempPrices = { ...tempPrices };
      delete newTempPrices[key];
      setTempPrices(newTempPrices);
      
      showToast(`Precios guardados para ${sucursal}`, 'success');
    }
  };

  const handleCancelChanges = (sucursal) => {
    const key = `${activeClient}-${sucursal}`;
    
    // Limpiar cambios pendientes
    const newPendingChanges = { ...pendingChanges };
    delete newPendingChanges[key];
    setPendingChanges(newPendingChanges);
    
    const newTempPrices = { ...tempPrices };
    delete newTempPrices[key];
    setTempPrices(newTempPrices);
  };

  const handleSortSucursales = () => {
    const sortedSucursales = [...config.sucursales[activeClient]].sort();
    const newSucursales = {
      ...config.sucursales,
      [activeClient]: sortedSucursales
    };
    updateConfig({ sucursales: newSucursales });
    showToast(`Sucursales de ${activeClient} ordenadas alfabéticamente`, 'success');
  };

  const handleBulkPriceUpdate = () => {
    if (bulkPrice.price && parseFloat(bulkPrice.price) > 0) {
      const newPrecios = { ...config.precios };
      
      config.sucursales[activeClient]?.forEach(sucursal => {
        if (!newPrecios[activeClient]) newPrecios[activeClient] = {};
        if (!newPrecios[activeClient][sucursal]) newPrecios[activeClient][sucursal] = {};
        newPrecios[activeClient][sucursal][bulkPrice.type] = parseFloat(bulkPrice.price);
      });
      
      updateConfig({ precios: newPrecios });
      setBulkPrice({ ...bulkPrice, price: '' });
      showToast(`Precio de ${bulkPrice.type} actualizado para todas las sucursales de ${activeClient}`, 'success');
    }
  };



  const sucursalesData = getSucursalesWithPrices(activeClient);

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-2 sm:p-4">
      <div className={`bg-white rounded-lg shadow-xl w-full max-w-6xl h-[95vh] sm:h-[90vh] flex flex-col ${
        config.darkMode ? 'bg-gray-800 text-white' : 'bg-white'
      }`}>
        
        {/* Header */}
        <div className={`flex items-center justify-between p-4 sm:p-6 border-b ${
          config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <h2 className="text-lg sm:text-2xl font-bold">Gestión de Catálogos</h2>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg hover:bg-gray-100 ${
              config.darkMode ? 'hover:bg-gray-700' : 'hover:bg-gray-100'
            }`}
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Client Tabs */}
        <div className={`border-b ${
          config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
        }`}>
          <div className="flex">
            {clients.map(client => (
              <button
                key={client}
                onClick={() => setActiveClient(client)}
                className={`px-6 py-3 font-medium text-sm border-b-2 ${
                  activeClient === client
                    ? config.darkMode 
                      ? 'border-blue-400 text-blue-400' 
                      : 'border-blue-500 text-blue-600'
                    : config.darkMode 
                      ? 'border-transparent text-gray-400 hover:text-gray-200' 
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {client}
                <span className={`ml-2 px-2 py-1 rounded-full text-xs ${
                  activeClient === client
                    ? config.darkMode ? 'bg-blue-900 text-blue-200' : 'bg-blue-100 text-blue-600'
                    : config.darkMode ? 'bg-gray-600 text-gray-300' : 'bg-gray-100 text-gray-600'
                }`}>
                  {config.sucursales[client]?.length || 0}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden flex flex-col lg:flex-row">
          
          {/* Left Panel - Controls */}
          <div className={`w-full lg:w-80 p-4 lg:p-6 border-b lg:border-b-0 lg:border-r overflow-y-auto ${
            config.darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'
          }`}>
            
            {/* Add Sucursal */}
            <div className="mb-4 lg:mb-6">
              <h3 className={`text-base lg:text-lg font-medium mb-2 lg:mb-3 ${
                config.darkMode ? 'text-white' : 'text-gray-900'
              }`}>Agregar Sucursal</h3>
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <input
                  type="text"
                  value={newSucursal}
                  onChange={(e) => setNewSucursal(e.target.value)}
                  placeholder="Nombre de sucursal"
                  className={`flex-1 border rounded-md px-3 py-2 text-sm ${
                    config.darkMode 
                      ? 'bg-gray-700 border-gray-600 text-white' 
                      : 'bg-white border-gray-300'
                  }`}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddSucursal()}
                />
                <button
                  onClick={handleAddSucursal}
                  className="px-4 py-2 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 w-full sm:w-auto"
                >
                  Agregar
                </button>
              </div>
            </div>

            {/* Search Filter */}
            <div className="mb-6">
              <h3 className={`text-lg font-medium mb-3 ${
                config.darkMode ? 'text-white' : 'text-gray-900'
              }`}>Buscar Sucursal</h3>
              <div className="relative">
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder="Filtrar sucursales..."
                  className={`w-full border rounded-md px-3 py-2 pl-10 text-sm ${
                    config.darkMode 
                      ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' 
                      : 'bg-white border-gray-300 placeholder-gray-500'
                  }`}
                />
                <svg className={`w-4 h-4 absolute left-3 top-3 ${config.darkMode ? 'text-gray-400' : 'text-gray-400'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                {searchFilter && (
                  <button
                    onClick={() => setSearchFilter('')}
                    className={`absolute right-3 top-3 ${config.darkMode ? 'text-gray-400 hover:text-gray-200' : 'text-gray-400 hover:text-gray-600'}`}
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>
            </div>

            {/* Sort */}
            <div className="mb-6">
              <button
                onClick={handleSortSucursales}
                className={`w-full flex items-center justify-center px-4 py-2 border rounded-md text-sm ${
                  config.darkMode 
                    ? 'border-gray-600 hover:bg-gray-700 text-white' 
                    : 'border-gray-300 hover:bg-gray-50 text-gray-700'
                }`}
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
                </svg>
                Ordenar Alfabéticamente
              </button>
            </div>

            {/* Bulk Price Update */}
            <div className="mb-6">
              <h3 className={`text-lg font-medium mb-3 ${
                config.darkMode ? 'text-white' : 'text-gray-900'
              }`}>Actualización Masiva</h3>
              <div className="space-y-3">
                <select
                  value={bulkPrice.type}
                  onChange={(e) => setBulkPrice({ ...bulkPrice, type: e.target.value })}
                  className={`w-full border rounded-md px-3 py-2 text-sm ${
                    config.darkMode 
                      ? 'bg-gray-700 border-gray-600 text-white' 
                      : 'bg-white border-gray-300'
                  }`}
                >
                  <option value="5kg">Bolsas de 5kg</option>
                  <option value="15kg">Bolsas de 15kg</option>
                </select>
                <div className="flex space-x-2">
                  <input
                    type="number"
                    step="0.1"
                    value={bulkPrice.price}
                    onChange={(e) => setBulkPrice({ ...bulkPrice, price: e.target.value })}
                    placeholder="Precio"
                    className={`flex-1 border rounded-md px-3 py-2 text-sm ${
                      config.darkMode 
                        ? 'bg-gray-700 border-gray-600 text-white' 
                        : 'bg-white border-gray-300'
                    }`}
                  />
                  <button
                    onClick={handleBulkPriceUpdate}
                    className="px-4 py-2 bg-green-500 text-white rounded-md text-sm hover:bg-green-600"
                  >
                    Aplicar
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Panel - Table */}
          <div className={`flex-1 overflow-y-auto ${
            config.darkMode ? 'bg-gray-800' : 'bg-white'
          }`}>
            <div className="p-4 lg:p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-medium ${
                  config.darkMode ? 'text-white' : 'text-gray-900'
                }`}>
                  Sucursales de {activeClient} ({sucursalesData.length}
                  {searchFilter && ` de ${config.sucursales[activeClient]?.length || 0}`})
                </h3>
                {searchFilter && (
                  <span className={`text-sm px-2 py-1 rounded ${
                    config.darkMode ? 'bg-blue-900 text-blue-200' : 'bg-blue-100 text-blue-600'
                  }`}>
                    Filtrado: "{searchFilter}"
                  </span>
                )}
              </div>

              <div className="overflow-x-auto -mx-4 lg:mx-0">
                <div className="min-w-full inline-block align-middle">
                <table className={`min-w-full divide-y ${config.darkMode ? 'divide-gray-700' : 'divide-gray-200'}`}>
                  <thead className={config.darkMode ? 'bg-gray-700' : 'bg-gray-50'}>
                    <tr>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>
                        Sucursal
                      </th>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>
                        Precio 5kg
                      </th>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>
                        Precio 15kg
                      </th>
                      <th className={`px-6 py-3 text-left text-xs font-medium uppercase tracking-wider ${
                        config.darkMode ? 'text-gray-300' : 'text-gray-500'
                      }`}>
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className={`${config.darkMode ? 'bg-gray-800 divide-gray-700' : 'bg-white divide-gray-200'}`}>
                    {sucursalesData.map((sucursal, index) => (
                      <tr key={index} className={config.darkMode ? 'bg-gray-800 hover:bg-gray-700' : 'bg-white hover:bg-gray-50'}>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {editingSucursal.name === sucursal.name ? (
                            <div className="flex items-center space-x-2">
                              <input
                                type="text"
                                value={editingSucursal.newName}
                                onChange={(e) => setEditingSucursal({ ...editingSucursal, newName: e.target.value })}
                                className={`text-sm font-medium border rounded px-2 py-1 ${config.darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300'}`}
                                autoFocus
                                onKeyPress={(e) => {
                                  if (e.key === 'Enter') handleEditSucursal(sucursal.name, editingSucursal.newName);
                                  if (e.key === 'Escape') setEditingSucursal({ name: '', newName: '' });
                                }}
                              />
                              <button
                                onClick={() => handleEditSucursal(sucursal.name, editingSucursal.newName)}
                                className="text-green-600 hover:text-green-800"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              </button>
                              <button
                                onClick={() => setEditingSucursal({ name: '', newName: '' })}
                                className="text-red-600 hover:text-red-800"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                              </button>
                            </div>
                          ) : (
                            <div className={`text-sm font-medium ${
                              config.darkMode ? 'text-white' : 'text-gray-900'
                            }`}>{sucursal.name}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="number"
                            step="0.1"
                            value={sucursal.prices['5kg']}
                            onChange={(e) => handlePriceChange(sucursal.name, '5kg', e.target.value)}
                            className={`w-20 border rounded px-2 py-1 text-sm ${
                              sucursal.hasChanges 
                                ? config.darkMode 
                                  ? 'bg-yellow-900 border-yellow-600 text-yellow-200' 
                                  : 'bg-yellow-50 border-yellow-300 text-yellow-900'
                                : config.darkMode 
                                  ? 'bg-gray-700 border-gray-600 text-white' 
                                  : 'bg-white border-gray-300'
                            }`}
                          />
                          <span className="ml-1 text-xs text-gray-500">MXN</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="number"
                            step="0.1"
                            value={sucursal.prices['15kg']}
                            onChange={(e) => handlePriceChange(sucursal.name, '15kg', e.target.value)}
                            className={`w-20 border rounded px-2 py-1 text-sm ${
                              sucursal.hasChanges 
                                ? config.darkMode 
                                  ? 'bg-yellow-900 border-yellow-600 text-yellow-200' 
                                  : 'bg-yellow-50 border-yellow-300 text-yellow-900'
                                : config.darkMode 
                                  ? 'bg-gray-700 border-gray-600 text-white' 
                                  : 'bg-white border-gray-300'
                            }`}
                          />
                          <span className="ml-1 text-xs text-gray-500">MXN</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="flex items-center space-x-2">
                            {sucursal.hasChanges ? (
                              <>
                                <button
                                  onClick={() => handleSaveChanges(sucursal.name)}
                                  className="text-green-600 hover:text-green-800 p-1 rounded"
                                  title="Guardar cambios"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handleCancelChanges(sucursal.name)}
                                  className="text-red-600 hover:text-red-800 p-1 rounded"
                                  title="Cancelar cambios"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                  </svg>
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  onClick={() => setEditingSucursal({ name: sucursal.name, newName: sucursal.name })}
                                  className="text-blue-600 hover:text-blue-800 p-1 rounded"
                                  title="Editar sucursal"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                  </svg>
                                </button>
                                <button
                                  onClick={() => handleDeleteSucursal(sucursal.name)}
                                  className="text-red-600 hover:text-red-800 p-1 rounded"
                                  title="Eliminar sucursal"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                  </svg>
                                </button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Toast Notifications */}
        <Toast
          message={toast.message}
          type={toast.type}
          isVisible={toast.isVisible}
          onClose={hideToast}
        />
      </div>
    </div>
  );
};

export default CatalogManager;