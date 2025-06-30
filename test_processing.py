#!/usr/bin/env python3
"""
Script de prueba para verificar el procesamiento de tickets
"""
import os
import sys
sys.path.append('.')

from app.services.textract import analyze_text_with_fallback
from app.services.ticket_detector import detect_ticket_type
from app.services.textprocess_OXXO import process_text_oxxo
from app.services.textprocess_KIOSKO import process_text_kiosko

def test_ticket_processing(image_path):
    """Prueba el procesamiento completo de un ticket"""
    print(f"🔍 Probando: {image_path}")
    
    try:
        # Leer imagen
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # OCR
        print("📝 Ejecutando OCR...")
        ocr_result = analyze_text_with_fallback(image_bytes)
        text = ocr_result.get('text', '')
        confidence = ocr_result.get('confidence', 0)
        
        print(f"📊 Confianza OCR: {confidence:.1f}%")
        print(f"📄 Texto extraído ({len(text)} chars):")
        print("-" * 50)
        print(text[:500] + "..." if len(text) > 500 else text)
        print("-" * 50)
        
        # Detectar tipo
        ticket_type = detect_ticket_type(text)
        print(f"🏪 Tipo detectado: {ticket_type}")
        
        # Procesar
        if ticket_type == "OXXO":
            result = process_text_oxxo(text)
        elif ticket_type == "KIOSKO":
            result = process_text_kiosko(text)
        else:
            print("❌ Tipo no soportado")
            return
        
        # Mostrar resultado
        if isinstance(result, dict) and "error" in result:
            print(f"❌ Error: {result['error']}")
        else:
            if not isinstance(result, list):
                result = [result]
            
            print(f"✅ Procesado exitosamente - {len(result)} productos:")
            for i, item in enumerate(result, 1):
                print(f"  {i}. {item}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Buscar imágenes de prueba
    test_images = []
    
    # Buscar en directorios comunes
    for directory in [".", "test_images", "samples", "tickets"]:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                        test_images.append(os.path.join(root, file))
    
    if not test_images:
        print("❌ No se encontraron imágenes de prueba")
        print("💡 Coloca imágenes .jpg/.png en el directorio actual")
        sys.exit(1)
    
    print(f"🎯 Encontradas {len(test_images)} imágenes de prueba")
    
    for image_path in test_images[:3]:  # Probar máximo 3
        test_ticket_processing(image_path)
        print("\n" + "="*60 + "\n")