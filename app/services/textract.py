import boto3
import botocore.exceptions
from fastapi import HTTPException
from .image_preprocessing import preprocess_image_for_ocr, detect_and_correct_orientation

# Intentar importar dotenv de manera segura
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # En Lambda no necesitamos dotenv, las variables de entorno ya están configuradas
    pass

# Variables globales
textract_client = None

def analyze_text_with_fallback(image_bytes):
    """
    Analiza texto con múltiples estrategias de fallback para maximizar éxito.
    
    Args:
        image_bytes: Bytes de la imagen
        
    Returns:
        dict: Resultado del OCR con la mejor estrategia encontrada
    """
    strategies = [
        (True, "con preprocesamiento completo"),
        (False, "sin preprocesamiento")
    ]
    
    best_result = None
    best_confidence = 0
    
    for preprocess, description in strategies:
        try:
            print(f"🔄 Intentando OCR {description}...")
            result = analyze_text(image_bytes, preprocess=preprocess)
            
            confidence = result.get('confidence', 0)
            print(f"📊 Confianza obtenida: {confidence:.1f}%")
            
            # Si obtenemos buena confianza, usar este resultado
            if confidence > 85:
                print(f"✅ Excelente confianza obtenida {description}")
                return result
            
            # Guardar el mejor resultado hasta ahora
            if confidence > best_confidence:
                best_result = result
                best_confidence = confidence
                
        except Exception as e:
            print(f"❌ Falló estrategia {description}: {e}")
            continue
    
    # Devolver el mejor resultado encontrado
    if best_result:
        print(f"✅ Usando mejor resultado con confianza: {best_confidence:.1f}%")
        return best_result
    else:
        # Si todo falla, intentar una vez más con configuración básica
        print("🚨 Todas las estrategias fallaron, intentando configuración básica...")
        return analyze_text(image_bytes, preprocess=False)

def get_textract_client():
    """Inicializa y devuelve el cliente de AWS Textract bajo demanda"""
    global textract_client
    
    if textract_client is None:
        try:
            # En Lambda, no necesitamos profile_name
            session = boto3.Session()
            textract_client = session.client("textract")
        except botocore.exceptions.NoCredentialsError:
            print("⚠️ No se encontraron credenciales de AWS.")
            return None
        except Exception as e:
            print(f"⚠️ Error al inicializar la sesión de AWS: {str(e)}")
            return None
    
    return textract_client

def analyze_text(image_bytes, preprocess=True):
    """ 
    Extrae texto de una imagen usando AWS Textract con preprocesamiento opcional.
    
    Args:
        image_bytes: Bytes de la imagen
        preprocess: Si aplicar preprocesamiento a la imagen
        
    Returns:
        dict: Diccionario con el texto extraído y metadatos
    """

    if not image_bytes:
        raise HTTPException(status_code=400, detail="⚠️ La imagen subida está vacía.")

    # Obtenemos el cliente bajo demanda
    client = get_textract_client()
    if client is None:
        raise HTTPException(status_code=500, detail="⚠️ No se pudo inicializar el cliente de AWS Textract.")

    try:
        # Preprocesar imagen si está habilitado
        processed_image_bytes = image_bytes
        if preprocess:
            print("🔧 Aplicando preprocesamiento a la imagen...")
            # Corregir orientación primero
            processed_image_bytes = detect_and_correct_orientation(image_bytes)
            # Luego aplicar mejoras de calidad
            processed_image_bytes = preprocess_image_for_ocr(processed_image_bytes)
        
        # Intentar OCR con imagen procesada
        response = client.detect_document_text(Document={"Bytes": processed_image_bytes})
        
        # Extraer texto con mejor estructura
        extracted_lines = []
        extracted_words = []
        confidence_scores = []
        
        for item in response.get('Blocks', []):
            if item.get('BlockType') == 'LINE':
                text = item.get('Text', '')
                confidence = item.get('Confidence', 0)
                extracted_lines.append(text)
                confidence_scores.append(confidence)
            elif item.get('BlockType') == 'WORD':
                text = item.get('Text', '')
                extracted_words.append(text)
        
        # Calcular confianza promedio
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # Crear texto final preservando estructura de líneas
        final_text = "\n".join(extracted_lines) if extracted_lines else " ".join(extracted_words)
        
        print(f"📊 OCR completado - Confianza promedio: {avg_confidence:.1f}%")
        print(f"📄 Líneas extraídas: {len(extracted_lines)}, Palabras: {len(extracted_words)}")
        
        # Si la confianza es muy baja, intentar sin preprocesamiento
        if preprocess and avg_confidence < 70:
            print("⚠️ Confianza baja, reintentando sin preprocesamiento...")
            return analyze_text(image_bytes, preprocess=False)
        
        return {
            "text": final_text,
            "confidence": avg_confidence,
            "lines_count": len(extracted_lines),
            "words_count": len(extracted_words),
            "preprocessed": preprocess
        }

    except botocore.exceptions.ClientError as e:
        error_msg = e.response["Error"]["Message"]
        # Si falla con imagen procesada, intentar con original
        if preprocess:
            print("⚠️ Error con imagen procesada, reintentando con original...")
            return analyze_text(image_bytes, preprocess=False)
        raise HTTPException(status_code=500, detail=f"❌ AWS Textract ClientError: {error_msg}")

    except boto3.exceptions.Boto3Error as e:
        if preprocess:
            print("⚠️ Error con imagen procesada, reintentando con original...")
            return analyze_text(image_bytes, preprocess=False)
        raise HTTPException(status_code=500, detail=f"❌ Error en AWS Textract: {str(e)}")

    except Exception as e:
        if preprocess:
            print("⚠️ Error con imagen procesada, reintentando con original...")
            return analyze_text(image_bytes, preprocess=False)
        raise HTTPException(status_code=500, detail=f"❌ Error inesperado en Textract: {str(e)}")