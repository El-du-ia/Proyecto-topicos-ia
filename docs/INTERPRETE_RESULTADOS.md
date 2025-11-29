# 🔍 Intérprete de Resultados Técnicos

## 📝 Descripción General

El `ResultInterpreter` es un componente que traduce la salida técnica de herramientas de ciberseguridad a explicaciones comprensibles para usuarios sin conocimientos técnicos profundos. Actúa como un "traductor" entre el lenguaje técnico de las herramientas y el lenguaje natural que un usuario común puede entender.

**Ubicación**: `src/core/interpreter.py`

---

## 🎯 Objetivo

Convertir esto:
```
21/tcp   open  ftp
22/tcp   open  ssh
80/tcp   open  http
3389/tcp open  ms-wbt-server
```

En esto:
```
🟠 ALTO - Se encontraron 4 puertos abiertos

📋 EXPLICACIÓN:
Los puertos abiertos son como 'puertas' por las que los programas se comunican:

  • Puerto 21: FTP (transferencia de archivos, protocolo antiguo e inseguro)
  • Puerto 22: SSH (acceso remoto seguro al servidor)
  • Puerto 80: HTTP (servidor web sin cifrado)
  • Puerto 3389: RDP (escritorio remoto de Windows)

💡 RECOMENDACIONES:
  ➜ Se detectaron puertos potencialmente peligrosos. Considera cerrarlos si no son necesarios.
```

---

## 🏗️ Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│                    ResultInterpreter                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: Salida técnica de herramientas                      │
│         (raw_output de nmap, scapy, whois, logs)            │
│                                                              │
│         ↓                                                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Análisis y Extracción                              │ │
│  │    • Regex patterns                                   │ │
│  │    • Parsing de datos estructurados                   │ │
│  │    • Identificación de elementos clave                │ │
│  └────────────────────────────────────────────────────────┘ │
│         ↓                                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 2. Evaluación de Severidad                            │ │
│  │    • critical, high, medium, low, info                │ │
│  │    • Basado en patrones conocidos                     │ │
│  │    • Contexto de seguridad                            │ │
│  └────────────────────────────────────────────────────────┘ │
│         ↓                                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 3. Generación de Interpretación                       │ │
│  │    • Resumen ejecutivo                                │ │
│  │    • Explicación simple                               │ │
│  │    • Hallazgos técnicos                               │ │
│  │    • Recomendaciones accionables                      │ │
│  └────────────────────────────────────────────────────────┘ │
│         ↓                                                    │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 4. Formateo para Display                              │ │
│  │    • Colores y emojis                                 │ │
│  │    • Estructura legible                               │ │
│  │    • Secciones organizadas                            │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Output: Interpretación comprensible                        │
│          {summary, findings, severity, recommendations}     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 📊 Estructura de Interpretación

Todas las funciones de interpretación devuelven un diccionario con esta estructura:

```python
{
    "summary": str,              # Resumen de 1 línea
    "findings": List[str],       # Lista de hallazgos principales
    "severity": str,             # critical/high/medium/low/info
    "recommendations": List[str],# Acciones sugeridas
    "simple_explanation": str    # Explicación en lenguaje simple
}
```

### Niveles de Severidad

| Nivel | Emoji | Descripción |
|-------|-------|-------------|
| `critical` | 🔴 | Requiere atención inmediata, riesgo alto |
| `high` | 🟠 | Problema serio, acción necesaria pronto |
| `medium` | 🟡 | Requiere revisión, riesgo moderado |
| `low` | 🟢 | Informativo, bajo riesgo |
| `info` | 🔵 | Solo informativo, sin riesgo |

---

## 🔧 Funciones de Interpretación

### 1. `interpret_nmap_output(raw_output: str)`

**Propósito**: Interpreta resultados de escaneos de puertos con Nmap.

**Análisis que realiza**:
- Extrae puertos abiertos y sus servicios
- Identifica puertos peligrosos (FTP, Telnet, RDP, SMB)
- Evalúa la superficie de ataque (cantidad de puertos)
- Genera explicaciones de cada puerto

**Lógica de Severidad**:
```python
# HIGH: Si hay puertos peligrosos
dangerous_ports = ['21', '23', '3389', '445', '135']

# MEDIUM: Si hay más de 10 puertos abiertos
if port_count > 10:
    severity = "medium"

# LOW: Pocos puertos, ninguno peligroso
else:
    severity = "low"
```

**Ejemplo de uso**:
```python
interpreter = ResultInterpreter()
nmap_output = """
21/tcp   open  ftp
22/tcp   open  ssh
80/tcp   open  http
443/tcp  open  https
"""

result = interpreter.interpret_nmap_output(nmap_output)
print(interpreter.format_interpretation(result))
```

