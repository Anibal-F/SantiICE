import React, { useState, useEffect } from 'react';
import { useConfig } from '../../contexts/ConfigContext';

const SessionHistory = ({ onSessionSelect, currentSessionId }) => {
  const { config } = useConfig();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSessionHistory();
  }, []);

  const loadSessionHistory = async () => {
    setLoading(true);
    try {
      // Simular carga de historial desde localStorage o API
      const savedSessions = JSON.parse(localStorage.getItem('conciliator_sessions') || '[]');
      setSessions(savedSessions.slice(0, 10)); // Últimas 10 sesiones
    } catch (error) {
      console.error('Error cargando historial:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSession = (sessionData) => {
    try {
      const savedSessions = JSON.parse(localStorage.getItem('conciliator_sessions') || '[]');
      const newSession = {
        id: sessionData.sessionId,
        client: sessionData.client,
        date: new Date().toISOString(),
        status: sessionData.status,
        summary: sessionData.summary,
        files: {
          source: sessionData.sourceFile?.name,
          looker: sessionData.lookerFile?.name
        }
      };
      
      const updatedSessions = [newSession, ...savedSessions.slice(0, 9)];
      localStorage.setItem('conciliator_sessions', JSON.stringify(updatedSessions));
      setSessions(updatedSessions);
    } catch (error) {
      console.error('Error guardando sesión:', error);
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

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'processing':
        return '⏳';
      case 'error':
        return '❌';
      default:
        return '📄';
    }
  };

  if (loading) {
    return (
      <div className="space-y-2">
        <h3 className={`text-sm font-medium ${
          config.darkMode ? 'text-gray-300' : 'text-gray-700'
        }`}>Historial de Sesiones</h3>
        <div className="animate-pulse space-y-2">
          {[1, 2, 3].map(i => (
            <div key={i} className={`h-16 rounded ${
              config.darkMode ? 'bg-gray-700' : 'bg-gray-200'
            }`} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className={`text-sm font-medium ${
          config.darkMode ? 'text-gray-300' : 'text-gray-700'
        }`}>Historial de Sesiones</h3>
        <button
          onClick={loadSessionHistory}
          className={`text-xs px-2 py-1 rounded transition-colors ${
            config.darkMode 
              ? 'hover:bg-gray-700 text-gray-400 hover:text-gray-300' 
              : 'hover:bg-gray-100 text-gray-500 hover:text-gray-700'
          }`}
          title="Actualizar historial"
        >
          🔄
        </button>
      </div>

      <div className="space-y-2 max-h-64 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className={`text-xs p-3 rounded text-center ${
            config.darkMode 
              ? 'text-gray-400 bg-gray-700' 
              : 'text-gray-500 bg-gray-50'
          }`}>
            No hay sesiones previas
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              onClick={() => onSessionSelect && onSessionSelect(session)}
              className={`p-3 rounded cursor-pointer transition-all duration-200 border ${
                session.id === currentSessionId
                  ? config.darkMode
                    ? 'bg-blue-900/30 border-blue-700'
                    : 'bg-blue-50 border-blue-200'
                  : config.darkMode
                    ? 'bg-gray-700 border-gray-600 hover:bg-gray-600'
                    : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm">{getStatusIcon(session.status)}</span>
                    <span className={`text-xs font-medium truncate ${
                      config.darkMode ? 'text-gray-200' : 'text-gray-800'
                    }`}>
                      {session.client}
                    </span>
                  </div>
                  
                  <div className={`text-xs mt-1 ${
                    config.darkMode ? 'text-gray-400' : 'text-gray-500'
                  }`}>
                    {formatDate(session.date)}
                  </div>
                  
                  {session.summary && (
                    <div className={`text-xs mt-1 ${
                      config.darkMode ? 'text-gray-400' : 'text-gray-600'
                    }`}>
                      {session.summary.total_records} registros
                      {session.summary.reconciliation_rate && (
                        <span className="ml-1">
                          • {session.summary.reconciliation_rate.toFixed(1)}% éxito
                        </span>
                      )}
                    </div>
                  )}
                </div>
                
                <div className={`text-xs ${getStatusColor(session.status)}`}>
                  {session.status === 'completed' ? 'Completada' :
                   session.status === 'processing' ? 'Procesando' :
                   session.status === 'error' ? 'Error' : 'Pendiente'}
                </div>
              </div>
              
              {session.files && (session.files.source || session.files.looker) && (
                <div className={`text-xs mt-2 space-y-1 ${
                  config.darkMode ? 'text-gray-500' : 'text-gray-400'
                }`}>
                  {session.files.source && (
                    <div className="truncate">📄 {session.files.source}</div>
                  )}
                  {session.files.looker && (
                    <div className="truncate">📊 {session.files.looker}</div>
                  )}
                </div>
              )}
            </div>
          ))
        )}
      </div>
      
      {sessions.length > 0 && (
        <button
          onClick={() => {
            localStorage.removeItem('conciliator_sessions');
            setSessions([]);
          }}
          className={`w-full text-xs py-2 px-3 rounded transition-colors ${
            config.darkMode
              ? 'text-red-400 hover:bg-red-900/20 border border-red-800'
              : 'text-red-600 hover:bg-red-50 border border-red-200'
          }`}
        >
          🗑️ Limpiar Historial
        </button>
      )}
    </div>
  );
};

// Función para guardar sesión desde el componente principal
SessionHistory.saveSession = (sessionData) => {
  try {
    const savedSessions = JSON.parse(localStorage.getItem('conciliator_sessions') || '[]');
    const newSession = {
      id: sessionData.sessionId,
      client: sessionData.client,
      date: new Date().toISOString(),
      status: sessionData.status,
      summary: sessionData.summary,
      files: {
        source: sessionData.sourceFile?.name,
        looker: sessionData.lookerFile?.name
      }
    };
    
    const updatedSessions = [newSession, ...savedSessions.slice(0, 9)];
    localStorage.setItem('conciliator_sessions', JSON.stringify(updatedSessions));
  } catch (error) {
    console.error('Error guardando sesión:', error);
  }
};

export default SessionHistory;