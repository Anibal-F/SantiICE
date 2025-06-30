// Configuración de la aplicación
// En producción (Docker), las llamadas API van a través del proxy nginx
// En desarrollo local, van directamente al backend
export const API_URL = process.env.REACT_APP_API_URL || (process.env.NODE_ENV === 'production' ? '' : 'http://localhost:8000');

export const APP_VERSION = '1.0.0';

// Configuración de autenticación
export const AUTH_CONFIG = {
  tokenKey: 'santiice_token',
  refreshInterval: 15 * 60 * 1000, // 15 minutos en milisegundos
};

// Configuración de tickets
export const TICKET_CONFIG = {
  maxFileSize: 5 * 1024 * 1024, // 5MB
  allowedTypes: ['image/jpeg', 'image/png'],
};

// Configuración del conciliador
export const CONCILIATOR_CONFIG = {
  maxFileSize: 10 * 1024 * 1024, // 10MB
  allowedTypes: [
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
    'application/vnd.ms-excel',
    'text/csv'
  ],
  pollingInterval: 3000, // 3 segundos
};