**Output**:
```
================================================================================
🟠 ALTO - Se encontraron 4 puertos abiertos
================================================================================

📋 EXPLICACIÓN:
Los puertos abiertos son como 'puertas' por las que los programas se comunican:

  • Puerto 21: FTP (transferencia de archivos, protocolo antiguo e inseguro)
  • Puerto 22: SSH (acceso remoto seguro al servidor)
  • Puerto 80: HTTP (servidor web sin cifrado)
  • Puerto 443: HTTPS (servidor web cifrado)

💡 RECOMENDACIONES:
  ➜ Se detectaron puertos potencialmente peligrosos. Considera cerrarlos si no son necesarios.

================================================================================
```

---

### 2. `interpret_packet_capture(raw_output: str, packet_count: int)`

**Propósito**: Interpreta capturas de tráfico de red (Scapy, tcpdump).

**Análisis que realiza**:
- Cuenta paquetes por protocolo (TCP, UDP, ICMP, DNS, HTTP, HTTPS)
- Detecta tráfico no cifrado excesivo
- Identifica protocolos sospechosos (IRC, puertos raros)
- Evalúa la seguridad general del tráfico

**Lógica de Severidad**:
```python
# MEDIUM: Más HTTP que HTTPS (tráfico sin cifrar)
if protocols["HTTP"] > protocols["HTTPS"] * 2:
    severity = "medium"

# HIGH: Tráfico IRC (común en botnets)
if "IRC" in raw_output or "6667" in raw_output:
    severity = "high"
```

**Ejemplo de uso**:
```python
capture_output = """
TCP packet from 192.168.1.5
HTTPS packet from 192.168.1.10
HTTP packet from 192.168.1.15
DNS query to 8.8.8.8
"""

result = interpreter.interpret_packet_capture(capture_output, 50)
print(interpreter.format_interpretation(result))
```

**Output**:
```
================================================================================
🔵 INFORMATIVO - Se capturaron 50 paquetes de red
================================================================================

📋 EXPLICACIÓN:
Se monitoreó el tráfico de red y se capturaron 50 paquetes de datos. 
Los protocolos más activos fueron: TCP, HTTP, HTTPS, DNS. 
La mayoría del tráfico está cifrado (HTTPS), lo cual es bueno para la privacidad.

🔍 DETALLES TÉCNICOS:
  • TCP: 1 paquetes
  • HTTP: 1 paquetes
  • HTTPS: 1 paquetes
  • DNS: 1 paquetes

================================================================================
```

---

### 3. `interpret_whois(raw_output: str)`

**Propósito**: Interpreta consultas WHOIS de dominios.

**Análisis que realiza**:
- Extrae información del registrador
- Identifica fechas de creación y expiración
- Proporciona contexto sobre el uso de WHOIS

**Ejemplo de uso**:
```python
whois_output = """
Domain Name: EXAMPLE.COM
Registrar: Example Registrar Inc.
Creation Date: 1995-08-14T04:00:00Z
Expiration Date: 2025-08-13T04:00:00Z
"""

result = interpreter.interpret_whois(whois_output)
print(interpreter.format_interpretation(result))
```

**Output**:
```
================================================================================
🔵 INFORMATIVO - Información de registro de dominio
================================================================================

📋 EXPLICACIÓN:
WHOIS proporciona información pública sobre quién registró un dominio web. 
Es útil para verificar la legitimidad de un sitio o identificar al propietario 
de un dominio sospechoso.

🔍 DETALLES TÉCNICOS:
  • Registrador: Example Registrar Inc.
  • Fecha de creación: 1995-08-14T04:00:00Z
  • Fecha de expiración: 2025-08-13T04:00:00Z

================================================================================
```

---

### 4. `interpret_log_analysis(findings: List[Dict])`

**Propósito**: Interpreta análisis de logs del sistema.

**Análisis que realiza**:
- Categoriza eventos (errores, advertencias, sospechosos)
- Cuenta eventos por tipo
- Evalúa riesgo basado en cantidad y tipo de eventos

**Lógica de Severidad**:
```python
# HIGH: Muchos eventos sospechosos
if len(suspicious) > 5:
    severity = "high"

# MEDIUM: Muchos errores
elif len(errors) > 10:
    severity = "medium"
```

**Ejemplo de uso**:
```python
findings = [
    {"type": "error", "message": "Authentication failure"},
    {"type": "error", "message": "Connection timeout"},
    {"type": "suspicious", "message": "Multiple failed login attempts"},
    {"type": "suspicious", "message": "Port scan detected"},
    {"type": "warning", "message": "Disk space low"},
]

result = interpreter.interpret_log_analysis(findings)
print(interpreter.format_interpretation(result))
```

