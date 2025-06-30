"""
Módulo de testing para validar y mejorar la precisión del OCR.
Incluye funciones para probar diferentes configuraciones y medir resultados.
"""

import json
import time
from datetime import datetime
from .textract import analyze_text, analyze_text_with_fallback
from .ticket_detector import detect_ticket_type, validate_ticket_content
from .textprocess_OXXO import process_text_oxxo as process_oxxo
from .textprocess_KIOSKO import process_text_kiosko as process_kiosko

def test_ocr_accuracy(image_bytes, filename="test_image", expected_type=None):
    """
    Prueba la precisión del OCR con diferentes configuraciones.
    
    Args:
        image_bytes: Bytes de la imagen a probar
        filename: Nombre del archivo para logging
        expected_type: Tipo esperado del ticket ("OXXO" o "KIOSKO")
        
    Returns:
        dict: Resultados detallados de las pruebas
    """
    print(f"🧪 Iniciando pruebas de OCR para: {filename}")
    
    results = {
        "filename": filename,
        "timestamp": datetime.now().isoformat(),
        "tests": [],
        "best_result": None,
        "recommendations": []
    }
    
    # Configuraciones a probar
    test_configs = [
        {"preprocess": True, "name": "Con preprocesamiento completo"},
        {"preprocess": False, "name": "Sin preprocesamiento"},
    ]
    
    best_confidence = 0
    best_config = None
    
    for config in test_configs:
        print(f"🔬 Probando configuración: {config['name']}")
        
        try:
            start_time = time.time()
            
            # Ejecutar OCR
            ocr_result = analyze_text(image_bytes, preprocess=config["preprocess"])
            
            processing_time = time.time() - start_time
            
            # Extraer información
            ocr_text = ocr_result.get('text', '')
            confidence = ocr_result.get('confidence', 0)
            
            # Detectar tipo de ticket
            detected_type = detect_ticket_type(ocr_text)
            
            # Validar contenido
            is_valid, validation_confidence, observations = validate_ticket_content(ocr_text, detected_type)
            
            # Intentar procesar el ticket
            processing_success = False
            processing_error = None
            product_count = 0
            
            try:
                if detected_type == "KIOSKO":
                    processed_data = process_kiosko(ocr_text)
                else:
                    processed_data = process_oxxo(ocr_text)
                
                if isinstance(processed_data, list):
                    product_count = len(processed_data)
                    processing_success = True
                elif isinstance(processed_data, dict) and "error" not in processed_data:
                    product_count = 1
                    processing_success = True
                    
            except Exception as e:
                processing_error = str(e)
            
            # Calcular puntuación general
            overall_score = (
                confidence * 0.4 +  # 40% confianza OCR
                validation_confidence * 0.3 +  # 30% validación de contenido
                (100 if processing_success else 0) * 0.2 +  # 20% éxito en procesamiento
                (100 if expected_type and detected_type == expected_type else 50) * 0.1  # 10% tipo correcto
            )
            
            test_result = {
                "config": config,
                "ocr_confidence": confidence,
                "detected_type": detected_type,
                "type_correct": expected_type == detected_type if expected_type else None,
                "validation_confidence": validation_confidence,
                "validation_observations": observations,
                "processing_success": processing_success,
                "processing_error": processing_error,
                "product_count": product_count,
                "processing_time": processing_time,
                "text_length": len(ocr_text),
                "overall_score": overall_score,
                "text_sample": ocr_text[:200] + "..." if len(ocr_text) > 200 else ocr_text
            }
            
            results["tests"].append(test_result)
            
            # Actualizar mejor resultado
            if overall_score > best_confidence:
                best_confidence = overall_score
                best_config = test_result
            
            print(f"✅ Configuración completada - Puntuación: {overall_score:.1f}")
            
        except Exception as e:
            error_result = {
                "config": config,
                "error": str(e),
                "overall_score": 0
            }
            results["tests"].append(error_result)
            print(f"❌ Error en configuración: {e}")
    
    # Establecer mejor resultado
    results["best_result"] = best_config
    
    # Generar recomendaciones
    recommendations = []
    
    if best_config:
        if best_config["ocr_confidence"] < 70:
            recommendations.append("Considerar mejorar la calidad de la imagen original")
        
        if best_config["validation_confidence"] < 60:
            recommendations.append("El tipo de ticket detectado tiene baja confianza")
        
        if not best_config["processing_success"]:
            recommendations.append("Revisar los patrones de extracción de datos")
        
        if best_config["processing_time"] > 10:
            recommendations.append("El procesamiento es lento, considerar optimizaciones")
        
        if best_config["config"]["preprocess"]:
            recommendations.append("El preprocesamiento mejora los resultados")
        else:
            recommendations.append("El preprocesamiento no es necesario para esta imagen")
    
    results["recommendations"] = recommendations
    
    print(f"🏆 Mejor configuración: {best_config['config']['name'] if best_config else 'Ninguna'}")
    print(f"📊 Puntuación final: {best_confidence:.1f}")
    
    return results

