// Configuración central de módulos
export const MODULE_CONFIG = {
  tickets: {
    id: 'tickets',
    name: 'Lector de Tickets',
    description: 'Procesa y extrae información de tickets',
    icon: 'scanner',
    color: 'blue',
    enabled: true,
    features: {
      ocr: true,
      catalogs: true,
      sheets: true,
      multiUpload: true
    },
    permissions: ['upload', 'edit', 'confirm', 'delete']
  },
  
  conciliator: {
    id: 'conciliator',
    name: 'Conciliador',
    description: 'Conciliación de archivos y reportes',
    icon: 'chart',
    color: 'green',
    enabled: true,
    features: {
      fileUpload: true,
      reconciliation: true,
      reports: true,
      websocket: true
    },
    permissions: ['view', 'upload', 'process', 'download']
  },
  
  inventory: {
    id: 'inventory',
    name: 'Inventario',
    description: 'Gestión de productos y stock',
    icon: 'warehouse',
    color: 'purple',
    enabled: false, // Próximamente
    features: {
      products: true,
      stock: true,
      alerts: true,
      reports: true
    },
    permissions: ['view', 'create', 'edit', 'delete']
  },
  
  reports: {
    id: 'reports',
    name: 'Reportes',
    description: 'Análisis y estadísticas de ventas',
    icon: 'settings',
    color: 'indigo',
    enabled: false, // Próximamente
    features: {
      analytics: true,
      export: true,
      dashboard: true,
      filters: true
    },
    permissions: ['view', 'export']
  }
};

// Obtener módulos habilitados
export const getEnabledModules = () => {
  return Object.values(MODULE_CONFIG).filter(module => module.enabled);
};

// Obtener configuración de un módulo específico
export const getModuleConfig = (moduleId) => {
  return MODULE_CONFIG[moduleId] || null;
};

// Verificar si un módulo tiene una característica específica
export const hasFeature = (moduleId, feature) => {
  const module = getModuleConfig(moduleId);
  return module?.features?.[feature] || false;
};