# 🔐 Configuración de Seguridad

## ⚠️ IMPORTANTE - Credenciales

Este proyecto requiere credenciales que **NUNCA** deben subirse a GitHub:

### Archivos requeridos (no incluidos en el repositorio):
1. `credentials.json` - Credenciales de Google Cloud
2. `service_account.json` - Cuenta de servicio (si aplica)
3. `.env` - Variables de entorno con claves

### 📋 Configuración Inicial

1. **Copia el archivo de ejemplo**:
   ```bash
   cp .env.example .env
   ```

2. **Edita `.env` con tus credenciales reales**:
   ```bash
   nano .env
   ```

3. **Agrega tus archivos de credenciales**:
   - Coloca `credentials.json` en la raíz del proyecto
   - Configura las variables AWS en `.env`

### 🚨 Verificación de Seguridad

Antes de hacer commit, verifica que estos archivos NO estén incluidos:
```bash
git status
# NO debe aparecer:
# - credentials.json
# - service_account.json  
# - .env
```

### 🔒 Buenas Prácticas

- ✅ Usa `.env.example` para documentar variables necesarias
- ✅ Mantén credenciales locales únicamente
- ✅ Usa diferentes credenciales para desarrollo/producción
- ✅ Rota credenciales regularmente
- ❌ NUNCA hagas commit de archivos con credenciales
- ❌ NUNCA compartas credenciales por chat/email

### 🌐 Despliegue en Producción

Para producción, configura las credenciales directamente en el servidor:
```bash
# En EC2/servidor
nano .env.production
# Configura con credenciales de producción
```