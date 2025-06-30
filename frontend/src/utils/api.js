import axios from 'axios';
import { sanitizeApiResponse } from './errorUtils';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutos para procesamiento de múltiples archivos
});

export const processTickets = async (files, onProgress) => {
  const formData = new FormData();
  
  files.forEach(file => {
    formData.append('files', file);
  });

  try {
    const response = await api.post('/process-tickets', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress?.({
          completed: Math.floor((percentCompleted / 100) * files.length),
          current: files[0]?.name
        });
      }
    });

    return sanitizeApiResponse(response.data);
  } catch (error) {
    console.error('Error processing tickets:', error);
    throw error;
  }
};

export const confirmTickets = async (tickets) => {
  try {
    const response = await api.post('/confirm-tickets', {
      tickets: tickets
    });

    // Asegurar que la respuesta tenga la estructura esperada
    return sanitizeApiResponse({
      success: response.data?.success || false,
      results: response.data?.results || [],
      summary: response.data?.summary || {
        total: 0,
        success: 0,
        errors: 0,
        duplicated: 0
      }
    });
  } catch (error) {
    console.error('Error confirming tickets:', error);
    
    // Retornar estructura de error segura
    return sanitizeApiResponse({
      success: false,
      results: [],
      summary: {
        total: tickets.length,
        success: 0,
        errors: tickets.length,
        duplicated: 0
      },
      error: error.message || 'Error desconocido'
    });
  }
};

// Endpoint original para compatibilidad
export const uploadSingleTicket = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await api.post('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });

    return sanitizeApiResponse(response.data);
  } catch (error) {
    console.error('Error uploading ticket:', error);
    throw error;
  }
};