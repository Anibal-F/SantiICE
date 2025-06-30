# Reporte de Patrones Identificados
## Análisis Exhaustivo de Tickets Reales

### 📊 Resumen de Análisis

**OXXO:** 8 patrones identificados
**KIOSKO:** 9 patrones identificados

### 🔍 Patrones OXXO Identificados

#### Patrón 1: 5kg - 32 bolsas
- **Línea:** 22
- **Texto:** `17.50 31.00 32.00 0.00 992.00`
- **Descripción:** Línea con precio 17.50 contiene cantidad 32
- **Contexto:**
```
   20: 37.50 0.00 3.00 0.00 0.00
   21: 2 7500465096004 BOLSA HIELO SANTI 5K
 → 22: 17.50 31.00 32.00 0.00 992.00
   23: ToT. TASA FIS. 0.00 %
   24: 992.00
```

#### Patrón 2: 15kg - 2 bolsas
- **Línea:** 22
- **Texto:** `17.50 31.00 32.00 0.00 992.00`
- **Descripción:** Línea con precio 17.50 contiene cantidad 2
- **Contexto:**
```
   20: 37.50 0.00 3.00 0.00 0.00
   21: 2 7500465096004 BOLSA HIELO SANTI 5K
 → 22: 17.50 31.00 32.00 0.00 992.00
   23: ToT. TASA FIS. 0.00 %
   24: 992.00
```

#### Patrón 3: 5kg - 26 bolsas
- **Línea:** 27
- **Texto:** `17.50 31.00 26.00 1.00 808.00`
- **Descripción:** Línea con precio 17.50 contiene cantidad 26
- **Contexto:**
```
   25: 0.00
   26: 2 7500465096004 BOLSA HIELO SANTI 5K
 → 27: 17.50 31.00 26.00 1.00 808.00
   28: ToT. TASA FIS. 0.00 %
   29: 808.00
```

#### Patrón 4: 5kg - 74 bolsas
- **Línea:** 23
- **Texto:** `17.50 31.00 74.00 1.00 2,294.00`
- **Descripción:** Línea con precio 17.50 contiene cantidad 74
- **Contexto:**
```
   21: 0.00
   22: 2 7500465096004 BOLSA HIELO SANTI 5K
 → 23: 17.50 31.00 74.00 1.00 2,294.00
   24: TOT. TASA FIS. 0.00 %
   25: 2,294.00
```

#### Patrón 5: 15kg - 23 bolsas
- **Línea:** 20
- **Texto:** `37.50 0.00 23.00 1.00`
- **Descripción:** Línea con precio 37.50 contiene cantidad 23
- **Contexto:**
```
   18: COSTO PRECIO UDS. U.COM VALTOT
   19: 1 7500485098011 HIELO SANTI ICE 15KG
 → 20: 37.50 0.00 23.00 1.00
   21: 0.00
   22: 2 7500465096004 BOLSA HIELO SANTI 5K
```

#### Patrón 6: 5kg - 72 bolsas
- **Línea:** 25
- **Texto:** `17.50 31.00 72.00 1.00 2,232.00`
- **Descripción:** Línea con precio 17.50 contiene cantidad 72
- **Contexto:**
```
   23: 0.00
   24: 2 7500465096004 BOLSA HIELO SANTI 5K
 → 25: 17.50 31.00 72.00 1.00 2,232.00
   26: TOT. TASA FIS, 0.00%
   27: 2,232.00
```

#### Patrón 7: 5kg - 120 bolsas
- **Línea:** 20
- **Texto:** `17.50 31.00 120.00 0.00 3,720.00`
- **Descripción:** Línea con precio 17.50 contiene cantidad 120
- **Contexto:**
```
   18: COSTO PRECIO UDS. U.COM VALTOT
   19: 2 7500465096004 BOLSA HIELO SANTI 5K
 → 20: 17.50 31.00 120.00 0.00 3,720.00
   21: 1 7500465096011 HIELO SANTICE 15KG
   22: 37.50
```

