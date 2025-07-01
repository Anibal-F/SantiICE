import React, { useState } from 'react';
import Home from './components/Home';
import UploadZone from './components/UploadZone';
import ProcessingStatus from './components/ProcessingStatus';
import ReviewTable from './components/ReviewTable';
import ResultsSummary from './components/ResultsSummary';
import Toast from './components/Toast';
import Sidebar from './components/Sidebar';
import CatalogManager from './components/CatalogManager';
import ManualTicketEntry from './components/ManualTicketEntry';
import Login from './components/Login';
import { useTicketProcessing } from './hooks/useTicketProcessing';
import { useToast } from './hooks/useToast';
import { ConfigProvider, useConfig } from './contexts/ConfigContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';

const STEPS = {
  UPLOAD: 'upload',
  PROCESSING: 'processing',
  REVIEW: 'review',
  CONFIRMING: 'confirming',
  RESULTS: 'results'
};

const MODULES = {
  HOME: 'home',
  TICKETS: 'tickets'
};

const AppContent = () => {
  const { isAuthenticated, loading, user, logout } = useAuth();
  const [currentModule, setCurrentModule] = useState(MODULES.HOME);
  const [currentStep, setCurrentStep] = useState(STEPS.UPLOAD);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [catalogManagerOpen, setCatalogManagerOpen] = useState(false);
  const { config } = useConfig();
  
  // Llamar todos los hooks antes de cualquier return condicional
  const {
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
    deleteProduct: deleteProductFromTicket,
    resetProcess
  } = useTicketProcessing();
  
  const { toast, showToast, hideToast } = useToast();
  
  // Redirección automática según el rol
  React.useEffect(() => {
    if (user && currentModule === MODULES.HOME) {
      if (user.role === 'operator') {
        setCurrentModule(MODULES.TICKETS);
      }
    }
  }, [user, currentModule]);
  
  // Mostrar loading mientras se verifica la autenticación
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  // Si no está autenticado, mostrar login
  if (!isAuthenticated) {
    return <Login />;
  }

  const handleFilesSelected = async (files) => {
    setCurrentStep(STEPS.PROCESSING);
    const result = await processTickets(files);
    if (result && result.success) {
      showToast(`¡${result.processedCount} tickets procesados exitosamente!`, 'success');
      setCurrentStep(STEPS.REVIEW);
    } else {
      showToast('Error al procesar algunos tickets', 'error');
      setCurrentStep(STEPS.UPLOAD);
    }
  };

  const handleConfirmTickets = async (validatedTickets) => {
    setCurrentStep(STEPS.CONFIRMING);
    const result = await confirmTickets(validatedTickets);
    if (result && result.success) {
      const successCount = result.summary?.success || 0;
      const errorCount = result.summary?.errors || 0;
      
      if (successCount > 0) {
        showToast(`¡${successCount} tickets enviados exitosamente!`, 'success');
      }
      if (errorCount > 0) {
        showToast(`${errorCount} tickets tuvieron errores`, 'error');
      }
    } else {
      showToast('Error al enviar tickets', 'error');
    }
    setCurrentStep(STEPS.RESULTS);
  };

  const handleAddMoreFiles = async (files) => {
    const success = await addMoreTickets(files);
    if (success) {
      // Usar el conteo directo de archivos procesados
      showToast(`¡${files.length} tickets adicionales procesados!`, 'success');
    } else {
      showToast('Error al procesar archivos adicionales', 'error');
    }
  };

  const handleStartOver = () => {
    resetProcess();
    setCurrentStep(STEPS.UPLOAD);
    // Limpiar resultados manuales
    window.manualResults = null;
  };

  const handleModuleSelect = (moduleId) => {
    setCurrentModule(moduleId);
    if (moduleId === MODULES.TICKETS) {
      setCurrentStep(STEPS.UPLOAD);
    }
  };

  const handleBackToHome = () => {
    setCurrentModule(MODULES.HOME);
    handleStartOver();
  };

  // Renderizar módulo HOME
  if (currentModule === MODULES.HOME) {
    return (
      <>
        <Home onModuleSelect={handleModuleSelect} />
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onOpenCatalogManager={() => {
            setCatalogManagerOpen(true);
            setSidebarOpen(false);
          }}
        />
        {catalogManagerOpen && (
          <CatalogManager onClose={() => setCatalogManagerOpen(false)} />
        )}
        <Toast
          message={toast.message}
          type={toast.type}
          isVisible={toast.isVisible}
          onClose={hideToast}
        />
      </>
    );
  }

  // Renderizar módulo CONCILIATOR
  if (currentModule === 'conciliator') {
    const { ConciliatorModule } = require('./modules/conciliator');
    return (
      <>
        <ConciliatorModule onBack={handleBackToHome} />
        <Sidebar
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          onOpenCatalogManager={() => {
            setCatalogManagerOpen(true);
            setSidebarOpen(false);
          }}
        />
        {catalogManagerOpen && (
          <CatalogManager onClose={() => setCatalogManagerOpen(false)} />
        )}
        <Toast
          message={toast.message}
          type={toast.type}
          isVisible={toast.isVisible}
          onClose={hideToast}
        />
      </>
    );
  }

  // Renderizar módulo TICKETS
  return (
    <div className={`min-h-screen transition-colors duration-200 ${
      config.darkMode ? 'bg-gray-900 text-white' : 'bg-gray-50'
    }`}>
      <div className="container mx-auto px-2 sm:px-4 py-4 sm:py-8">
        <header className="text-center mb-4 sm:mb-8 relative">
          {/* Solo mostrar botón home si el usuario tiene más permisos que solo tickets */}
          {user?.permissions?.length > 1 && (
            <div className="absolute top-0 left-0">
              <button
                onClick={handleBackToHome}
                className={`p-2 rounded-lg transition-colors ${
                  config.darkMode 
                    ? 'hover:bg-gray-800 text-gray-300 hover:text-white' 
                    : 'hover:bg-gray-200 text-gray-600 hover:text-gray-900'
                }`}
                title="Volver al inicio"
              >
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                </svg>
              </button>
            </div>
          )}
          
          <div className="absolute top-0 right-0">
            {/* Botón de configuración para usuarios con permisos de config */}
            {user?.permissions?.includes('config') && (
              <button
                onClick={() => setSidebarOpen(true)}
                className={`p-2 rounded-lg transition-colors mr-2 ${
                  config.darkMode 
                    ? 'hover:bg-gray-800 text-gray-300 hover:text-white' 
                    : 'hover:bg-gray-200 text-gray-600 hover:text-gray-900'
                }`}
                title="Configuración"
              >
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            )}
            

          </div>
          
          <h1 className={`text-xl sm:text-3xl font-bold mb-2 px-8 ${
            config.darkMode ? 'text-white' : 'text-gray-900'
          }`}>
            Lector de Tickets
          </h1>
          <p className={`text-sm sm:text-base px-4 ${
            config.darkMode ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Procesamiento OCR de Tickets
          </p>
        </header>

        {/* Progress Steps */}
        <div className="flex justify-center mb-4 sm:mb-8 overflow-x-auto">
          <div className="flex items-center space-x-2 sm:space-x-4 px-4">
            {Object.values(STEPS).map((step, index) => (
              <div key={step} className="flex items-center flex-shrink-0">
                <div className={`w-6 h-6 sm:w-8 sm:h-8 rounded-full flex items-center justify-center text-xs sm:text-sm font-medium ${
                  currentStep === step 
                    ? 'bg-primary-500 text-white' 
                    : Object.values(STEPS).indexOf(currentStep) > index
                    ? 'bg-success-500 text-white'
                    : 'bg-gray-300 text-gray-600'
                }`}>
                  {index + 1}
                </div>
                {index < Object.values(STEPS).length - 1 && (
                  <div className={`w-6 sm:w-12 h-0.5 mx-1 sm:mx-2 ${
                    Object.values(STEPS).indexOf(currentStep) > index
                      ? 'bg-success-500'
                      : 'bg-gray-300'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Step Content */}
        <div className="max-w-6xl mx-auto px-1 sm:px-0">
          {currentStep === STEPS.UPLOAD && (
            <div className="space-y-6">
              <UploadZone onFilesSelected={handleFilesSelected} />
              
              <ManualTicketEntry 
                onAddTicket={(ticket) => {
                  // Convertir ticket manual al formato esperado y agregarlo
                  console.log('Ticket manual recibido:', ticket);
                  showToast('Ticket manual agregado para revisión', 'success');
                  setCurrentStep(STEPS.REVIEW);
                }}
                showToast={showToast}
                onNavigateToStep={(step, data) => {
                  if (step === 4) {
                    // Ir al paso de confirmación (enviando a sheets)
                    setCurrentStep(STEPS.CONFIRMING);
                  } else if (step === 5) {
                    // Ir al paso de resultados
                    setCurrentStep(STEPS.RESULTS);
                    // Actualizar los resultados con los datos de tickets manuales
                    if (data && data.results) {
                      console.log('Actualizando results con datos manuales:', data);
                      // Simular la estructura que espera useTicketProcessing
                      const manualResults = {
                        results: data.results,
                        summary: data.summary,
                        isManualUpload: true
                      };
                      // Forzar actualización del estado de results
                      window.manualResults = manualResults;
                    }
                  }
                }}
              />
            </div>
          )}

          {currentStep === STEPS.PROCESSING && (
            <ProcessingStatus processing={processing} />
          )}

          {currentStep === STEPS.REVIEW && (
            <ReviewTable 
              tickets={tickets}
              onUpdateTicket={updateTicket}
              onConfirm={handleConfirmTickets}
              onCancel={handleStartOver}
              onAddMoreFiles={handleAddMoreFiles}
              onAddProduct={addProductToTicket}
              onUpdateQuantity={updateQuantity}
              isProcessingMore={processingMore}
              newTicketCounts={newTicketCounts}
              showToast={showToast}
              onDeleteTicket={(ticketId) => {
                deleteTicket(ticketId);
                showToast('Ticket eliminado correctamente', 'success');
              }}
              onDeleteProduct={deleteProductFromTicket}
            />
          )}

          {currentStep === STEPS.CONFIRMING && (
            <ProcessingStatus 
              processing={confirming} 
              message="Enviando tickets a Google Sheets..."
            />
          )}

          {currentStep === STEPS.RESULTS && (
            <ResultsSummary 
              results={window.manualResults || results}
              onStartOver={handleStartOver}
            />
          )}
        </div>
        
        {/* Toast Notifications */}
        <Toast
          message={toast.message}
          type={toast.type}
          isVisible={toast.isVisible}
          onClose={hideToast}
        />
        
        {/* Sidebar - Solo para usuarios con permisos de config */}
        {user?.permissions?.includes('config') && (
          <Sidebar
            isOpen={sidebarOpen}
            onToggle={() => setSidebarOpen(!sidebarOpen)}
            onOpenCatalogManager={() => {
              setCatalogManagerOpen(true);
              setSidebarOpen(false);
            }}
          />
        )}
        
        {/* Catalog Manager - Solo para usuarios con permisos de config */}
        {catalogManagerOpen && user?.permissions?.includes('config') && (
          <CatalogManager onClose={() => setCatalogManagerOpen(false)} />
        )}
        
        {/* Botón de cerrar sesión flotante para operadores */}
        {user?.role === 'operator' && (
          <button
            onClick={logout}
            className={`fixed bottom-6 right-6 px-4 py-2 text-sm rounded-full shadow-lg transition-colors z-50 ${
              config.darkMode 
                ? 'bg-red-600 hover:bg-red-700 text-white' 
                : 'bg-red-500 hover:bg-red-600 text-white'
            }`}
            title="Cerrar Sesión"
          >
            Cerrar Sesión
          </button>
        )}
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <ConfigProvider>
        <AppContent />
      </ConfigProvider>
    </AuthProvider>
  );
}

export default App;