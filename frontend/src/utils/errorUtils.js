/**
 * Convierte cualquier tipo de mensaje de error a una cadena segura para React
 * @param {any} message - El mensaje que puede ser string, objeto, array, etc.
 * @returns {string} - Una cadena segura para mostrar en React
 */
export const safeErrorMessage = (message) => {
  if (typeof message === 'string') {
    return message;
  }
  
  if (message && typeof message === 'object') {
    // Si es un error de validación de Pydantic
    if (message.msg) {
      return message.msg;
    }
    
    // Si es un array de errores
    if (Array.isArray(message)) {
      return message.map(err => safeErrorMessage(err)).join(', ');
    }
    
    // Si tiene una propiedad 'message'
    if (message.message) {
      return safeErrorMessage(message.message);
    }
    
    // Si tiene una propiedad 'details'
    if (message.details) {
      return safeErrorMessage(message.details);
    }
    
    // Si tiene una propiedad 'error'
    if (message.error) {
      return safeErrorMessage(message.error);
    }
    
    // Como último recurso, convertir a JSON
    try {
      return JSON.stringify(message);
    } catch {
      return 'Error de formato desconocido';
    }
  }
  
  // Para cualquier otro tipo
  return String(message || 'Error desconocido');
};

/**
 * Procesa una respuesta de API para asegurar que todos los mensajes sean seguros
 * @param {any} response - La respuesta de la API
 * @returns {any} - La respuesta con mensajes seguros
 */
export const sanitizeApiResponse = (response) => {
  if (!response || typeof response !== 'object') {
    return response;
  }
  
  const sanitized = { ...response };
  
  // Sanitizar resultados si existen
  if (sanitized.results && Array.isArray(sanitized.results)) {
    sanitized.results = sanitized.results.map(result => ({
      ...result,
      message: safeErrorMessage(result.message),
      error: result.error ? safeErrorMessage(result.error) : result.error
    }));
  }
  
  // Sanitizar mensaje principal si existe
  if (sanitized.message) {
    sanitized.message = safeErrorMessage(sanitized.message);
  }
  
  // Sanitizar error principal si existe
  if (sanitized.error) {
    sanitized.error = safeErrorMessage(sanitized.error);
  }
  
  return sanitized;
};