def batch_test_images(image_list, output_file="ocr_test_results.json"):
    """
    Prueba múltiples imágenes y genera un reporte consolidado.
    
    Args:
        image_list: Lista de tuplas (image_bytes, filename, expected_type)
        output_file: Archivo donde guardar los resultados
        
    Returns:
        dict: Reporte consolidado
    """
    print(f"🧪 Iniciando pruebas en lote de {len(image_list)} imágenes")
    
    batch_results = {
        "timestamp": datetime.now().isoformat(),
        "total_images": len(image_list),
        "individual_results": [],
        "summary": {}
    }
    
    total_score = 0
    successful_tests = 0
    
    for i, (image_bytes, filename, expected_type) in enumerate(image_list, 1):
        print(f"\n📸 Procesando imagen {i}/{len(image_list)}: {filename}")
        
        try:
            result = test_ocr_accuracy(image_bytes, filename, expected_type)
            batch_results["individual_results"].append(result)
            
            if result["best_result"]:
                total_score += result["best_result"]["overall_score"]
                successful_tests += 1
                
        except Exception as e:
            print(f"❌ Error procesando {filename}: {e}")
            batch_results["individual_results"].append({
                "filename": filename,
                "error": str(e)
            })
    
    # Generar resumen
    if successful_tests > 0:
        avg_score = total_score / successful_tests
        batch_results["summary"] = {
            "average_score": avg_score,
            "successful_tests": successful_tests,
            "failed_tests": len(image_list) - successful_tests,
            "success_rate": (successful_tests / len(image_list)) * 100
        }
    
    # Guardar resultados
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(batch_results, f, indent=2, ensure_ascii=False)
        print(f"📄 Resultados guardados en: {output_file}")
    except Exception as e:
        print(f"⚠️ No se pudieron guardar los resultados: {e}")
    
    return batch_results

def analyze_common_errors(test_results):
    """
    Analiza errores comunes en los resultados de las pruebas.
    
    Args:
        test_results: Resultados de las pruebas
        
    Returns:
        dict: Análisis de errores comunes
    """
    error_analysis = {
        "low_ocr_confidence": [],
        "type_detection_errors": [],
        "processing_failures": [],
        "validation_issues": []
    }
    
    for result in test_results.get("individual_results", []):
        if "best_result" in result and result["best_result"]:
            best = result["best_result"]
            filename = result["filename"]
            
            # OCR con baja confianza
            if best["ocr_confidence"] < 70:
                error_analysis["low_ocr_confidence"].append({
                    "filename": filename,
                    "confidence": best["ocr_confidence"]
                })
            
            # Errores de detección de tipo
            if best.get("type_correct") is False:
                error_analysis["type_detection_errors"].append({
                    "filename": filename,
                    "detected": best["detected_type"],
                    "expected": result.get("expected_type")
                })
            
            # Fallas en procesamiento
            if not best["processing_success"]:
                error_analysis["processing_failures"].append({
                    "filename": filename,
                    "error": best.get("processing_error", "Unknown error")
                })
            
            # Problemas de validación
            if best["validation_confidence"] < 60:
                error_analysis["validation_issues"].append({
                    "filename": filename,
                    "confidence": best["validation_confidence"],
                    "observations": best["validation_observations"]
                })
    
    return error_analysis