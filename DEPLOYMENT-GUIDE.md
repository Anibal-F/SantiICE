# 🚀 Guía de Despliegue - SantiICE-OCR

## ✅ Estado Actual
- ✅ Contenedores Docker configurados y funcionando
- ✅ Frontend: React + Nginx (Puerto 80)
- ✅ Backend: FastAPI + Python (Puerto 8000)
- ✅ Proxy reverso configurado
- ✅ Variables de entorno optimizadas

## 📋 Pasos para Subir a GitHub

### 1. Preparar el Repositorio
```bash
# Inicializar git (si no está inicializado)
git init

# Agregar archivos
git add .

# Commit inicial
git commit -m "feat: Sistema SantiICE-OCR con Docker configurado"

# Agregar repositorio remoto
git remote add origin https://github.com/TU_USUARIO/SantiICE-OCR.git

# Subir a GitHub
git push -u origin main
```

### 2. Verificar Archivos Importantes
Asegúrate de que estos archivos estén incluidos:
- ✅ `docker-compose.yml`
- ✅ `Dockerfile.backend`
- ✅ `Dockerfile.frontend`
- ✅ `nginx.conf`
- ✅ `requirements.txt`
- ✅ `.dockerignore`
- ✅ `build-docker.sh`
- ✅ `rebuild-docker.sh`

## 🌐 Despliegue en AWS EC2

### 1. Configuración de la Instancia EC2
```bash
# Tipo de instancia recomendado: t3.medium o superior
# Sistema operativo: Ubuntu 22.04 LTS
# Puertos abiertos: 22 (SSH), 80 (HTTP), 443 (HTTPS)
```

### 2. Instalación de Dependencias en EC2
```bash
# Conectar por SSH
ssh -i tu-clave.pem ubuntu@tu-ip-ec2

# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reiniciar sesión para aplicar cambios de grupo
exit
# Volver a conectar por SSH
```

### 3. Clonar y Configurar el Proyecto
```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/SantiICE-OCR.git
cd SantiICE-OCR

# Configurar variables de entorno
cp .env.docker .env.production
nano .env.production
# Actualizar con las credenciales de producción

# Configurar archivos de credenciales
# Subir credentials.json y service_account.json de forma segura
```

### 4. Desplegar la Aplicación
```bash
# Hacer ejecutables los scripts
chmod +x build-docker.sh rebuild-docker.sh

# Construir y ejecutar
./build-docker.sh

# Verificar estado
docker-compose ps
```

### 5. Configurar Dominio y SSL (Opcional)
```bash
# Instalar Certbot para SSL
sudo apt install certbot python3-certbot-nginx -y

# Configurar nginx para dominio
sudo nano /etc/nginx/sites-available/santiice

# Obtener certificado SSL
sudo certbot --nginx -d tu-dominio.com
```

## 🔧 Configuración de Producción

### Variables de Entorno (.env.production)
```env
AWS_DEFAULT_REGION=us-east-1
AWS_ACCESS_KEY_ID=TU_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=TU_SECRET_KEY
FLASK_ENV=production
```

### Configuración de Seguridad
- ✅ Cambiar credenciales por defecto
- ✅ Configurar firewall (UFW)
- ✅ Configurar SSL/HTTPS
- ✅ Configurar backups automáticos

## 📊 Monitoreo y Mantenimiento

### Comandos Útiles
```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Actualizar aplicación
git pull
./rebuild-docker.sh

# Ver uso de recursos
docker stats

# Limpiar sistema
docker system prune -f
```

### Backup de Datos
```bash
# Backup de uploads y logs
tar -czf backup-$(date +%Y%m%d).tar.gz uploads/ logs/

# Subir a S3 (opcional)
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://tu-bucket/backups/
```

## 🚨 Solución de Problemas

### Problemas Comunes
1. **Puerto 80 ocupado**: `sudo lsof -i :80`
2. **Memoria insuficiente**: Aumentar swap o instancia
3. **Permisos de Docker**: `sudo usermod -aG docker $USER`
4. **Credenciales AWS**: Verificar `.env.production`

### Logs de Depuración
```bash
# Backend
docker-compose logs backend --tail=50

# Frontend
docker-compose logs frontend --tail=50

# Nginx
docker-compose exec frontend cat /var/log/nginx/error.log
```

## 📞 Contacto y Soporte

Para soporte técnico o dudas sobre el despliegue, contactar al equipo de desarrollo.

---

**Última actualización**: $(date)
**Versión**: 1.0.0
**Estado**: ✅ Listo para producción