**Output**:
```
================================================================================
🔵 INFORMATIVO - Se analizaron logs y se encontraron 5 eventos relevantes
================================================================================

📋 EXPLICACIÓN:
Los logs (registros) son como el 'diario' del sistema, donde se guardan todos 
los eventos. Se revisaron los registros y se encontraron 5 eventos que requieren 
atención.

🔍 DETALLES TÉCNICOS:
  • Errores: 2
  • Advertencias: 1
  • Eventos sospechosos: 2

================================================================================
```

---

## 🎨 Formateo de Salida

### `format_interpretation(interpretation: Dict)`

Convierte el diccionario de interpretación en texto formateado para consola.

**Elementos visuales**:
- Líneas de separación (`=====`)
- Emojis para severidad (🔴🟠🟡🟢🔵)
- Secciones organizadas
- Viñetas para listas

**Secciones**:
1. **Header**: Severidad + Resumen
2. **Explicación**: Descripción en lenguaje simple
3. **Detalles técnicos**: Lista de hallazgos
4. **Recomendaciones**: Acciones sugeridas

---

## 💡 Casos de Uso

### Uso 1: Integración con Herramientas

```python
from src.core.interpreter import ResultInterpreter
from src.tools.nmap_tool import nmap_scan_tool

# Ejecutar herramienta
nmap_result = nmap_scan_tool(target="192.168.1.1")

# Interpretar resultado
interpreter = ResultInterpreter()
interpretation = interpreter.interpret_nmap_output(nmap_result)

# Mostrar al usuario
print(interpreter.format_interpretation(interpretation))
```

### Uso 2: Con el Agente CAI

```python
# El agente ejecuta una herramienta y recibe el resultado
tool_result = agent.execute_tool("nmap_scan", {"target": "example.com"})

# Interpretar antes de presentar al usuario
interpreter = ResultInterpreter()
interpretation = interpreter.interpret_nmap_output(tool_result)

# El agente puede usar la interpretación simple para su respuesta
agent_response = f"""
He escaneado {target} y encontré lo siguiente:

{interpretation['simple_explanation']}

Detalles:
{', '.join(interpretation['findings'])}

Recomendación: {interpretation['recommendations'][0] if interpretation['recommendations'] else 'Todo parece estar bien'}
"""
```

### Uso 3: Reportes Automatizados

```python
# Generar reporte de múltiples escaneos
interpreter = ResultInterpreter()
report_sections = []

# Escaneo de puertos
nmap_result = run_nmap_scan()
nmap_interp = interpreter.interpret_nmap_output(nmap_result)
report_sections.append(interpreter.format_interpretation(nmap_interp))

# Captura de tráfico
traffic_result = capture_traffic()
traffic_interp = interpreter.interpret_packet_capture(traffic_result, 100)
report_sections.append(interpreter.format_interpretation(traffic_interp))

# Combinar en reporte
full_report = "\n\n".join(report_sections)
save_report(full_report)
```

---

## 🔍 Patrones de Análisis

### Puertos Peligrosos Conocidos

```python
dangerous_ports = {
    '21': 'FTP - Transferencia sin cifrado, vulnerable a sniffing',
    '23': 'Telnet - Acceso remoto sin cifrado, muy inseguro',
    '135': 'MS-RPC - Objetivo común de exploits en Windows',
    '445': 'SMB - Vulnerable a ataques como EternalBlue',
    '3389': 'RDP - Escritorio remoto, objetivo de fuerza bruta'
}
```

### Protocolos Sospechosos

```python
suspicious_protocols = {
    'IRC': 'Común en comunicación de botnets',
    'Telnet': 'Protocolo sin cifrado obsoleto',
    'FTP': 'Transferencia de archivos sin cifrado'
}
```

### Explicaciones de Puertos Comunes

```python
port_explanations = {
    "22": "SSH (acceso remoto seguro al servidor)",
    "80": "HTTP (servidor web sin cifrado)",
    "443": "HTTPS (servidor web cifrado)",
    "3306": "MySQL (base de datos)",
    "5432": "PostgreSQL (base de datos)",
    "8080": "HTTP alternativo (servidor web de prueba)",
}
```

---


## 📖 Referencias

- **Archivo principal**: `src/core/interpreter.py`
- **Herramientas que lo usan**:
  - `src/tools/nmap_tool.py`
  - `src/tools/cai_tools_wrapper.py`
  - `src/tools/log_analyzer_tool.py`
- **Documentación relacionada**:
  - `docs/tools_spec.md` - Especificación de herramientas
  - `docs/architecture.md` - Arquitectura general

---

**Última actualización**: 2025-11-29  
**Autor**: dui-IA Team
