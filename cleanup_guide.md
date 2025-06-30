# Guía de Limpieza del Proyecto SantiICE-OCR
## Archivos a Mantener vs Deprecar

### 🗂️ ARCHIVOS PRINCIPALES A MANTENER

#### **Core del Sistema (MANTENER)**
```
✅ app/                              # Aplicación principal
   ├── services/
   │   ├── textprocess_OXXO.py      # ✅ Procesador OXXO optimizado
   │   ├── textprocess_KIOSKO.py    # ✅ Procesador KIOSKO optimizado
   │   ├── google_sheets.py         # ✅ Integración Google Sheets
   │   ├── textract.py              # ✅ Servicio OCR
   │   └── ticket_detector.py       # ✅ Detector de tipos
   ├── credentials/                 # ✅ Credenciales
   ├── templates/                   # ✅ Templates
   ├── main.py                      # ✅ Aplicación FastAPI
   └── __init__.py                  # ✅ Módulo Python

✅ lambda_package/                   # ✅ Package para AWS Lambda
✅ static/                          # ✅ Archivos estáticos
✅ test_images/                     # ✅ Imágenes de prueba
✅ .env                             # ✅ Variables de entorno
✅ requirements.txt                 # ✅ Dependencias
✅ credentials.json                 # ✅ Credenciales Google
✅ service_account.json             # ✅ Cuenta de servicio
```

#### **Configuración AWS (MANTENER)**
```
✅ lambda_function.py               # ✅ Función Lambda principal
✅ build-lambda-package.sh          # ✅ Script de build
✅ lambda-policy.json               # ✅ Políticas IAM
✅ trust-policy.json                # ✅ Políticas de confianza
✅ cors-config.json                 # ✅ Configuración CORS
```

#### **Documentación Final (MANTENER)**
```
✅ reporte_detallado_final.md       # ✅ Reporte final con datos reales
✅ final_comprehensive_report.md    # ✅ Reporte comprehensivo
✅ implementation_report.md         # ✅ Reporte de implementación
✅ pattern_analysis_report.md       # ✅ Análisis de patrones
```

### 🗑️ ARCHIVOS A DEPRECAR

#### **Scripts de Desarrollo/Testing (DEPRECAR)**
```
❌ analyze_kiosko_detailed.py       # Análisis temporal
❌ analyze_oxxo_formats.py          # Análisis temporal
❌ comprehensive_analysis.py        # Análisis temporal
❌ extract_kiosko_quantities_improved.py  # Prototipo
❌ final_oxxo_algorithm.py          # Prototipo
❌ improved_extraction.py           # Prototipo
❌ improved_oxxo_algorithm.py       # Prototipo
❌ generate_consolidated_report.py  # Script temporal
❌ generate_kiosko_report.py        # Script temporal
❌ detailed_final_report.py         # Script temporal
❌ final_comprehensive_test.py      # Test temporal
❌ test_improved_system.py          # Test temporal
❌ test_oxxo_corrections.py         # Test temporal
❌ test_oxxo_fixed.py               # Test temporal
❌ test_extreme_quantity.py         # Test temporal
❌ test_kiosko.py                   # Test temporal
❌ test_ocr_improvements.py         # Test temporal
❌ test_specific.py                 # Test temporal
❌ simple_test.py                   # Test temporal
❌ validate_kiosko_quantities.py    # Validación temporal
```

#### **Reportes Intermedios (DEPRECAR)**
```
❌ consolidated_report.md           # Reporte intermedio
❌ error_analysis_report.md         # Análisis intermedio
❌ final_analysis_summary.md        # Resumen intermedio
❌ final_analysis.md                # Análisis intermedio
❌ kiosko_final_report.md           # Reporte intermedio
❌ kiosko_test_report.md            # Test intermedio
❌ pattern_summary.md               # Resumen intermedio
❌ test_report.md                   # Test intermedio
```

#### **Archivos de Respuesta/Debug (DEPRECAR)**
```
❌ response.json                    # Respuesta de debug
```

### 📦 ESTRUCTURA FINAL RECOMENDADA

```
SantiICE-OCR/
├── app/                           # ✅ Core del sistema
├── lambda_package/                # ✅ Package AWS
├── static/                        # ✅ Frontend
├── test_images/                   # ✅ Imágenes de prueba
├── docs/                          # 📁 NUEVA: Documentación
│   ├── reporte_detallado_final.md
│   ├── final_comprehensive_report.md
│   ├── implementation_report.md
│   └── pattern_analysis_report.md
├── scripts/                       # 📁 NUEVA: Scripts útiles
│   └── build-lambda-package.sh
├── config/                        # 📁 NUEVA: Configuraciones
│   ├── lambda-policy.json
│   ├── trust-policy.json
│   └── cors-config.json
├── .env                          # ✅ Variables
├── requirements.txt              # ✅ Dependencias
├── lambda_function.py            # ✅ Lambda
├── credentials.json              # ✅ Credenciales
└── service_account.json          # ✅ Cuenta servicio
```

### 🔧 COMANDOS DE LIMPIEZA

#### **1. Crear Backup**
```bash
# Crear backup completo antes de limpiar
cp -r /Users/analistadesoporte/SantiICE-OCR /Users/analistadesoporte/SantiICE-OCR-BACKUP-$(date +%Y%m%d)
```

#### **2. Crear Estructura Organizada**
```bash
mkdir -p docs scripts config
```

#### **3. Mover Archivos Importantes**
```bash
# Mover documentación
mv reporte_detallado_final.md docs/
mv final_comprehensive_report.md docs/
mv implementation_report.md docs/
mv pattern_analysis_report.md docs/

# Mover scripts
mv build-lambda-package.sh scripts/

# Mover configuraciones
mv lambda-policy.json config/
mv trust-policy.json config/
mv cors-config.json config/
```

#### **4. Eliminar Archivos Temporales**
```bash
# Eliminar scripts de desarrollo
rm analyze_*.py comprehensive_analysis.py extract_*.py
rm final_oxxo_algorithm.py improved_*.py generate_*.py
rm detailed_final_report.py final_comprehensive_test.py
rm test_*.py simple_test.py validate_*.py

# Eliminar reportes intermedios
rm consolidated_report.md error_analysis_report.md
rm final_analysis*.md kiosko_*_report.md
rm pattern_summary.md test_report.md

# Eliminar archivos de debug
rm response.json
```

### ✅ RESULTADO FINAL

**Archivos mantenidos:** ~15 archivos esenciales
**Archivos eliminados:** ~35 archivos temporales
**Organización:** Estructura limpia y profesional
**Backup:** Copia completa preservada

### 📋 CHECKLIST DE LIMPIEZA

- [ ] ✅ Crear backup completo
- [ ] 📁 Crear estructura de carpetas
- [ ] 📄 Mover documentación a `docs/`
- [ ] 🔧 Mover scripts a `scripts/`
- [ ] ⚙️ Mover configuraciones a `config/`
- [ ] 🗑️ Eliminar archivos temporales
- [ ] ✅ Verificar que el sistema funciona
- [ ] 📦 Crear README.md actualizado

**Estado:** ✅ **LISTO PARA LIMPIEZA Y BACKUP**