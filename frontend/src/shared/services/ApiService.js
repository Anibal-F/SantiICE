// Servicio API centralizado para todos los módulos
import axios from 'axios';
import { getBackendConfig, buildApiUrl } from '../../core/config/backendConfig';

class ApiService {
  constructor() {
    this.clients = new Map();
  }

  // Obtener cliente HTTP para un módulo específico
  getClient(moduleId) {
    if (!this.clients.has(moduleId)) {
      const config = getBackendConfig(moduleId);
      if (!config) {
        throw new Error(`Backend config not found for module: ${moduleId}`);
      }

      const client = axios.create({
        baseURL: config.baseUrl,
        timeout: config.timeout,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      // Interceptor para requests
      client.interceptors.request.use(
        (config) => {
          // Agregar token de autenticación si existe
          const token = localStorage.getItem('auth_token');
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
          return config;
        },
        (error) => Promise.reject(error)
      );

      // Interceptor para responses
      client.interceptors.response.use(
        (response) => response,
        (error) => {
          if (error.response?.status === 401) {
            // Manejar token expirado
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
          }
          return Promise.reject(error);
        }
      );

      this.clients.set(moduleId, client);
    }

    return this.clients.get(moduleId);
  }

  // Método genérico para hacer requests
  async request(moduleId, endpoint, options = {}) {
    const client = this.getClient(moduleId);
    const config = getBackendConfig(moduleId);
    
    const endpointPath = config.endpoints[endpoint];
    if (!endpointPath) {
      throw new Error(`Endpoint '${endpoint}' not found for module: ${moduleId}`);
    }

    return client.request({
      url: endpointPath,
      ...options
    });
  }

  // Métodos específicos por tipo de request
  async get(moduleId, endpoint, params = {}) {
    return this.request(moduleId, endpoint, {
      method: 'GET',
      params
    });
  }

  async post(moduleId, endpoint, data = {}, config = {}) {
    return this.request(moduleId, endpoint, {
      method: 'POST',
      data,
      ...config
    });
  }

  async put(moduleId, endpoint, data = {}) {
    return this.request(moduleId, endpoint, {
      method: 'PUT',
      data
    });
  }

  async delete(moduleId, endpoint, params = {}) {
    return this.request(moduleId, endpoint, {
      method: 'DELETE',
      params
    });
  }

  // Upload de archivos
  async uploadFile(moduleId, endpoint, file, sessionId, fileType = 'source', onProgress = null) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', fileType);

    const config = getBackendConfig(moduleId);
    const endpointPath = config.endpoints[endpoint];
    const url = `${endpointPath}/${sessionId}`;

    return this.request(moduleId, endpoint, {
      method: 'POST',
      url: url,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: onProgress
    });
  }

  // WebSocket connection
  createWebSocket(moduleId, path, sessionId) {
    const config = getBackendConfig(moduleId);
    if (!config.websocket) {
      throw new Error(`WebSocket not configured for module: ${moduleId}`);
    }

    const wsUrl = `${config.websocket}${path}/${sessionId}`;
    return new WebSocket(wsUrl);
  }
}

// Instancia singleton
const apiService = new ApiService();
export default apiService;