#### Patrón 8: 5kg - 42 bolsas
- **Línea:** 20
- **Texto:** `17.50 31.00 42.00 1.00 1,302.00`
- **Descripción:** Línea con precio 17.50 contiene cantidad 42
- **Contexto:**
```
   18: COSTO PRECIO UDS. U.COM VALTOT
   19: 1 7500465096004 BOLSA HIELO SANTI 5K
 → 20: 17.50 31.00 42.00 1.00 1,302.00
   21: 2 750046509601 HIELO SANTHICE 15KG
   22: CADENA
```

### 🔍 Patrones KIOSKO Identificados

#### Patrón 1: 5kg - 90 bolsas
- **Línea:** 22
- **Texto:** `90.00`
- **Descripción:** Cantidad 90 en formato decimal
- **Contexto:**
```
   20: 630.00
   21: 7500465096004
 → 22: 90.00
   23: 16.00
   24: BOLSA DE HIELO SANTI ICE 5
```

#### Patrón 2: 15kg - 14 bolsas
- **Línea:** 17
- **Texto:** `14.00`
- **Descripción:** Cantidad 14 en formato decimal
- **Contexto:**
```
   15: Importe
   16: 7500465096011
 → 17: 14.00
   18: 45.00
   19: BOLSA DE HIELO SANTI ICE 15
```

#### Patrón 3: 5kg - 43 bolsas
- **Línea:** 19
- **Texto:** `7500465096004 43.00`
- **Descripción:** Cantidad 43 en formato decimal
- **Contexto:**
```
   17: BOLSA DE HIELO SANTI ICE 15
   18: 270.00
 → 19: 7500465096004 43.00
   20: 16.00
   21: BOLSA DE HIELO SANTI ICE 5
```

#### Patrón 4: 15kg - 6 bolsas
- **Línea:** 14
- **Texto:** `7500465096011`
- **Descripción:** Línea con código 15kg contiene cantidad 6
- **Contexto:**
```
   12: Descripcion
   13: Importe
 → 14: 7500465096011
   15: 6.00
   16: 45.00
```

#### Patrón 5: 5kg - 48 bolsas
- **Línea:** 19
- **Texto:** `7500465096004 48.00`
- **Descripción:** Cantidad 48 en formato decimal
- **Contexto:**
```
   17: BOLSA DE HIELO SANTI ICE 15
   18: 315.00
 → 19: 7500465096004 48.00
   20: 16.00
   21: BOLSA DE HIELO SANTI ICE 5
```

#### Patrón 6: 15kg - 7 bolsas
- **Línea:** 14
- **Texto:** `7500465096011`
- **Descripción:** Línea con código 15kg contiene cantidad 7
- **Contexto:**
```
   12: Descripcion
   13: Importe
 → 14: 7500465096011
   15: 7.00
   16: 45.00
```

#### Patrón 7: 5kg - 56 bolsas
- **Línea:** 14
- **Texto:** `BOLSA DE HIELO SANTI 56.00 ICE 15`
- **Descripción:** Cantidad 56 en formato decimal
- **Contexto:**
```
   12: Importe
   13: Descripcion
 → 14: BOLSA DE HIELO SANTI 56.00 ICE 15
   15: 7500465096011
   16: 34.00
```

#### Patrón 8: 15kg - 34 bolsas
- **Línea:** 16
- **Texto:** `34.00`
- **Descripción:** Cantidad 34 en formato decimal
- **Contexto:**
```
   14: BOLSA DE HIELO SANTI 56.00 ICE 15
   15: 7500465096011
 → 16: 34.00
   17: 45.00
   18: 1,530.00
```

#### Patrón 9: 15kg - 28 bolsas
- **Línea:** 15
- **Texto:** `28.00`
- **Descripción:** Cantidad 28 en formato decimal
- **Contexto:**
```
   13: Importe
   14: 7500465096011
 → 15: 28.00
   16: 45.00
   17: BOLSA DE HIELO SANTI ICE 15
```

