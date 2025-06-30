// Punto de entrada del módulo de tickets
export { default as TicketsModule } from './TicketsModule';
export { useTicketProcessing } from '../../hooks/useTicketProcessing';

// Configuración específica del módulo
export const TICKETS_CONFIG = {
  name: 'Lector de Tickets',
  version: '1.0.0',
  description: 'Módulo para procesamiento OCR de tickets OXXO y KIOSKO',
  features: {
    ocr: true,
    multiUpload: true,
    catalogs: true,
    sheets: true
  }
};