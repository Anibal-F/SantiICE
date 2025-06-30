// Punto de entrada del módulo conciliador
export { default as ConciliatorModule } from './ConciliatorModule';

// Configuración específica del módulo
export const CONCILIATOR_CONFIG = {
  name: 'Conciliador de Archivos',
  version: '1.0.0',
  description: 'Módulo para conciliación de archivos OXXO y KIOSKO vs Looker',
  features: {
    fileUpload: true,
    multiClient: true,
    realTimeProgress: true,
    reportGeneration: true,
    websocket: true
  }
};