import React, { useState, useEffect } from 'react';
import { useConfig } from '../../contexts/ConfigContext';
import SessionService from '../../services/sessions';

const SessionHistoryPanel = ({ isOpen, onClose, onSessionSelect }) => {
  const { config } = useConfig();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSessions();
    }
  }, [isOpen]);

  const loadSessions = async () => {
    setLoading(true);
    try {
      const sessionData = SessionService.getSessions();
      setSessions(sessionData);
    } catch (error) {
      console.error('Error cargando sesiones:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('es-ES', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 dark:text-green-400';
      case 'processing':
        return 'text-blue-600 dark:text-blue-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const clearAllSessions = () => {
    if (window.confirm('¿Estás seguro de que quieres eliminar todo el historial?')) {
      SessionService.clearSessions();
      setSessions([]);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 z-40"
        onClick={onClose}
      />
      
      {/* Panel */}
      <div className={`fixed right-0 top-0 h-full w-96 z-50 transform transition-transform duration-300 flex flex-col ${
        config.darkMode ? 'bg-gray-800' : 'bg-white'
      } shadow-xl`}>
        
        {/* Header */}
        <div className={`p-4 border-b ${
          config.darkMode ? 'border-gray-700' : 'border-gray-200'
        }`}>
          <div className="flex items-center justify-between">
            <h2 className={`text-lg font-semibold ${
              config.darkMode ? 'text-white' : 'text-gray-900'
            }`}>
              Historial de Sesiones
            </h2>
            <button
              onClick={onClose}
              className={`p-2 rounded-lg transition-colors ${
                config.darkMode 
                  ? 'hover:bg-gray-700 text-gray-400 hover:text-white' 
                  : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
              }`}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 max-h-[calc(100vh-140px)]">
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className={`animate-pulse h-20 rounded ${
                  config.darkMode ? 'bg-gray-700' : 'bg-gray-200'
                }`} />
              ))}
            </div>
          ) : sessions.length === 0 ? (
            <div className={`text-center py-8 ${
              config.darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              <svg className="w-12 h-12 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p>No hay sesiones guardadas</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sessions.map((session) => (
                <div
                  key={session.id}
                  onClick={() => {
                    onSessionSelect(session);
                    onClose();
                  }}
                  className={`p-4 rounded-lg cursor-pointer transition-all duration-200 border ${
                    config.darkMode
                      ? 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                      : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className={`text-sm font-medium ${
                          config.darkMode ? 'text-gray-200' : 'text-gray-800'
                        }`}>
                          {session.client && session.client !== 'Sin cliente' ? session.client : 'Cliente no especificado'}
                        </span>
                        <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(session.status)} ${
                          config.darkMode ? 'bg-gray-600' : 'bg-gray-200'
                        }`}>
                          {session.status === 'completed' ? 'Completada' : 
                           session.status === 'processing' ? 'Procesando' : 'Error'}
                        </span>
                      </div>
                      
                      <div className={`text-xs mt-1 ${
                        config.darkMode ? 'text-gray-400' : 'text-gray-500'
                      }`}>
                        {formatDate(session.date)}
                      </div>
                      
                      {session.summary && (
                        <div className={`text-xs mt-2 space-y-1 ${
                          config.darkMode ? 'text-gray-400' : 'text-gray-600'
                        }`}>
                          <div>📊 {session.summary.total_records} registros</div>
                          <div>✅ {session.summary.exact_matches} conciliados</div>
                          <div>⚠️ {session.summary.major_differences} diferencias</div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        {sessions.length > 0 && (
          <div className={`p-4 border-t ${
            config.darkMode ? 'border-gray-700' : 'border-gray-200'
          }`}>
            <button
              onClick={clearAllSessions}
              className={`w-full py-2 px-4 rounded-md text-sm font-medium transition-colors ${
                config.darkMode
                  ? 'text-red-400 hover:bg-red-900/20 border border-red-800'
                  : 'text-red-600 hover:bg-red-50 border border-red-200'
              }`}
            >
              🗑️ Limpiar Historial
            </button>
          </div>
        )}
      </div>
    </>
  );
};

export default SessionHistoryPanel;