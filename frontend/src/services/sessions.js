const SESSIONS_KEY = 'conciliator_sessions';

export const SessionService = {
  // Obtener todas las sesiones
  getSessions() {
    try {
      const sessions = localStorage.getItem(SESSIONS_KEY);
      return sessions ? JSON.parse(sessions) : [];
    } catch (error) {
      console.error('Error cargando sesiones:', error);
      return [];
    }
  },

  // Guardar una nueva sesión
  saveSession(sessionData) {
    try {
      const sessions = this.getSessions();
      
      // Verificar si ya existe una sesión con el mismo ID
      const existingIndex = sessions.findIndex(s => s.id === sessionData.sessionId);
      
      const newSession = {
        id: sessionData.sessionId,
        client: sessionData.client || 'Cliente no especificado',
        date: new Date().toISOString(),
        status: sessionData.status,
        summary: sessionData.summary,
        records: sessionData.records || [],
        files: {
          source: sessionData.sourceFile?.name,
          looker: sessionData.lookerFile?.name
        },
        dateRange: sessionData.dateRange
      };
      
      let updatedSessions;
      if (existingIndex >= 0) {
        // Actualizar sesión existente
        updatedSessions = [...sessions];
        updatedSessions[existingIndex] = newSession;
      } else {
        // Agregar nueva sesión al inicio y mantener solo las últimas 20
        updatedSessions = [newSession, ...sessions.slice(0, 19)];
      }
      
      localStorage.setItem(SESSIONS_KEY, JSON.stringify(updatedSessions));
      return newSession;
    } catch (error) {
      console.error('Error guardando sesión:', error);
      return null;
    }
  },

  // Obtener resultados de una sesión específica
  getSessionResults(sessionId) {
    const sessions = this.getSessions();
    const session = sessions.find(s => s.id === sessionId);
    return session ? { summary: session.summary, records: session.records || [] } : null;
  },

  // Obtener sesión completa
  getSession(sessionId) {
    const sessions = this.getSessions();
    return sessions.find(s => s.id === sessionId) || null;
  },

  // Limpiar todas las sesiones
  clearSessions() {
    try {
      localStorage.removeItem(SESSIONS_KEY);
      return true;
    } catch (error) {
      console.error('Error limpiando sesiones:', error);
      return false;
    }
  }
};

export default SessionService;