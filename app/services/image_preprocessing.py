"""
Módulo de preprocesamiento de imágenes para mejorar la calidad del OCR.
Incluye funciones para limpiar, mejorar contraste y corregir orientación.
"""

import io
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

def preprocess_image_for_ocr(image_bytes):
    """
    Preprocesa una imagen para mejorar la calidad del OCR.
    
    Args:
        image_bytes: Bytes de la imagen original
        
    Returns:
        bytes: Imagen procesada en bytes
    """
    try:
        # Cargar imagen desde bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 1. Redimensionar si es muy grande (mantener proporción)
        max_size = 2000
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = tuple(int(dim * ratio) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            print(f"📏 Imagen redimensionada a: {new_size}")
        
        # 2. Mejorar contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.3)  # Aumentar contraste 30%
        
        # 3. Mejorar nitidez
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)  # Aumentar nitidez 20%
        
        # 4. Aplicar filtro para reducir ruido
        image = image.filter(ImageFilter.MedianFilter(size=3))
        
        # 5. Convertir a escala de grises para mejor OCR
        image = image.convert('L')  # Escala de grises
        
        # 6. Aplicar umbralización para mejorar texto
        image_array = np.array(image)
        # Umbral adaptativo simple
        threshold = np.mean(image_array) - 10
        image_array = np.where(image_array > threshold, 255, 0)
        image = Image.fromarray(image_array.astype(np.uint8))
        
        # Convertir de vuelta a bytes
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='JPEG', quality=95)
        processed_bytes = output_buffer.getvalue()
        
        print(f"✅ Imagen preprocesada exitosamente")
        return processed_bytes
        
    except Exception as e:
        print(f"⚠️ Error en preprocesamiento: {e}")
        # Devolver imagen original si falla el procesamiento
        return image_bytes

def detect_and_correct_orientation(image_bytes):
    """
    Detecta y corrige la orientación de la imagen si está rotada.
    
    Args:
        image_bytes: Bytes de la imagen
        
    Returns:
        bytes: Imagen con orientación corregida
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        
        # Verificar si la imagen tiene información EXIF de orientación
        if hasattr(image, '_getexif') and image._getexif() is not None:
            exif = image._getexif()
            orientation = exif.get(274)  # Código EXIF para orientación
            
            if orientation == 3:
                image = image.rotate(180, expand=True)
            elif orientation == 6:
                image = image.rotate(270, expand=True)
            elif orientation == 8:
                image = image.rotate(90, expand=True)
        
        # Convertir de vuelta a bytes
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='JPEG', quality=95)
        return output_buffer.getvalue()
        
    except Exception as e:
        print(f"⚠️ Error corrigiendo orientación: {e}")
        return image_bytes