// Configuración de backends por módulo
export const BACKEND_CONFIG = {
  tickets: {
    baseUrl: process.env.REACT_APP_TICKETS_API_URL || 'http://localhost:8000',
    endpoints: {
      upload: '/upload-tickets',
      process: '/process-tickets',
      confirm: '/confirm-tickets',
      catalogs: '/catalogs'
    },
    timeout: 30000
  },
  
  conciliator: {
    baseUrl: process.env.REACT_APP_CONCILIATOR_API_URL || 'http://localhost:8000',
    endpoints: {
      clients: '/api/conciliator/clients',
      session: '/api/conciliator/session',
      upload: '/api/conciliator/upload',
      process: '/api/conciliator/process',
      results: '/api/conciliator/results',
      download: '/api/conciliator/download'
    },
    websocket: process.env.REACT_APP_CONCILIATOR_WS_URL || 'ws://localhost:8000/api/conciliator/ws',
    timeout: 60000
  },
  
  inventory: {
    baseUrl: process.env.REACT_APP_INVENTORY_API_URL || 'http://localhost:8002',
    endpoints: {
      products: '/api/products',
      stock: '/api/stock',
      movements: '/api/movements'
    },
    timeout: 15000
  },
  
  reports: {
    baseUrl: process.env.REACT_APP_REPORTS_API_URL || 'http://localhost:8003',
    endpoints: {
      generate: '/api/generate',
      list: '/api/reports',
      download: '/api/download'
    },
    timeout: 45000
  }
};

// Obtener configuración de backend para un módulo
export const getBackendConfig = (moduleId) => {
  return BACKEND_CONFIG[moduleId] || null;
};

// Construir URL completa para un endpoint
export const buildApiUrl = (moduleId, endpoint, params = {}) => {
  const config = getBackendConfig(moduleId);
  if (!config) throw new Error(`Backend config not found for module: ${moduleId}`);
  
  const baseUrl = config.baseUrl;
  const endpointPath = config.endpoints[endpoint];
  if (!endpointPath) throw new Error(`Endpoint '${endpoint}' not found for module: ${moduleId}`);
  
  let url = `${baseUrl}${endpointPath}`;
  
  // Reemplazar parámetros en la URL
  Object.keys(params).forEach(key => {
    url = url.replace(`{${key}}`, params[key]);
  });
  
  return url;
};

// Configuración de proxy para desarrollo
export const PROXY_CONFIG = {
  '/api/tickets/*': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    pathRewrite: { '^/api/tickets': '' }
  },
  '/api/conciliator/*': {
    target: 'http://localhost:8001',
    changeOrigin: true,
    pathRewrite: { '^/api/conciliator': '/api' }
  },
  '/api/inventory/*': {
    target: 'http://localhost:8002',
    changeOrigin: true,
    pathRewrite: { '^/api/inventory': '/api' }
  },
  '/api/reports/*': {
    target: 'http://localhost:8003',
    changeOrigin: true,
    pathRewrite: { '^/api/reports': '/api' }
  }
};