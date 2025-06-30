// Sistema de permisos por roles y módulos
export const ROLES = {
  ADMIN: 'admin',
  OPERATOR: 'operator',
  VIEWER: 'viewer'
};

export const PERMISSIONS = {
  // Permisos generales
  VIEW: 'view',
  CREATE: 'create',
  EDIT: 'edit',
  DELETE: 'delete',
  
  // Permisos específicos de tickets
  UPLOAD: 'upload',
  CONFIRM: 'confirm',
  
  // Permisos de configuración
  CONFIG: 'config',
  CATALOGS: 'catalogs',
  
  // Permisos de reportes
  EXPORT: 'export',
  ANALYTICS: 'analytics'
};

// Configuración de permisos por rol
export const ROLE_PERMISSIONS = {
  [ROLES.ADMIN]: {
    global: ['config', 'catalogs'],
    tickets: ['view', 'upload', 'edit', 'confirm', 'delete'],
    inventory: ['view', 'create', 'edit', 'delete'],
    reports: ['view', 'export', 'analytics']
  },
  
  [ROLES.OPERATOR]: {
    global: [],
    tickets: ['view', 'upload', 'edit', 'confirm'],
    inventory: ['view', 'create', 'edit'],
    reports: ['view']
  },
  
  [ROLES.VIEWER]: {
    global: [],
    tickets: ['view'],
    inventory: ['view'],
    reports: ['view', 'export']
  }
};

// Verificar si un usuario tiene un permiso específico
export const hasPermission = (userRole, module, permission) => {
  const rolePerms = ROLE_PERMISSIONS[userRole];
  if (!rolePerms) return false;
  
  // Verificar permisos globales
  if (rolePerms.global?.includes(permission)) return true;
  
  // Verificar permisos del módulo específico
  return rolePerms[module]?.includes(permission) || false;
};

// Obtener todos los permisos de un usuario para un módulo
export const getModulePermissions = (userRole, module) => {
  const rolePerms = ROLE_PERMISSIONS[userRole];
  if (!rolePerms) return [];
  
  return [
    ...(rolePerms.global || []),
    ...(rolePerms[module] || [])
  ];
};

// Verificar si un usuario puede acceder a un módulo
export const canAccessModule = (userRole, module) => {
  const modulePerms = getModulePermissions(userRole, module);
  return modulePerms.length > 0;
};

// Hook para usar permisos (para uso futuro con autenticación)
export const usePermissions = (userRole = ROLES.ADMIN) => {
  return {
    hasPermission: (module, permission) => hasPermission(userRole, module, permission),
    getModulePermissions: (module) => getModulePermissions(userRole, module),
    canAccessModule: (module) => canAccessModule(userRole, module),
    role: userRole
  };
};