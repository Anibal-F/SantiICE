#!/bin/bash
# build-lambda-package.sh
# Script para construir el paquete de despliegue para AWS Lambda

# Crear directorio temporal para el paquete
echo "Creando estructura para el paquete de Lambda..."
PACKAGE_DIR="lambda_package"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Instalar dependencias en el directorio del paquete
echo "Instalando dependencias..."
pip install -r requirements.txt -t $PACKAGE_DIR

# Copiar el código de la aplicación
echo "Copiando código de la aplicación..."
cp lambda_function.py $PACKAGE_DIR/
cp -r app $PACKAGE_DIR/

# Crear el archivo ZIP
echo "Creando archivo ZIP..."
cd $PACKAGE_DIR
zip -r ../deployment_package.zip .
cd ..

echo "Paquete deployment_package.zip creado exitosamente."
echo "Recuerda que el tamaño máximo para subir directamente a Lambda es 50MB."
echo "Si el paquete supera este tamaño, deberás subirlo a través de S3."

# Imprimir tamaño del paquete
PACKAGE_SIZE=$(du -h deployment_package.zip | cut -f1)
echo "Tamaño del paquete: $PACKAGE_SIZE"